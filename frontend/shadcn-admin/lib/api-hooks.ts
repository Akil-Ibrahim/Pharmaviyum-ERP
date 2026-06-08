/**
 * React hooks for API communication
 * Provides reusable hooks for fetching and mutating backend data
 */

import { useCallback, useState, useEffect } from 'react';
import { api, ApiError } from './api-client';

interface UseQueryOptions {
  enabled?: boolean;
  refetchInterval?: number;
  onSuccess?: (data: unknown) => void;
  onError?: (error: Error) => void;
}

interface UseQueryResult<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function useQuery<T>(
  endpoint: string,
  options: UseQueryOptions = {}
): UseQueryResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.get<T>(endpoint);
      setData(result);
      options.onSuccess?.(result);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);
      options.onError?.(error);
    } finally {
      setLoading(false);
    }
  }, [endpoint, options]);

  useEffect(() => {
    if (options.enabled === false) return;
    
    fetchData();

    if (options.refetchInterval) {
      const interval = setInterval(fetchData, options.refetchInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, options.enabled, options.refetchInterval]);

  return { data, loading, error, refetch: fetchData };
}

interface UseMutationOptions<T> {
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseMutationResult<T, V> {
  mutate: (data?: V) => Promise<T | null>;
  loading: boolean;
  error: Error | null;
  data: T | null;
}

export function useMutation<T, V = unknown>(
  endpoint: string,
  method: 'post' | 'put' | 'patch' | 'delete' = 'post',
  options: UseMutationOptions<T> = {}
): UseMutationResult<T, V> {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [data, setData] = useState<T | null>(null);

  const mutate = useCallback(
    async (payload?: V) => {
      try {
        setLoading(true);
        setError(null);
        const result = await (api[method] as any)<T>(endpoint, payload);
        setData(result);
        options.onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error('Unknown error');
        setError(error);
        options.onError?.(error);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [endpoint, method, options]
  );

  return { mutate, loading, error, data };
}

// Health check hook
export function useBackendHealth(): { isHealthy: boolean; checking: boolean } {
  const [isHealthy, setIsHealthy] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch('/health');
        setIsHealthy(response.ok);
      } catch {
        setIsHealthy(false);
      } finally {
        setChecking(false);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return { isHealthy, checking };
}

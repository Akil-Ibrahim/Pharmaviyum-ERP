/**
 * React hook for fetching & mutating orders. * Replace with SWR/React-Query in production for caching & deduping.
 * Mirrors FastAPI /api/v1/orders/ endpoints.
 */

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import { Order } from "@/lib/types";

export function useOrders(page = 1, size = 20) {
  const [data, setData] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // FastAPI returns paginated JSON. Adjust path to your exact endpoint.
      const res = await api.get<{ items: Order[] }>(`/orders/?page=${page}&size=${size}`);
      setData(res.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch orders");
    } finally {
      setLoading(false);
    }
  }, [page, size]);

  useEffect(() => { fetchOrders(); }, [fetchOrders]);

  const createOrder = async (payload: Record<string, unknown>) => api.post<Order>("/orders/", payload);
  const updateOrder = async (id: string, payload: Record<string, unknown>) => api.put<Order>(`/orders/${id}`, payload);
  const deleteOrder = async (id: string) => api.delete(`/orders/${id}`);

  return { data, loading, error, refetch: fetchOrders, createOrder, updateOrder, deleteOrder };
}

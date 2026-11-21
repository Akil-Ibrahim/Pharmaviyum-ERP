/**
 * TanStack Query hooks for Patient module.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
});

interface PatientCreate {
  firstName: string;
  lastName: string;
  phone: string;
}

export function usePatients() {
  const queryClient = useQueryClient();
  
  const patientsQuery = useQuery({
    queryKey: ['patients'],
    queryFn: async () => {
      const response = await apiClient.get('/patients/');
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
  });
  
  const createPatientMutation = useMutation({
    mutationFn: async (data: PatientCreate) => {
      const response = await apiClient.post('/patients/', data);
      return response.data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['patients'] }),
  });
  
  return {
    patients: patientsQuery.data?.items || [],
    isLoading: patientsQuery.isLoading,
    error: patientsQuery.error,
    createPatient: createPatientMutation.mutate,
    isCreating: createPatientMutation.isPending,
  };
}

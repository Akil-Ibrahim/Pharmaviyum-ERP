/**
 * Patient Detail Route with Data Loading.
 * 
 * Uses TanStack Router for type-safe routing with:
 * - Automatic data loading
 * - Search params validation
 * - Type-safe navigation
 */
import { createFileRoute } from '@tanstack/react-router';
import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
});

export const Route = createFileRoute('/patients/$patientId')({
  // Load data before rendering
  loader: async ({ params }) => {
    const response = await apiClient.get(`/patients/${params.patientId}`);
    return { patient: response.data.data };
  },
  
  // Validate search params
  validateSearch: (search) => ({
    tab: (search.tab as string) || 'overview',
  }),
  
  component: PatientDetailPage,
});

function PatientDetailPage() {
  const { patient } = Route.useLoaderData();
  const { tab } = Route.useSearch();
  
  return (
    <div className="container mx-auto py-8">
      <h1 className="text-2xl font-bold">{patient.fullName}</h1>
      <p>Phone: {patient.phone}</p>
      <p>Loyalty: {patient.loyaltyTier}</p>
      <p>Active tab: {tab}</p>
    </div>
  );
}

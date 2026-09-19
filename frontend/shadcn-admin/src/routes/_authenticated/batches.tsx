import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/batches')({
  component: () => <EntityPage title='Batches' description='Medication batches, expiry dates, quantities, and product traceability.' />,
})

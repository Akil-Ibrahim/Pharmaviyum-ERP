import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/batches')({
  component: () => (
    <EntityPage title='Batches' description='Medication batches, expiry dates, quantities, and product traceability.' endpoint='/api/v1/batches' columns={['id', 'product_id', 'batch_number', 'expiry_date', 'received_quantity', 'available_quantity', 'barcode']} />
  ),
})

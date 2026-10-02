import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/patient-purchases')({
  component: () => (
    <EntityPage
      title='Patient Purchases'
      description='Canonical patient purchase ledger, receipts, quantities, and purchase values.'
      endpoint='/api/v1/patient-purchases/'
      columns={[
        'id',
        'patient_id',
        'product_name',
        'receipt_number',
        'category',
        'quantity',
        'unit_price',
        'total_amount',
        'prescription_required',
        'purchased_at',
      ]}
    />
  ),
})

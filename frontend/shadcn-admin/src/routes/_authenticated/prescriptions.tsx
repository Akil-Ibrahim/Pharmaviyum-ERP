import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/prescriptions')({
  component: () => (
    <EntityPage
      title='Prescriptions'
      description='Prescription records, validity, medication, and dispensing status.'
      endpoint='/api/v1/prescriptions'
      columns={['id', 'patient_id', 'product_id', 'prescription_number', 'status', 'issued_at', 'expires_at']}
    />
  ),
})

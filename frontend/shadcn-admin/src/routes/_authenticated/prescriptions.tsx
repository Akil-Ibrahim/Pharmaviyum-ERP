import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/prescriptions')({
  component: () => (
    <EntityPage
      title='Prescriptions'
      description='Prescription records, validity, medication, and dispensing status.'
    />
  ),
})

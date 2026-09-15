import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/patients')({
  component: () => (
    <EntityPage
      title='Patients'
      description='Patient profiles, history, and pharmacy interactions.'
    />
  ),
})

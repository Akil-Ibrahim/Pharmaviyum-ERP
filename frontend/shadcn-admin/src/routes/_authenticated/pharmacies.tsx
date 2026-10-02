import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/pharmacies')({
  component: () => (
    <EntityPage
      title='Pharmacies'
      description='Pharmacies operational directory and status.'
      endpoint='/api/v1/pharmacies'
      columns={['id', 'name', 'code', 'address', 'timezone', 'is_active']}
    />
  ),
})

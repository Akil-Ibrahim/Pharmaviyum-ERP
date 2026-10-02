import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/suppliers')({
  component: () => (
    <EntityPage
      title='Suppliers'
      description='Suppliers operational directory and status.'
      endpoint='/api/v1/suppliers'
      columns={[
        'id',
        'name',
        'code',
        'contact_name',
        'email',
        'phone',
        'is_active',
      ]}
    />
  ),
})

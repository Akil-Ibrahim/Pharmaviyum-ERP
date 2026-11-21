import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/users/')({
  component: () => (
    <EntityPage
      title='Users'
      description='Administrative user accounts, roles, and account status.'
      endpoint='/api/v1/users/'
      columns={['id', 'username', 'email', 'is_active', 'is_superuser', 'created_at']}
    />
  ),
})

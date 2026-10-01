import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/users')({
  component: () => (
    <EntityPage
      title='Users / Staff'
      description='Administrative users, pharmacy staff, roles, permissions, and pharmacy assignments.'
      status='Administration'
    />
  ),
})

import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/audit-logs')({
  component: () => (
    <EntityPage
      title='Audit Logs'
      description='Security and compliance trail for sensitive administrative actions.'
      status='Security control'
    />
  ),
})

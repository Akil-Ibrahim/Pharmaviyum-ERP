import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/erp-sync')({
  component: () => (
    <EntityPage
      title='ERP Sync'
      description='Real-time synchronization between Pharmaviyum and the pharmacy ERP.'
      status='Integration foundation'
    />
  ),
})

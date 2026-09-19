import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/sync-events')({
  component: () => <EntityPage title='Sync Events' description='ERP synchronization history, status, timestamps, and processing results.' />,
})

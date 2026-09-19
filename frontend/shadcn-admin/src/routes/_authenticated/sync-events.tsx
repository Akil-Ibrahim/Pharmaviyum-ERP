import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/sync-events')({
  component: () => (
    <EntityPage title='Sync Events' description='ERP synchronization history, status, timestamps, and processing results.' endpoint='/api/v1/sync-events' columns={['id', 'integration_id', 'event_id', 'entity_type', 'entity_id', 'direction', 'status', 'received_at', 'processed_at']} />
  ),
})

import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/sync-events')({
  component: SyncPage,
})

function SyncPage() {
  return null
}

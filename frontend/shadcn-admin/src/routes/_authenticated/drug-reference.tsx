import { createFileRoute } from '@tanstack/react-router'

// The entity remains available in the sidebar, but its standalone UI is intentionally removed.
// Domain data, API endpoints, and backend workflows are unchanged.
export const Route = createFileRoute('/_authenticated/drug-reference')({
  component: () => null,
})

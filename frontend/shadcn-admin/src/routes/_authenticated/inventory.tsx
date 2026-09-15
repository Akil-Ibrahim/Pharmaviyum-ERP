import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/inventory')({
  component: () => (
    <EntityPage
      title='Inventory'
      description='Stock levels, batches, expiry dates, and inventory movements.'
    />
  ),
})

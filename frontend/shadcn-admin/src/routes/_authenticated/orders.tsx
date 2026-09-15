import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/orders')({
  component: () => (
    <EntityPage
      title='Orders'
      description='Sales orders, fulfillment status, and patient purchase history.'
    />
  ),
})

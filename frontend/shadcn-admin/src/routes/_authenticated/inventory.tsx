import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/inventory')({
  component: () => (
    <RoutePlaceholder
      title='Stock Management'
      description='Pharmacy stock levels and inventory operations.'
    />
  ),
})

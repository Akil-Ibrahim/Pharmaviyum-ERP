import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/orders')({
  component: () => (
    <RoutePlaceholder
      title='Purchase Orders'
      description='Purchase order planning and supplier ordering.'
    />
  ),
})

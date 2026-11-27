import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/procurement')({
  component: () => (
    <RoutePlaceholder
      title='Receiving'
      description='Goods receiving and purchase delivery records.'
    />
  ),
})

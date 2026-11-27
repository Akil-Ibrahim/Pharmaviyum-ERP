import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated//')({
  component: () => (
    <RoutePlaceholder
      title='Dashboard'
      description='Operational overview and pharmacy performance workspace.'
    />
  ),
})

import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/transfers')({
  component: () => (
    <RoutePlaceholder
      title='Transfers'
      description='Stock transfers between pharmacy locations.'
    />
  ),
})

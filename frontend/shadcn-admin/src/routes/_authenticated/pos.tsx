import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/pos')({
  component: () => (
    <RoutePlaceholder
      title='POS'
      description='Point-of-sale workspace for pharmacy checkout.'
    />
  ),
})

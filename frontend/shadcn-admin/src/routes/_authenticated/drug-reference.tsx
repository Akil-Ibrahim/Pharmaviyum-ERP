import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/drug-reference')({
  component: () => (
    <RoutePlaceholder
      title='Drug Catalog'
      description='Medication reference catalog and medicine lookup.'
    />
  ),
})

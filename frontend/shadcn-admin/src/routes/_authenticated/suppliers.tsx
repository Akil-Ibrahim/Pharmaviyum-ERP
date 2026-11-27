import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/suppliers')({
  component: () => (
    <RoutePlaceholder
      title='Suppliers'
      description='Supplier directory and procurement contacts.'
    />
  ),
})

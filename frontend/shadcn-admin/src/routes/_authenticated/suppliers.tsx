import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/suppliers')({
  component: () => (
    <EntityPage
      title='Suppliers'
      description='Supplier directory, purchasing relationships, and supply data.'
    />
  ),
})

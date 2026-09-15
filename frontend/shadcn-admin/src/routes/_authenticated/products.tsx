import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/products')({
  component: () => (
    <EntityPage
      title='Products'
      description='Medicines and pharmacy products with catalog and pricing data.'
    />
  ),
})

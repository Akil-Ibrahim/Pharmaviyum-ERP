import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/pharmacies')({
  component: () => (
    <RoutePlaceholder
      title='Pharmacies'
      description='Pharmacy locations and organization settings.'
    />
  ),
})

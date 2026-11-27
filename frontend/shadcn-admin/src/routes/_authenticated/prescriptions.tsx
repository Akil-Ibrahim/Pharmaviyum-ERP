import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/prescriptions')({
  component: () => (
    <RoutePlaceholder
      title='Prescriptions'
      description='Prescription records and dispensing workflow entry point.'
    />
  ),
})

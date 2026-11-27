import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/patients')({
  component: () => (
    <RoutePlaceholder
      title='Patients'
      description='Patient profiles and pharmacy care records.'
    />
  ),
})

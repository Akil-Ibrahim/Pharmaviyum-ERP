import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/defectura')({
  component: () => (
    <RoutePlaceholder
      title='Defectura'
      description='Manual and automatic replenishment planning for pharmacy inventory.'
    />
  ),
})

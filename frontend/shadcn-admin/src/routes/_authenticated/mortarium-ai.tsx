import { createFileRoute } from '@tanstack/react-router'
import { RoutePlaceholder } from '@/components/route-placeholder'

export const Route = createFileRoute('/_authenticated/mortarium-ai')({
  component: () => (
    <RoutePlaceholder
      title='Mortarium AI'
      description='AI assistant workspace for pharmacy operations and clinical support.'
    />
  ),
})

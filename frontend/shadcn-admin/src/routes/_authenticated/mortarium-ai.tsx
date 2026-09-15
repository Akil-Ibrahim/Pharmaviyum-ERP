import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/mortarium-ai')({
  component: () => (
    <EntityPage
      title='Mortarium AI'
      description='AI and RAG workspace for authorized pharmacy knowledge and patient context.'
      status='RAG workspace'
    />
  ),
})

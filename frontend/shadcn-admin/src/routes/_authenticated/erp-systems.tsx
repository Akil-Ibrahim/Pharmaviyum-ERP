import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/erp-systems')({
  component: () => <EntityPage title='ERP Systems' description='Connected enterprise resource planning systems and integration status.' />,
})

import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/suppliers')({
  component: () => (
    <EntityPage title='Suppliers' description='Supplier directory, purchasing relationships, and supply data.' endpoint='/api/v1/suppliers' columns={['id', 'name', 'code', 'contact_name', 'email', 'phone', 'is_active']} />
  ),
})

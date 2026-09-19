import { createFileRoute } from '@tanstack/react-router'
import { EntityPage } from '@/features/pharmaviyum/entity-page'

export const Route = createFileRoute('/_authenticated/patient-purchases')({
  component: () => <EntityPage title='Patient Purchases' description='Canonical patient purchase ledger, receipts, quantities, and purchase values.' />,
})

import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/erp-systems')({
  component: ERPPage,
})

function ERPPage() {
  return null
}

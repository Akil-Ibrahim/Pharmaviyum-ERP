import { Navigate, createFileRoute } from '@tanstack/react-router'

function LegacyAccountRedirect() {
  return <Navigate to='/settings' replace />
}

export const Route = createFileRoute('/_authenticated/settings/account')({
  component: LegacyAccountRedirect,
})

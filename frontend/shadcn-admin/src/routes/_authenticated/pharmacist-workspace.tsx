import { createFileRoute } from '@tanstack/react-router'
import { PharmacistWorkspace } from '@/features/pharmacist-workspace'

export const Route = createFileRoute('/_authenticated/pharmacist-workspace')({
  component: PharmacistWorkspace,
})

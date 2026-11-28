import { createFileRoute } from '@tanstack/react-router'
import { DeveloperOverview } from '@/features/developer'

export const Route = createFileRoute('/_authenticated/developer/')({
  component: DeveloperOverview,
})

import { createFileRoute } from '@tanstack/react-router'
import { DeveloperRuns } from '@/features/developer'

export const Route = createFileRoute('/_authenticated/developer/test-runs')({
  component: DeveloperRuns,
})

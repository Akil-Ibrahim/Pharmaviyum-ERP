import { createFileRoute } from '@tanstack/react-router'
import { DeveloperLogs } from '@/features/developer'

export const Route = createFileRoute('/_authenticated/developer/agent-logs')({
  component: DeveloperLogs,
})

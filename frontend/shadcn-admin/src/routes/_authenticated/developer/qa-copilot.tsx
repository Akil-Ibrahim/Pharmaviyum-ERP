import { createFileRoute } from '@tanstack/react-router'
import { DeveloperCopilot } from '@/features/developer'

export const Route = createFileRoute('/_authenticated/developer/qa-copilot')({
  component: DeveloperCopilot,
})

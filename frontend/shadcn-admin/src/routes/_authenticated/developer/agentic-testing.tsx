import { createFileRoute } from '@tanstack/react-router'
import { DeveloperAgenticTesting } from '@/features/developer'

export const Route = createFileRoute('/_authenticated/developer/agentic-testing')({
  component: DeveloperAgenticTesting,
})

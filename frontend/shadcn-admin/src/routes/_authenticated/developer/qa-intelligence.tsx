import { createFileRoute } from '@tanstack/react-router'
import { DeveloperIntelligence } from '@/features/developer'

export const Route = createFileRoute('/_authenticated/developer/qa-intelligence')({
  component: DeveloperIntelligence,
})

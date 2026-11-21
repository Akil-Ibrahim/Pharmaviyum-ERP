import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/mortarium-ai')({
  component: MortariumAI,
})

function MortariumAI() {
  return null
}

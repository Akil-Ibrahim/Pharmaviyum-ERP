import { createFileRoute } from '@tanstack/react-router'
import { Pos } from '@/features/pos'

export const Route = createFileRoute('/_authenticated/pos')({
  component: Pos,
})

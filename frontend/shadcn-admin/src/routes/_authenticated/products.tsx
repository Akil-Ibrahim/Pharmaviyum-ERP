import { createFileRoute } from '@tanstack/react-router'
import { Products } from '@/features/pharmaviyum/products'

export const Route = createFileRoute('/_authenticated/products')({
  component: Products,
})

import { type SVGProps } from 'react'
import { cn } from '@/lib/utils'

export function IconGoogle({ className, ...props }: SVGProps<SVGSVGElement>) {
  return (
    <svg role='img' viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg' width='24' height='24' className={cn(className)} {...props}>
      <title>Google</title>
      <path fill='currentColor' d='M21.35 12.27c0-.68-.06-1.34-.18-1.97H12v3.73h5.23a4.47 4.47 0 0 1-1.94 2.93v2.44h3.14c1.84-1.69 2.92-4.18 2.92-7.13Z' />
      <path fill='currentColor' d='M12 21.6c2.64 0 4.86-.87 6.48-2.36l-3.14-2.44c-.87.58-1.98.92-3.34.92-2.56 0-4.73-1.73-5.51-4.06H3.25v2.52A9.8 9.8 0 0 0 12 21.6Z' />
      <path fill='currentColor' d='M6.49 13.66A5.88 5.88 0 0 1 6.18 12c0-.58.1-1.14.31-1.66V7.82H3.25A9.6 9.6 0 0 0 2.2 12c0 1.51.36 2.94 1.05 4.18l3.24-2.52Z' />
      <path fill='currentColor' d='M12 6.28c1.44 0 2.73.5 3.75 1.48l2.81-2.81C16.85 3.36 14.63 2.4 12 2.4a9.8 9.8 0 0 0-8.75 5.42l3.24 2.52C7.27 8.01 9.44 6.28 12 6.28Z' />
    </svg>
  )
}

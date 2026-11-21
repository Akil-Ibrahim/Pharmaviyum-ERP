import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type PageHeaderProps = {
  title: ReactNode
  description?: ReactNode
  actions?: ReactNode
  className?: string
}

export function PageHeader({
  title,
  description,
  actions,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        'flex min-w-0 flex-col gap-4 sm:flex-row sm:items-end sm:justify-between',
        className
      )}
    >
      <div className='min-w-0 space-y-1'>
        <h1 className='text-2xl font-semibold tracking-tight'>{title}</h1>
        {description ? (
          <p className='text-sm text-muted-foreground'>{description}</p>
        ) : null}
      </div>
      {actions ? (
        <div className='flex min-w-0 flex-wrap items-center gap-2 sm:shrink-0'>
          {actions}
        </div>
      ) : null}
    </div>
  )
}

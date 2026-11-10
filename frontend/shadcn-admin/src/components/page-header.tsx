import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'

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
      <div className='flex min-w-0 items-start gap-3'>
        <div className='flex h-8 shrink-0 items-center gap-3'>
          <SidebarTrigger
            variant='outline'
            aria-label='Toggle navigation sidebar'
            title='Toggle navigation sidebar'
            className='size-8 rounded-lg max-md:scale-110'
          />
          <Separator orientation='vertical' className='h-6' />
        </div>
        <div className='min-w-0 space-y-1'>
          <h1 className='text-2xl font-semibold tracking-tight'>{title}</h1>
          {description ? (
            <p className='text-sm text-muted-foreground'>{description}</p>
          ) : null}
        </div>
      </div>
      {actions ? (
        <div className='flex min-w-0 flex-wrap items-center gap-2 sm:shrink-0'>
          {actions}
        </div>
      ) : null}
    </div>
  )
}

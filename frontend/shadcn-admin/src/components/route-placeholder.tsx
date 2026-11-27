import { Construction } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { Main } from '@/components/layout/main'
import { PageHeader } from '@/components/page-header'

type RoutePlaceholderProps = {
  title: string
  description: string
}

export function RoutePlaceholder({
  title,
  description,
}: RoutePlaceholderProps) {
  return (
    <Main className='flex min-w-0 flex-col gap-6'>
      <PageHeader title={title} description={description} />
      <Card>
        <CardContent className='flex flex-col items-center gap-3 px-6 py-12 text-center'>
          <Construction className='size-10 text-muted-foreground' aria-hidden='true' />
          <Badge variant='secondary'>Route active · UI pending</Badge>
          <h2 className='text-lg font-semibold'>{title}</h2>
          <p className='max-w-xl text-sm text-muted-foreground'>
            This route is active and ready for navigation. The page interface
            and workflow will be implemented in a later phase.
          </p>
        </CardContent>
      </Card>
    </Main>
  )
}

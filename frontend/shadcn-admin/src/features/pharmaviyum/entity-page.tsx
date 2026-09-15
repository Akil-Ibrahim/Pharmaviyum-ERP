import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type EntityPageProps = {
  title: string
  description: string
  status?: string
}

export function EntityPage({ title, description, status = 'Ready for integration' }: EntityPageProps) {
  return (
    <div className='space-y-6'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>{title}</h1>
        <p className='text-muted-foreground'>{description}</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Operational overview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className='flex items-center justify-between rounded-lg border p-4'>
            <div>
              <p className='font-medium'>{title}</p>
              <p className='text-sm text-muted-foreground'>{description}</p>
            </div>
            <span className='text-sm text-muted-foreground'>{status}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

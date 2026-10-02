import { createFileRoute } from '@tanstack/react-router'
import { BookOpen, Link2, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'

export const Route = createFileRoute('/_authenticated/drug-reference')({
  component: DrugReferencePage,
})

function DrugReferencePage() {
  return (
    <div className='space-y-6 p-6'>
      <div>
        <h1 className='text-2xl font-bold tracking-tight'>Drug Reference</h1>
        <p className='text-muted-foreground'>
          International reference layer for INN, ATC, reference products, and
          generic products.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Reference Search</CardTitle>
          <p className='text-sm text-muted-foreground'>
            Search by INN / active substance. Reference and generic products
            remain separate records.
          </p>
        </CardHeader>
        <CardContent>
          <div className='relative'>
            <Search className='absolute top-3 left-3 size-4 text-muted-foreground' />
            <Input
              className='pl-9'
              placeholder='Search by INN / active substance, e.g. Omeprazole...'
            />
          </div>
        </CardContent>
      </Card>
      <div className='grid gap-4 lg:grid-cols-3'>
        <ReferenceCard
          title='Drug Reference'
          icon={BookOpen}
          text='Canonical international substance and classification context.'
          tags={['INN', 'ATC']}
        />
        <ReferenceCard
          title='Reference Product'
          icon={Link2}
          text='Original/reference medicinal product associated with the reference layer.'
          tags={['Original', 'Medicinal Product']}
        />
        <ReferenceCard
          title='Generic Products'
          icon={Link2}
          text='Equivalent or generic medicinal products remain separate records.'
          tags={['Generic', 'Manufacturer']}
        />
      </div>
      <Card className='border-dashed'>
        <CardContent className='p-5 text-sm text-muted-foreground'>
          Frontend model: Drug Reference / INN / ATC → Medicinal Products →
          Local Products → Batches / FEFO → POS. Backend reference actions will
          be connected when the international catalog API is exposed.
        </CardContent>
      </Card>
    </div>
  )
}

function ReferenceCard({
  title,
  text,
  tags,
  icon: Icon,
}: {
  title: string
  text: string
  tags: string[]
  icon: typeof BookOpen
}) {
  return (
    <Card>
      <CardHeader>
        <div className='flex items-center gap-2'>
          <Icon className='size-4 text-primary' />
          <CardTitle className='text-base'>{title}</CardTitle>
        </div>
      </CardHeader>
      <CardContent className='space-y-3'>
        <p className='text-sm text-muted-foreground'>{text}</p>
        <div className='flex flex-wrap gap-2'>
          {tags.map((tag) => (
            <Badge key={tag} variant='secondary'>
              {tag}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

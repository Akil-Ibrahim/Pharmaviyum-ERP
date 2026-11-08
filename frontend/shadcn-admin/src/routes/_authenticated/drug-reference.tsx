import { useEffect, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import {
  AlertCircle,
  BookOpen,
  Database,
  Globe2,
  Loader2,
  Pill,
  Search,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

export const Route = createFileRoute('/_authenticated/drug-reference')({
  component: DrugReferencePage,
})

type DrugCatalogResult = {
  medicinal_product_id: number | null
  drug_reference_id: number | null
  inn_name: string
  atc_code: string | null
  ingredient_names: string[]
  brand_name: string | null
  product_type: string
  manufacturer: string | null
  strength: string | null
  dosage_form: string | null
  route: string | null
  package_description: string | null
  gtin: string | null
  regulatory_id: string | null
  authorization_country: string | null
  manufacturer_country: string | null
  authorization_status: string | null
  product_class: string | null
  source_record_id: string | null
  source_name: string | null
  review_status: string
}

function DrugReferencePage() {
  const [query, setQuery] = useState('')
  const [country, setCountry] = useState('')
  const [results, setResults] = useState<DrugCatalogResult[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) return

    let cancelled = false
    const timer = window.setTimeout(async () => {
      setLoading(true)
      const params = new URLSearchParams({
        q: term,
        limit: '50',
      })
      if (country.trim()) params.set('country', country.trim())

      try {
        const data = await apiFetch<DrugCatalogResult[]>(
          `/drug-catalog/search?${params.toString()}`
        )
        if (!cancelled) setResults(data)
      } catch (err) {
        if (!cancelled) {
          setResults([])
          setError(
            err instanceof Error
              ? err.message
              : 'Unable to search the international drug reference.'
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 250)

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [query, country])

  const clearSearch = () => {
    setQuery('')
    setCountry('')
    setResults([])
    setError('')
    setLoading(false)
  }

  const hasQuery = query.trim().length >= 2

  return (
    <div className='pharmacy-data-page space-y-6 p-4 md:p-6'>
      <header className='flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between'>
        <div className='flex items-start gap-3'>
          <span className='flex size-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary'>
            <BookOpen className='size-5' />
          </span>
          <div>
            <h1 className='text-2xl font-bold tracking-tight'>
              International Drug Reference
            </h1>
            <p className='mt-1 max-w-3xl text-sm text-muted-foreground'>
              Search normalized active ingredients, ATC codes, medicinal
              products, strengths, dosage forms, manufacturers, and regulatory
              identifiers.
            </p>
          </div>
        </div>
        <Button
          variant='outline'
          size='sm'
          onClick={clearSearch}
          disabled={!query && !country && results.length === 0 && !error}
        >
          <X className='mr-2 size-4' />
          Clear
        </Button>
      </header>

      <Card>
        <CardHeader className='pb-3'>
          <CardTitle className='flex items-center gap-2 text-base'>
            <Search className='size-4 text-primary' />
            Reference search
          </CardTitle>
          <p className='text-sm text-muted-foreground'>
            Enter at least 2 characters. Search results are reference data,
            not pharmacy stock or dispensing authorization.
          </p>
        </CardHeader>
        <CardContent>
          <div className='grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(220px,0.38fr)]'>
            <label className='space-y-2 text-sm font-medium'>
              Medicine, INN, ingredient, brand, strength, ATC or GTIN
              <div className='relative'>
                <Search className='pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground' />
                <Input
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value)
                    setResults([])
                    setError('')
                    setLoading(false)
                  }}
                  className='h-11 pl-9'
                  placeholder='e.g. omeprazole, 500 mg, or 1234567890123'
                  autoComplete='off'
                />
              </div>
            </label>
            <label className='space-y-2 text-sm font-medium'>
              Authorization country
              <div className='relative'>
                <Globe2 className='pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground' />
                <Input
                  value={country}
                  onChange={(event) => {
                    setCountry(event.target.value)
                    setResults([])
                    setError('')
                    setLoading(false)
                  }}
                  className='h-11 pl-9'
                  placeholder='Exact country name'
                  autoComplete='off'
                />
              </div>
              <span className='block text-xs font-normal text-muted-foreground'>
                Optional exact match, case-insensitive.
              </span>
            </label>
          </div>
          <div className='mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground'>
            <span>
              Search is performed against the authenticated catalog API.
            </span>
            {loading && (
              <span className='inline-flex items-center gap-2'>
                <Loader2 className='size-3.5 animate-spin' />
                Searching reference records…
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {error && (
        <div
          role='alert'
          className='flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm'
        >
          <AlertCircle className='mt-0.5 size-4 shrink-0 text-destructive' />
          <span>{error}</span>
        </div>
      )}

      <section className='space-y-3' aria-live='polite'>
        <div className='flex flex-wrap items-center justify-between gap-2'>
          <div>
            <h2 className='font-semibold'>Catalog records</h2>
            <p className='text-sm text-muted-foreground'>
              {hasQuery
                ? loading
                  ? 'Updating results…'
                  : `${results.length} record${results.length === 1 ? '' : 's'} returned`
                : 'Results will appear here after you enter a search term.'}
            </p>
          </div>
          <Badge variant='outline'>Reference data only</Badge>
        </div>

        {!hasQuery && !loading && (
          <Card className='border-dashed'>
            <CardContent className='flex min-h-44 flex-col items-center justify-center gap-2 p-6 text-center'>
              <Database className='size-8 text-muted-foreground/60' />
              <p className='font-medium'>Search the international catalog</p>
              <p className='max-w-lg text-sm text-muted-foreground'>
                Start with an INN or active ingredient. You can also search by
                brand, manufacturer, dosage form, strength, ATC code, package,
                GTIN, or regulatory identifier.
              </p>
            </CardContent>
          </Card>
        )}

        {hasQuery && !loading && !error && results.length === 0 && (
          <Card className='border-dashed'>
            <CardContent className='flex min-h-36 flex-col items-center justify-center gap-2 p-6 text-center'>
              <Pill className='size-7 text-muted-foreground/60' />
              <p className='font-medium'>No reference records found</p>
              <p className='text-sm text-muted-foreground'>
                Try another search term or remove the authorization-country
                filter.
              </p>
            </CardContent>
          </Card>
        )}

        {results.length > 0 && (
          <div className='grid gap-3 xl:grid-cols-2'>
            {results.map((item, index) => {
              const displayName = item.brand_name || item.inn_name
              const isPending = item.review_status === 'pending_review'
              const identity = `${item.source_name ?? 'catalog'}-${item.source_record_id ?? item.medicinal_product_id ?? item.drug_reference_id ?? index}`

              return (
                <Card key={identity} className='min-w-0'>
                  <CardHeader className='space-y-2 pb-3'>
                    <div className='flex flex-wrap items-start justify-between gap-2'>
                      <div className='min-w-0'>
                        <CardTitle className='text-base leading-snug'>
                          {displayName}
                        </CardTitle>
                        {item.brand_name && (
                          <p className='mt-1 text-sm text-muted-foreground'>
                            INN: {item.inn_name}
                          </p>
                        )}
                      </div>
                      <div className='flex shrink-0 flex-wrap gap-1.5'>
                        <Badge variant='secondary'>
                          {item.product_type || 'reference'}
                        </Badge>
                        <Badge variant={isPending ? 'outline' : 'secondary'}>
                          {isPending ? 'Pending review' : 'Reference'}
                        </Badge>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className='space-y-3 text-sm'>
                    <div className='grid gap-x-4 gap-y-2 sm:grid-cols-2'>
                      <Detail label='Active ingredient(s)'>
                        {item.ingredient_names.length
                          ? item.ingredient_names.join(', ')
                          : item.inn_name}
                      </Detail>
                      <Detail label='Strength / dosage form'>
                        {[item.strength, item.dosage_form]
                          .filter(Boolean)
                          .join(' · ') || 'Not specified'}
                      </Detail>
                      <Detail label='Manufacturer / holder'>
                        {item.manufacturer || 'Not specified'}
                      </Detail>
                      <Detail label='Route'>
                        {item.route || 'Not specified'}
                      </Detail>
                      <Detail label='Authorization country'>
                        {item.authorization_country || 'Not specified'}
                      </Detail>
                      <Detail label='Authorization status'>
                        {item.authorization_status || 'Not provided'}
                      </Detail>
                      <Detail label='ATC code'>
                        {item.atc_code || 'Not provided'}
                      </Detail>
                      <Detail label='GTIN / barcode'>
                        {item.gtin || 'Not provided'}
                      </Detail>
                    </div>
                    {(item.package_description ||
                      item.regulatory_id ||
                      item.source_name) && (
                      <div className='flex flex-wrap gap-x-4 gap-y-1 border-t pt-3 text-xs text-muted-foreground'>
                        {item.package_description && (
                          <span>Pack: {item.package_description}</span>
                        )}
                        {item.regulatory_id && (
                          <span>Regulatory ID: {item.regulatory_id}</span>
                        )}
                        {item.source_name && (
                          <span>Source: {item.source_name}</span>
                        )}
                      </div>
                    )}
                    <p className='rounded-md bg-muted/60 p-2.5 text-xs text-muted-foreground'>
                      Reference record only. It does not create a local
                      pharmacy product, price, stock balance, batch, or expiry
                      date and does not establish local market authorization.
                    </p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}

function Detail({ label, children }: { label: string; children: string }) {
  return (
    <div className='min-w-0'>
      <p className='text-xs text-muted-foreground'>{label}</p>
      <p className='mt-0.5 break-words font-medium'>{children}</p>
    </div>
  )
}

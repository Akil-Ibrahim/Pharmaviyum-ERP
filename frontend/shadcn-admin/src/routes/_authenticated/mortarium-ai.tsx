import { useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { Bot, Check, Loader2, Search, RotateCcw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api-client'

export const Route = createFileRoute('/_authenticated/mortarium-ai')({
  component: MortariumAI,
})

const languageCodes = [
  'af','am','ar','az','be','bg','bn','bs','ca','cs','cy','da','de','el','en','es','et','eu','fa','fi','fil','fr','ga','gl','gu','he','hi','hr','hu','hy','id','is','it','ja','ka','kk','km','kn','ko','ky','lo','lt','lv','mk','ml','mn','mr','ms','mt','my','ne','nl','no','pa','pl','pt','ro','ru','sk','sl','so','sq','sr','sv','sw','ta','te','tg','th','tk','tr','uk','ur','uz','vi','zh','zu',
]

const fallbackNames: Record<string, string> = {
  en: 'English',
  ru: 'Русский',
  uk: 'Українська',
}

function languageName(code: string) {
  try {
    return new Intl.DisplayNames(['en'], { type: 'language' }).of(code) ?? fallbackNames[code] ?? code
  } catch {
    return fallbackNames[code] ?? code
  }
}

function MortariumAI() {
  const [language, setLanguage] = useState(() => localStorage.getItem('pharmaviyum-ai-language') || 'en')
  const [search, setSearch] = useState('')
  const [pharmacyId, setPharmacyId] = useState<number>()
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  useEffect(() => { localStorage.setItem('pharmaviyum-ai-language', language) }, [language])
  const [loading, setLoading] = useState(false)
  useEffect(() => { apiFetch<{ pharmacies: { id: number }[] }>('/api/v1/ai/context').then(({ pharmacies }) => setPharmacyId(pharmacies[0]?.id)).catch(() => undefined) }, [])
  async function ask(text: string) {
    if (!text.trim() || !pharmacyId || loading) return
    setLoading(true)
    setQuery('')
    try {
      const result = await apiFetch<{ answer: string }>('/api/v1/ai/query', { method: 'POST', body: JSON.stringify({ query: text.trim(), pharmacy_id: pharmacyId, language, country: 'VN' }) })
      setAnswer(result.answer)
    } catch (error) {
      setAnswer(error instanceof Error ? error.message : 'AI processing failed')
    } finally { setLoading(false) }
  }

  const languages = useMemo(
    () => languageCodes
      .map((code) => ({ code, name: languageName(code) }))
      .sort((a, b) => a.name.localeCompare(b.name, 'en')),
    []
  )

  const filtered = languages.filter(({ name }) =>
    name.toLowerCase().includes(search.trim().toLowerCase())
  )

  return (
    <div className='min-h-full space-y-6 p-6'>
      <header className='flex flex-wrap items-start justify-between gap-4'>
        <div>
          <div className='flex items-center gap-2'>
            <div className='flex size-9 items-center justify-center rounded-xl bg-primary text-primary-foreground'><Bot className='size-5' /></div>
            <div><p className='text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground'>Pharmacy Intelligence</p><h1 className='text-2xl font-bold tracking-tight'>Mortarium AI</h1></div>
          </div>
          <p className='mt-3 max-w-2xl text-sm text-muted-foreground'>Ask questions about patients, sales, inventory, prescriptions, forecasts, and pharmacy operations. Answers will use the selected language and available CRM context.</p>
        </div>
        <Button variant='outline' className='gap-2' onClick={() => { setAnswer(''); setQuery('') }}><RotateCcw className='size-4' /> New conversation</Button>
      </header>

      <div className='grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]'>
        <section className='rounded-2xl border bg-card p-6 shadow-sm'>
          <div className='flex min-h-[420px] flex-col items-center justify-center text-center'>
            <div className='mb-5 flex size-16 items-center justify-center rounded-2xl border bg-muted/40'><Bot className='size-8 text-muted-foreground' /></div>
            <h2 className='text-xl font-semibold'>{answer ? 'Mortarium response' : 'How can Mortarium help?'}</h2>
            <p className='mt-2 max-w-lg whitespace-pre-wrap text-sm text-muted-foreground'>{answer || 'Use natural language to analyze pharmacy data. The production AI query endpoint is connected to the existing agent and tenant-scoped context.'}</p>
            <div className='mt-6 w-full max-w-2xl'>
              <div className='mb-3 flex gap-2'><input value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') void ask(query) }} placeholder='Ask Mortarium AI…' className='flex-1 rounded-lg border bg-background px-3 py-2 text-sm' /><Button onClick={() => void ask(query)} disabled={!pharmacyId || loading || !query.trim()}>{loading ? <Loader2 className='size-4 animate-spin' /> : 'Ask'}</Button></div>
              <div className='grid gap-2 sm:grid-cols-2'>
              {['What products are below reorder level?','Show this month’s revenue trend','Which batches expire within 30 days?','Analyze patient purchase activity'].map((prompt) => <button key={prompt} type='button' onClick={() => void ask(prompt)} className='rounded-xl border p-3 text-left text-sm transition hover:bg-muted'>{prompt}</button>)}
            </div>
            </div>
          </div>
        </section>

        <aside className='rounded-2xl border bg-card p-5 shadow-sm'>
          <div className='mb-4'><p className='font-semibold'>Language</p><p className='text-xs text-muted-foreground'>English is the default. Choose the response language.</p></div>
          <label className='mb-4 flex items-center gap-2 rounded-lg border px-3 py-2'>
            <Search className='size-4 text-muted-foreground' />
            <span className='sr-only'>Search language</span>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder='Search language...' className='w-full bg-transparent text-sm outline-none' />
          </label>
          <div className='max-h-[520px] space-y-1 overflow-y-auto pe-1'>
            {filtered.map(({ code, name }) => (
              <label key={code} className='flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm hover:bg-muted'>
                <input type='checkbox' checked={language === code} onChange={() => setLanguage(code)} className='size-4 accent-primary' />
                <span className='flex-1'>{name}</span>
                {language === code && <Check className='size-4 text-primary' />}
              </label>
            ))}
          </div>
        </aside>
      </div>

      <div className='grid gap-4 md:grid-cols-4'>
        {[
          ['INSIGHT', 'What happened'],
          ['ANALYSIS', 'Why it happened'],
          ['FORECAST', 'What may happen next'],
          ['RECOMMENDATION', 'What to consider'],
        ].map(([title, description]) => <div key={title} className='rounded-xl border bg-card p-4'><p className='text-xs font-semibold tracking-wider text-muted-foreground'>{title}</p><p className='mt-1 text-sm'>{description}</p></div>)}
      </div>
    </div>
  )
}

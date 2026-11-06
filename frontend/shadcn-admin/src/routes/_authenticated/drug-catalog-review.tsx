import { useCallback, useEffect, useState } from 'react'
import { AlertCircle, CheckCircle2, ClipboardCheck, Loader2, RefreshCw, Search, ShieldAlert, XCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { apiFetch } from '@/lib/api-client'
import { useAuthStore } from '@/stores/auth-store'
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/drug-catalog-review')({
  component: DrugCatalogReviewPage,
})

type SourceRecord = {
  id: number
  source_name: string
  source_record_id: string
  source_version: string
  source_url: string | null
  license_terms: string | null
  extracted_at: string
  normalized_payload: Record<string, unknown> | null
  review_status: 'pending_review' | 'approved' | 'rejected' | 'duplicate'
  match_confidence: number | null
  review_notes: string | null
}
type MatchCandidate = {
  target_type: 'drug_reference' | 'medicinal_product'
  drug_reference_id: number
  medicinal_product_id: number | null
  display_name: string
  confidence: number
  reasons: string[]
}

function DrugCatalogReviewPage() {
  const roles = useAuthStore((state) => state.auth.user?.role ?? [])
  const isAdmin = roles.includes('admin')
  const [records, setRecords] = useState<SourceRecord[]>([])
  const [selected, setSelected] = useState<SourceRecord | null>(null)
  const [matches, setMatches] = useState<MatchCandidate[]>([])
  const [selectedMatch, setSelectedMatch] = useState<MatchCandidate | null>(null)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [matching, setMatching] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const loadRecords = useCallback(async () => {
    try {
      const result = await apiFetch<SourceRecord[]>('/api/v1/drug-catalog/sources?review_status=pending_review&limit=200')
      setRecords(result)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось загрузить очередь проверки')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (isAdmin) void loadRecords()
  }, [isAdmin, loadRecords])

  const chooseRecord = (record: SourceRecord) => {
    setSelected(record)
    setMatches([])
    setSelectedMatch(null)
    setNotes('')
    setError('')
  }

  const findMatches = async () => {
    if (!selected) return
    setMatching(true)
    setError('')
    try {
      const result = await apiFetch<MatchCandidate[]>(`/api/v1/drug-catalog/sources/${selected.id}/matches`)
      setMatches(result)
      setSelectedMatch(result[0] ?? null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось получить предложения совпадений')
    } finally {
      setMatching(false)
    }
  }

  const submitReview = async (decision: 'approved' | 'duplicate' | 'rejected', createNew = false) => {
    if (!selected) return
    if (decision !== 'rejected' && !selectedMatch && !createNew) {
      setError('Для решения требуется выбрать целевую запись каталога')
      return
    }
    setSaving(true)
    setError('')
    const body = {
      review_status: decision,
      matched_drug_reference_id: createNew || decision === 'rejected' || selectedMatch?.target_type !== 'drug_reference' ? null : selectedMatch.drug_reference_id,
      matched_medicinal_product_id: createNew || decision === 'rejected' || selectedMatch?.target_type !== 'medicinal_product' ? null : selectedMatch?.medicinal_product_id ?? null,
      create_new: createNew,
      match_confidence: decision === 'rejected' || createNew ? null : selectedMatch?.confidence ?? null,
      review_notes: notes.trim() || null,
    }
    try {
      await apiFetch<SourceRecord>(`/api/v1/drug-catalog/sources/${selected.id}/review`, {
        method: 'PATCH',
        body: JSON.stringify(body),
      })
      setSelected(null)
      setMatches([])
      setSelectedMatch(null)
      setLoading(true)
      await loadRecords()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось сохранить решение')
    } finally {
      setSaving(false)
    }
  }

  if (!isAdmin) {
    return <div className='p-6'><Card><CardContent className='flex items-center gap-3 p-6'><ShieldAlert className='size-5 text-destructive'/><div><h1 className='font-semibold'>Доступ только для администратора</h1><p className='text-sm text-muted-foreground'>Проверка внешних источников каталога доступна superuser-аккаунтам.</p></div></CardContent></Card></div>
  }

  return (
    <div className='space-y-6 p-4 md:p-6'>
      <header className='flex flex-wrap items-center justify-between gap-3'>
        <div className='flex items-center gap-3'><span className='flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary'><ClipboardCheck className='size-5'/></span><div><h1 className='text-2xl font-bold tracking-tight'>Проверка Drug Catalog</h1><p className='text-sm text-muted-foreground'>Очередь импорта, provenance и подтверждение совпадений с существующим справочником</p></div></div>
        <Button variant='outline' onClick={() => { setLoading(true); void loadRecords() }} disabled={loading}><RefreshCw className={`mr-2 size-4 ${loading ? 'animate-spin' : ''}`}/>Обновить</Button>
      </header>
      <div className='grid gap-4 lg:grid-cols-[minmax(280px,0.8fr)_minmax(0,1.6fr)]'>
        <Card className='min-w-0'>
          <CardHeader><div className='flex items-center justify-between'><CardTitle className='text-base'>Ожидают проверки</CardTitle><Badge variant='secondary'>{records.length}</Badge></div></CardHeader>
          <CardContent className='space-y-2'>
            {loading && <div className='flex items-center gap-2 py-4 text-sm text-muted-foreground'><Loader2 className='size-4 animate-spin'/>Загрузка…</div>}
            {!loading && records.length === 0 && <p className='py-5 text-sm text-muted-foreground'>Нет записей, ожидающих проверки.</p>}
            {records.map((record) => <button key={record.id} onClick={() => chooseRecord(record)} className={`w-full rounded-lg border p-3 text-left transition-colors hover:bg-accent ${selected?.id === record.id ? 'border-primary bg-accent' : ''}`}>
              <div className='flex items-center justify-between gap-2'><span className='font-medium'>{record.source_name}</span><Badge variant='outline'>#{record.id}</Badge></div>
              <p className='mt-1 truncate text-sm text-muted-foreground'>{record.source_record_id}</p>
              <p className='mt-1 text-xs text-muted-foreground'>{new Date(record.extracted_at).toLocaleString()}</p>
            </button>)}
          </CardContent>
        </Card>
        <div className='min-w-0 space-y-4'>
          {error && <div role='alert' className='flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm'><AlertCircle className='mt-0.5 size-4 shrink-0 text-destructive'/>{error}</div>}
          {!selected && <Card><CardContent className='flex min-h-56 flex-col items-center justify-center gap-2 p-6 text-center text-muted-foreground'><Search className='size-8 opacity-50'/><p>Выберите запись слева, чтобы изучить источник и проверить возможные совпадения.</p></CardContent></Card>}
          {selected && <>
            <Card>
              <CardHeader><div className='flex flex-wrap items-center justify-between gap-2'><CardTitle className='text-base'>Источник #{selected.id}: {selected.source_name}</CardTitle><Badge variant='outline'>pending_review</Badge></div></CardHeader>
              <CardContent className='space-y-3 text-sm'>
                <div className='grid gap-2 sm:grid-cols-2'><div><span className='text-muted-foreground'>Source record ID</span><p className='font-medium'>{selected.source_record_id}</p></div><div><span className='text-muted-foreground'>Версия источника</span><p className='break-all font-medium'>{selected.source_version}</p></div><div><span className='text-muted-foreground'>Извлечено</span><p>{new Date(selected.extracted_at).toLocaleString()}</p></div><div><span className='text-muted-foreground'>Source URL</span><p className='break-all'>{selected.source_url ?? 'Не указан'}</p></div></div>
                <div><span className='text-muted-foreground'>Условия лицензии / использования</span><p className='whitespace-pre-wrap'>{selected.license_terms ?? 'Не указаны — требуется ручная проверка перед распространением данных.'}</p></div>
                <details><summary className='cursor-pointer font-medium'>Нормализованные данные источника</summary><pre className='mt-2 max-h-64 overflow-auto rounded-md bg-muted p-3 text-xs'>{JSON.stringify(selected.normalized_payload, null, 2)}</pre></details>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><div className='flex flex-wrap items-center justify-between gap-2'><CardTitle className='text-base'>Предложения совпадений</CardTitle><Button size='sm' variant='outline' onClick={() => void findMatches()} disabled={matching}><Search className='mr-2 size-4'/>{matching ? 'Поиск…' : 'Найти совпадения'}</Button></div></CardHeader>
              <CardContent className='space-y-2'>
                {matches.length === 0 && <p className='text-sm text-muted-foreground'>Предложения рассчитываются только по запросу и не изменяют каталог или статус записи.</p>}
                {matches.map((match) => <button key={`${match.target_type}-${match.medicinal_product_id ?? match.drug_reference_id}`} onClick={() => setSelectedMatch(match)} className={`w-full rounded-lg border p-3 text-left hover:bg-accent ${selectedMatch === match ? 'border-primary bg-accent' : ''}`}>
                  <div className='flex flex-wrap items-center justify-between gap-2'><span className='font-medium'>{match.display_name}</span><div className='flex items-center gap-2'><Badge variant='secondary'>{Math.round(match.confidence * 100)}%</Badge>{selectedMatch === match && <CheckCircle2 className='size-4 text-primary'/>}</div></div>
                  <p className='mt-1 text-xs text-muted-foreground'>{match.target_type === 'medicinal_product' ? `Medicinal Product #${match.medicinal_product_id}` : `Drug Reference #${match.drug_reference_id}`}</p>
                  <p className='mt-2 text-xs text-muted-foreground'>{match.reasons.join(' · ') || 'Нет дополнительных объяснений'}</p>
                </button>)}
                {matches.length > 0 && <p className='text-xs text-muted-foreground'>Совпадения — подсказки для ручного решения. Они не подтверждают регистрацию препарата или право продажи в конкретной стране.</p>}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className='text-base'>Решение администратора</CardTitle></CardHeader>
              <CardContent className='space-y-3'>
                <Textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder='Комментарий к проверке (необязательно)' rows={3}/>
                <div className='flex flex-wrap gap-2'>
                  <Button onClick={() => void submitReview('approved')} disabled={saving || !selectedMatch}><CheckCircle2 className='mr-2 size-4'/>Подтвердить совпадение</Button>
                  <Button variant='outline' onClick={() => void submitReview('approved', true)} disabled={saving}>Создать новую запись и подтвердить</Button>
                  <Button variant='outline' onClick={() => void submitReview('duplicate')} disabled={saving || !selectedMatch}>Отметить дубликатом</Button>
                  <Button variant='destructive' onClick={() => void submitReview('rejected')} disabled={saving}><XCircle className='mr-2 size-4'/>Отклонить</Button>
                </div>
                <p className='text-xs text-muted-foreground'>«Создать новую запись» добавляет только глобальные Drug Reference и Medicinal Product из проверенных данных источника. Ни одна кнопка здесь не создаёт аптечный SKU, цену, партию или остаток и не подтверждает право продажи на локальном рынке.</p>
              </CardContent>
            </Card>
          </>}
        </div>
      </div>
    </div>
  )
}

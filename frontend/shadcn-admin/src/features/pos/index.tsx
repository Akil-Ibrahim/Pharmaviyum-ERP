import { useEffect, useMemo, useRef, useState } from 'react'
import { Search, Plus, Minus, Trash2, CreditCard, Pill, X, Receipt, Barcode } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type LocalProduct = {
  id: number; name: string; sku: string; dosage_strength: string | null
  dosage_form: string | null; units_per_pack: number; manufacturer: string | null
  inn_name: string | null; gtin: string | null; barcode: string | null
  price: number; stock: number; medicinal_product_id: number | null
  batch_number?: string | null; expiry_date?: string | null
}
type DrugCatalogResult = {
  medicinal_product_id: number | null; drug_reference_id: number | null; inn_name: string
  atc_code: string | null; ingredient_names: string[]; brand_name: string | null
  product_type: string; manufacturer: string | null; strength: string | null
  dosage_form: string | null; route: string | null; package_description: string | null
  gtin: string | null; regulatory_id: string | null; authorization_country: string | null
  source_record_id?: string | null; source_name?: string | null; review_status?: string
  authorization_status?: string | null; product_class?: string | null
}
type InventoryLot = { inventory_id: number; lot_number: string | null; expiry_date: string | null; quantity: number; reserved_quantity: number; available_quantity: number; expiry_date_missing: boolean }
type CartItem = LocalProduct & { quantity: number }
type PharmacyOption = { id: number; name: string }
type SaleResult = {
  id: number; receipt_number: string; status: string; total: string
  payments: { id: number; method: string; status: string }[]
}
const money = (value: number) => new Intl.NumberFormat('uk-UA', { style: 'currency', currency: 'UAH' }).format(value)

export function Pos() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<LocalProduct[]>([])
  const [lotsByProduct, setLotsByProduct] = useState<Record<number, InventoryLot[]>>({})
  const [referenceResults, setReferenceResults] = useState<DrugCatalogResult[]>([])
  const [cart, setCart] = useState<CartItem[]>([])
  const [pharmacies, setPharmacies] = useState<PharmacyOption[]>([])
  const [pharmacyId, setPharmacyId] = useState<number>()
  const [loading, setLoading] = useState(false)
  const [notice, setNotice] = useState('')
  const [checkoutOpen, setCheckoutOpen] = useState(false)
  const [receivingOpen, setReceivingOpen] = useState(false)
  const [receivingProductId, setReceivingProductId] = useState('')
  const [receivingLot, setReceivingLot] = useState('')
  const [receivingExpiry, setReceivingExpiry] = useState('')
  const [receivingQuantity, setReceivingQuantity] = useState('')
  const [paymentMethod, setPaymentMethod] = useState<'cash' | 'card_terminal' | 'online'>('cash')
  const [cashReceived, setCashReceived] = useState('')
  const [processing, setProcessing] = useState(false)
  const [sale, setSale] = useState<SaleResult | null>(null)
  const searchRef = useRef<HTMLInputElement>(null)
  const idempotencyKey = useRef(crypto.randomUUID())

  const total = useMemo(() => cart.reduce((sum, item) => sum + item.price * item.quantity, 0), [cart])
  const cash = Number(cashReceived) || 0
  const units = cart.reduce((sum, item) => sum + item.quantity, 0)

  useEffect(() => {
    apiFetch<PharmacyOption[]>('/api/v1/pharmacies').then(items => {
      setPharmacies(items)
      setPharmacyId(items[0]?.id)
    }).catch(() => setNotice('Не удалось загрузить список аптек.'))
  }, [])

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2 || !pharmacyId) {
      setResults([])
      setReferenceResults([])
      return
    }
    let cancelled = false
    const timer = window.setTimeout(async () => {
      setLoading(true)
      try {
        const [local, reference] = await Promise.all([
          apiFetch<LocalProduct[]>(`/api/v1/pos/products/search?q=${encodeURIComponent(term)}&pharmacy_id=${pharmacyId}&limit=30`),
          apiFetch<DrugCatalogResult[]>(`/drug-catalog/search?q=${encodeURIComponent(term)}&limit=50`).catch(() => []),
        ])
        if (!cancelled) { setResults(local); setReferenceResults(reference) }
      } catch {
        if (!cancelled) { setResults([]); setNotice('Ошибка поиска аптечного ассортимента.') }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }, 200)
    return () => { cancelled = true; window.clearTimeout(timer) }
  }, [query, pharmacyId])

  const formatExpiry = (value?: string | null) => value ? new Date(`${value}T00:00:00`).toLocaleDateString('uk-UA') : 'Не указан — определяется по партии'

  useEffect(() => {
    if (!pharmacyId || cart.length === 0) { setLotsByProduct({}); return }
    let cancelled = false
    Promise.all(cart.map(async item => {
      try {
        const lots = await apiFetch<InventoryLot[]>(`/api/v1/pos/products/${item.id}/lots?pharmacy_id=${pharmacyId}`)
        return [item.id, lots] as const
      } catch {
        return [item.id, []] as const
      }
    })).then(entries => {
      if (!cancelled) setLotsByProduct(Object.fromEntries(entries))
    })
    return () => { cancelled = true }
  }, [cart.map(item => item.id).join(','), pharmacyId])



  const addProduct = (product: LocalProduct) => {
    if (product.stock < 1) { setNotice('Нет доступного остатка.'); return }
    setCart(items => {
      const found = items.find(item => item.id === product.id)
      if (found) return items.map(item => item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) } : item)
      return [...items, { ...product, quantity: 1 }]
    })
    setNotice('')
    setQuery('')
    searchRef.current?.focus()
  }

  const changeQuantity = (id: number, delta: number) => setCart(items => items.flatMap(item => {
    if (item.id !== id) return [item]
    const next = Math.min(item.stock, item.quantity + delta)
    return next > 0 ? [{ ...item, quantity: next }] : []
  }))


  const receiveStock = async () => {
    const quantity = Number(receivingQuantity)
    if (!pharmacyId || !receivingProductId || !receivingLot.trim() || !receivingExpiry || !Number.isInteger(quantity) || quantity <= 0) {
      setNotice('Заполните товар, номер партии, срок годности и целое положительное количество.')
      return
    }
    setProcessing(true)
    setNotice('')
    try {
      const received = await apiFetch<{ lot_quantity: number; available_quantity: number; lot_number: string }>('/api/v1/pos/inventory/receive', {
        method: 'POST',
        body: JSON.stringify({
          pharmacy_id: pharmacyId,
          product_id: Number(receivingProductId),
          lot_number: receivingLot.trim(),
          expiry_date: `${receivingExpiry}T00:00:00`,
          quantity,
        }),
      })
      setReceivingOpen(false)
      setReceivingLot('')
      setReceivingExpiry('')
      setReceivingQuantity('')
      setNotice(`Приход принят. Партия ${received.lot_number}: доступно ${received.available_quantity} шт.`)
      if (query.trim().length >= 2) {
        const refreshed = await apiFetch<LocalProduct[]>(`/api/v1/pos/products/search?q=${encodeURIComponent(query.trim())}&pharmacy_id=${pharmacyId}&limit=30`)
        setResults(refreshed)
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Не удалось зарегистрировать приход.')
    } finally { setProcessing(false) }
  }

  const completeSale = async () => {
    if (!pharmacyId || !cart.length || processing) return
    if (paymentMethod === 'cash' && cash < total) { setNotice('Полученная сумма меньше суммы чека.'); return }
    setProcessing(true)
    setNotice('')
    try {
      const result = await apiFetch<SaleResult>('/api/v1/pos/checkout', {
        method: 'POST',
        body: JSON.stringify({
          pharmacy_id: pharmacyId, idempotency_key: idempotencyKey.current,
          currency: 'UAH', items: cart.map(item => ({ product_id: item.id, quantity: item.quantity })),
          discount_total: 0, payment_method: paymentMethod,
          ...(paymentMethod === 'cash' ? { cash_received: cash } : {}),
        }),
      })
      setSale(result)
      idempotencyKey.current = crypto.randomUUID()
      if (result.status === 'completed') {
        setCart([])
        setCheckoutOpen(false)
        setNotice(`Продажа завершена. Чек № ${result.receipt_number}`)
      } else {
        setNotice(`Платёж ожидает подтверждения провайдера. Чек ${result.receipt_number}; товар зарезервирован.`)
      }
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Продажа не подтверждена. Проверьте состояние операции перед повтором.')
    } finally { setProcessing(false) }
  }

  return (
    <div className='min-h-screen bg-muted/20 p-3 md:p-5'>
      <div className='mx-auto flex min-h-[calc(100vh-2.5rem)] w-full max-w-[1920px] flex-col gap-4'>
        <header className='flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-background p-4'>
          <div className='flex items-center gap-3'><span className='flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground'><Pill /></span><div><h1 className='text-xl font-bold'>Аптечная касса</h1><p className='text-xs text-muted-foreground'>Выбор препаратов и оформление продажи</p></div></div>
          <div className='flex flex-wrap items-center gap-2'><Button variant='outline' onClick={() => { setReceivingOpen(true); setQuery(''); setResults([]); searchRef.current?.focus() }}>Приёмка на склад</Button><label className='flex items-center gap-2 text-sm'>Аптека<select className='h-9 max-w-[220px] rounded-md border bg-background px-2' value={pharmacyId ?? ''} onChange={e => { setPharmacyId(Number(e.target.value)); setCart([]); setSale(null) }}><option value=''>Выберите аптеку</option>{pharmacies.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label></div>
        </header>

        {notice && <div role='status' className='flex items-center justify-between gap-3 rounded-lg border bg-background p-3 text-sm'>{notice}<button aria-label='Закрыть уведомление' onClick={() => setNotice('')}><X className='size-4' /></button></div>}

        {cart.length > 0 && (
          <Card className='min-h-0 flex-1 overflow-y-auto'>
            <CardHeader className='pb-3'><div className='flex items-center justify-between'><CardTitle>Выбранные препараты</CardTitle><Badge>{units} шт.</Badge></div><p className='text-sm text-muted-foreground'>Проверьте количество и состав продажи.</p></CardHeader>
            <CardContent className='space-y-3'>
              {cart.map(item => <div key={item.id} className='flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3'>
                <div className='min-w-0 flex-1'><p className='font-semibold'>{item.name}</p><p className='text-xs text-muted-foreground'>{[item.inn_name, item.dosage_strength, item.dosage_form, item.manufacturer].filter(Boolean).join(' · ')}</p><p className='mt-1 text-sm'>Цена: {money(item.price)} · Доступно: {item.stock} · В чеке: {item.quantity} шт.</p><div className='mt-2 space-y-1 text-xs text-muted-foreground'><p className='font-medium text-foreground'>Складские партии (сначала ближайший срок годности):</p>{(lotsByProduct[item.id] || []).length ? lotsByProduct[item.id].map(lot => <p key={lot.inventory_id}>Партия: {lot.lot_number || 'без номера'} · Годен до: {formatExpiry(lot.expiry_date)} · Доступно: {lot.available_quantity} шт.</p>) : <p>Нет доступных партий с указанным сроком годности. Проверьте складской приход.</p>}</div><p className='text-xs text-muted-foreground'>Штрихкод: {item.barcode || item.gtin || 'не указан'}</p></div>
                <div className='flex items-center gap-2'><Button size='icon' variant='outline' aria-label='Уменьшить количество' onClick={() => changeQuantity(item.id, -1)}><Minus className='size-4' /></Button><span className='w-8 text-center font-semibold'>{item.quantity}</span><Button size='icon' variant='outline' aria-label='Увеличить количество' disabled={item.quantity >= item.stock} onClick={() => changeQuantity(item.id, 1)}><Plus className='size-4' /></Button><Button size='icon' variant='ghost' aria-label='Удалить препарат' onClick={() => setCart(rows => rows.filter(row => row.id !== item.id))}><Trash2 className='size-4' /></Button></div>
                <strong className='w-28 text-right'>{money(item.price * item.quantity)}</strong>
              </div>)}
              <div className='flex flex-wrap items-center justify-between gap-3 border-t pt-4'><span className='text-lg font-semibold'>Итого: {money(total)}</span><Button size='lg' onClick={() => { setCashReceived(total.toFixed(2)); setCheckoutOpen(true) }}><CreditCard className='mr-2 size-4' /> Вывести в чек</Button></div>
            </CardContent>
          </Card>
        )}

        {sale?.status === 'completed' && <Card><CardContent className='flex items-center justify-between gap-3 p-4'><div className='flex items-center gap-2'><Receipt className='size-5 text-primary' /><div><p className='font-semibold'>Чек № {sale.receipt_number}</p><p className='text-sm text-muted-foreground'>Продажа зарегистрирована · {money(Number(sale.total))}</p></div></div><Button variant='outline' onClick={() => { setSale(null); setNotice('Новая продажа.'); searchRef.current?.focus() }}>Новая продажа</Button></CardContent></Card>}

        <Card className='mt-auto max-h-[42vh] shrink-0 overflow-y-auto border-primary/20 shadow-sm'>
          <CardHeader className='pb-3'><CardTitle className='flex items-center gap-2'><Search className='size-5 text-primary' /> Поиск и каталог препаратов</CardTitle><p className='text-sm text-muted-foreground'>Введите название, МНН, бренд, дозировку, производителя или отсканируйте штрихкод.</p></CardHeader>
          <CardContent className='space-y-3'>
            <form onSubmit={e => { e.preventDefault(); if (results.length === 1) addProduct(results[0]) }} className='flex gap-2'><Input ref={searchRef} autoFocus value={query} onChange={e => setQuery(e.target.value)} placeholder='Например, омепразол 20 мг или ибупрофен…' className='h-12 text-base' /><Button type='submit' className='h-12'><Search className='mr-2 size-4' /> Найти</Button></form>
            <p className='flex items-center gap-2 text-xs text-muted-foreground'><Barcode className='size-4' /> Сканер штрихкода поддерживается как клавиатурный ввод.</p>
            {loading && <p className='py-4 text-center text-sm text-muted-foreground'>Ищем препараты…</p>}
            {!loading && query.trim().length >= 2 && results.length === 0 && <p className='py-5 text-center text-sm text-muted-foreground'>В ассортименте этой аптеки совпадений нет.</p>}
            {results.map(product => <div key={product.id} className='flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3'><div className='min-w-0 flex-1'><p className='font-semibold'>{product.name}</p><p className='text-xs text-muted-foreground'>Бренд / производитель: {product.manufacturer || 'не указан'} · МНН: {product.inn_name || 'не указано'}</p><p className='text-xs text-muted-foreground'>{[product.dosage_strength, product.dosage_form].filter(Boolean).join(' · ')}</p><p className='mt-1 text-xs text-muted-foreground'>SKU: {product.sku} · Доступно: {product.stock} · Цена: {money(product.price)}</p><p className='text-xs text-muted-foreground'>Штрихкод: {product.barcode || product.gtin || 'не указан'}</p></div><Button onClick={() => addProduct(product)} disabled={product.stock < 1}><Plus className='mr-1 size-4' /> Добавить</Button></div>)}
            {query.trim().length >= 2 && referenceResults.length > 0 && <div className='space-y-2 border-t pt-3'><p className='text-sm font-semibold'>Международный справочник — только для ознакомления</p>{referenceResults.map((item, index) => <div key={item.source_record_id ?? item.medicinal_product_id ?? index} className='rounded-lg border border-dashed p-3'><p className='font-medium'>{item.brand_name || item.inn_name}</p><p className='text-xs text-muted-foreground'>Бренд: {item.brand_name || 'не указан'} · Производитель: {item.manufacturer || 'не указан'}</p><p className='text-xs text-muted-foreground'>{[item.inn_name, item.strength, item.dosage_form, item.authorization_country].filter(Boolean).join(' · ')}</p><p className='text-xs text-muted-foreground'>Штрихкод / GTIN: {item.gtin || 'нет в источнике'} · Остаток и срок годности: определяются только после заведения партии в аптеке</p><Badge variant='outline' className='mt-2'>Справочная запись — не товар аптеки</Badge></div>)}</div>}
            <p className='pt-1 text-xs text-muted-foreground'>В чек можно добавить только товар выбранной аптеки с назначенной ценой и доступным остатком. Справочные записи каталога не продаются напрямую.</p>
          </CardContent>
        </Card>
      </div>

      {receivingOpen && <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4'><section role='dialog' aria-modal='true' aria-labelledby='receiving-title' className='w-full max-w-lg space-y-4 rounded-xl border bg-background p-5 shadow-xl'><div className='flex items-center justify-between'><h2 id='receiving-title' className='text-xl font-bold'>Приёмка лекарств на склад</h2><Button size='icon' variant='ghost' onClick={() => setReceivingOpen(false)} aria-label='Закрыть'><X /></Button></div><p className='text-sm text-muted-foreground'>Приход будет записан в остатки выбранной аптеки и сразу станет доступен POS с учётом срока годности.</p><label className='block text-sm font-medium'>Найти товар<Input className='mt-2 h-11' value={query} onChange={e => setQuery(e.target.value)} placeholder='Название, МНН, SKU или штрихкод' /></label><div className='max-h-36 space-y-1 overflow-y-auto rounded-md border p-2'>{results.map(product => <button type='button' key={product.id} onClick={() => setReceivingProductId(String(product.id))} className={`flex w-full items-center justify-between rounded-md p-2 text-left text-sm hover:bg-muted ${receivingProductId === String(product.id) ? 'bg-primary/10 outline outline-1 outline-primary' : ''}`}><span>{product.name}<span className='block text-xs text-muted-foreground'>{product.sku} · {product.manufacturer || 'производитель не указан'}</span></span><span>{money(product.price)}</span></button>)}{query.trim().length >= 2 && results.length === 0 && <p className='p-2 text-xs text-muted-foreground'>Товар не найден в локальном ассортименте. Сначала заведите его как товар аптеки.</p>}</div><label className='block text-sm font-medium'>Номер партии / серии<Input className='mt-2 h-11' value={receivingLot} onChange={e => setReceivingLot(e.target.value)} maxLength={100} /></label><label className='block text-sm font-medium'>Срок годности<Input className='mt-2 h-11' type='date' min={new Date().toISOString().slice(0,10)} value={receivingExpiry} onChange={e => setReceivingExpiry(e.target.value)} /></label><label className='block text-sm font-medium'>Количество поступления<Input className='mt-2 h-11' type='number' min='1' step='1' value={receivingQuantity} onChange={e => setReceivingQuantity(e.target.value)} /></label><div className='flex gap-2'><Button className='flex-1' disabled={processing || !receivingProductId || !receivingLot.trim() || !receivingExpiry || Number(receivingQuantity) <= 0} onClick={() => void receiveStock()}>{processing ? 'Сохранение…' : 'Принять на склад'}</Button><Button variant='outline' onClick={() => setReceivingOpen(false)} disabled={processing}>Отмена</Button></div></section></div>}

      {checkoutOpen && <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4'><section role='dialog' aria-modal='true' aria-labelledby='checkout-title' className='w-full max-w-md space-y-4 rounded-xl border bg-background p-5 shadow-xl'><div className='flex items-center justify-between'><h2 id='checkout-title' className='text-xl font-bold'>Оплата и закрытие чека</h2><Button size='icon' variant='ghost' onClick={() => setCheckoutOpen(false)} aria-label='Закрыть'><X /></Button></div><div className='rounded-lg bg-muted p-4'><p className='text-sm text-muted-foreground'>Сумма к оплате</p><p className='text-3xl font-bold'>{money(total)}</p></div><label className='block text-sm font-medium'>Способ оплаты<select className='mt-2 h-11 w-full rounded-md border bg-background px-3' value={paymentMethod} onChange={e => setPaymentMethod(e.target.value as typeof paymentMethod)}><option value='cash'>Наличными</option><option value='card_terminal'>Банковской картой через терминал</option><option value='online'>Онлайн-оплата</option></select></label>{paymentMethod === 'cash' ? <label className='block text-sm font-medium'>Получено наличными<Input className='mt-2 h-11' type='number' min='0' step='0.01' value={cashReceived} onChange={e => setCashReceived(e.target.value)} /><span className='mt-2 block text-sm text-muted-foreground'>Сдача: {money(Math.max(0, cash - total))}</span></label> : <p className='rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm'>Оплата будет считаться успешной только после подтверждения подключённого платёжного провайдера. Сейчас без настроенного провайдера продажа останется ожидающей подтверждения.</p>}<Button className='w-full' size='lg' disabled={processing || !pharmacyId || (paymentMethod === 'cash' && cash < total)} onClick={() => void completeSale()}>{processing ? 'Обработка…' : paymentMethod === 'cash' ? 'Подтвердить оплату и выдать чек' : 'Создать платёж'}</Button><Button variant='outline' className='w-full' onClick={() => setCheckoutOpen(false)} disabled={processing}>Назад к препаратам</Button></section></div>}
    </div>
  )
}

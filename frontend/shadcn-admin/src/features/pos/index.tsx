import { useEffect, useMemo, useRef, useState } from 'react'
import { Barcode, Check, CreditCard, Minus, Plus, Search, ShoppingCart, Tag, Trash2, UserRound, X } from 'lucide-react'
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
}
type DrugCatalogResult = {
  medicinal_product_id: number; drug_reference_id: number; inn_name: string
  atc_code: string | null; ingredient_names: string[]; brand_name: string | null
  product_type: string; manufacturer: string | null; strength: string | null
  dosage_form: string | null; route: string | null; package_description: string | null
  gtin: string | null; regulatory_id: string | null
}
type CartItem = LocalProduct & { quantity: number }
const money = (value: number) => new Intl.NumberFormat('uk-UA', { style: 'currency', currency: 'UAH' }).format(value)

export function Pos() {
  const [query, setQuery] = useState('')
  const [cart, setCart] = useState<CartItem[]>([])
  const [localResults, setLocalResults] = useState<LocalProduct[]>([])
  const [referenceResults, setReferenceResults] = useState<DrugCatalogResult[]>([])
  const [loading, setLoading] = useState(false)
  const [referenceLoading, setReferenceLoading] = useState(false)
  const [localError, setLocalError] = useState(false)
  const [referenceError, setReferenceError] = useState(false)
  const [discount, setDiscount] = useState('0')
  const [cashReceived, setCashReceived] = useState('')
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [customer, setCustomer] = useState('')
  const [notice, setNotice] = useState('')
  const searchRef = useRef<HTMLInputElement>(null)
  const discountPercent = Math.min(100, Math.max(0, Number(discount) || 0))
  const subtotal = useMemo(() => cart.reduce((sum, item) => sum + item.price * item.quantity, 0), [cart])
  const discountAmount = subtotal * discountPercent / 100
  const total = subtotal - discountAmount
  const quantity = cart.reduce((sum, item) => sum + item.quantity, 0)
  const cash = Number(cashReceived) || 0

  useEffect(() => {
    const term = query.trim()
    if (term.length < 2) { setLocalResults([]); setReferenceResults([]); setLoading(false); setReferenceLoading(false); setLocalError(false); setReferenceError(false); return }
    let cancelled = false
    setLoading(true); setReferenceLoading(true); setLocalError(false); setReferenceError(false)
    apiFetch<LocalProduct[]>(`/products/search?q=${encodeURIComponent(term)}&limit=20`)
      .then(items => { if (!cancelled) setLocalResults(items) })
      .catch(() => { if (!cancelled) { setLocalResults([]); setLocalError(true) } })
      .finally(() => { if (!cancelled) setLoading(false) })
    apiFetch<DrugCatalogResult[]>(`/drug-catalog/search?q=${encodeURIComponent(term)}&limit=8`)
      .then(items => { if (!cancelled) setReferenceResults(items) })
      .catch(() => { if (!cancelled) { setReferenceResults([]); setReferenceError(true) } })
      .finally(() => { if (!cancelled) setReferenceLoading(false) })
    return () => { cancelled = true }
  }, [query])

  const addToCart = (product: LocalProduct) => {
    setNotice('')
    setCart(items => {
      const existing = items.find(item => item.id === product.id)
      if (existing) return items.map(item => item.id === product.id ? { ...item, quantity: Math.min(item.quantity + 1, product.stock) } : item)
      if (product.stock < 1) return items
      return [...items, { ...product, quantity: 1 }]
    })
    setQuery('')
    searchRef.current?.focus()
  }
  const updateQuantity = (id: number, delta: number) => setCart(items => items.flatMap(item => {
    if (item.id !== id) return [item]
    const next = item.quantity + delta
    return next > 0 ? [{ ...item, quantity: Math.min(next, item.stock) }] : []
  }))
  const scanSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const term = query.trim()
    if (!term) return
    const match = localResults.find(item => item.barcode === term || item.gtin === term || item.sku.toLowerCase() === term.toLowerCase())
    if (match) addToCart(match)
    else setNotice('Точный штрихкод не найден. Проверьте результаты поиска и наличие товара в локальном каталоге.')
  }
  const beginPayment = () => {
    if (!cart.length) return
    setPaymentOpen(true)
    setCashReceived(total.toFixed(2))
  }
  const confirmPayment = () => {
    // Orders currently have no persisted line items or payment/stock-deduction transaction.
    // Never claim a sale was completed until the backend can atomically record it.
    setNotice('Корзина подготовлена. Проведение продажи отключено до подключения безопасной серверной операции: позиции чека, оплата и списание остатков должны сохраняться одной транзакцией.')
    setPaymentOpen(false)
  }

  return <div className='pharmacy-pos min-h-full space-y-5 p-4 md:p-6'>
    <header className='flex flex-col justify-between gap-3 sm:flex-row sm:items-center'>
      <div><div className='flex items-center gap-2'><span className='flex size-10 items-center justify-center rounded-xl bg-primary/10 text-primary'><ShoppingCart className='size-5'/></span><div><h1 className='text-2xl font-bold tracking-tight'>Аптечная касса</h1><p className='text-sm text-muted-foreground'>POS · Продажа и проверка наличия</p></div></div></div>
      <div className='flex flex-wrap items-center gap-2'><Badge variant='outline' className='gap-2 px-3 py-2'><span className='size-2 rounded-full bg-emerald-500'/>Каталог API</Badge><Button variant='outline' onClick={() => { setCart([]); setDiscount('0'); setCustomer(''); setNotice('Чек очищен'); searchRef.current?.focus() }}><Trash2 className='mr-2 size-4'/>Новый чек</Button></div>
    </header>
    {notice && <div role='status' className='flex items-start justify-between gap-3 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm'><span>{notice}</span><button aria-label='Закрыть сообщение' onClick={() => setNotice('')}><X className='size-4'/></button></div>}
    <div className='grid gap-5 2xl:grid-cols-[minmax(0,1fr)_420px]'>
      <section className='space-y-4'>
        <Card className='overflow-hidden border-primary/20 shadow-sm'>
          <CardHeader className='bg-primary/[0.04] pb-4'><div className='flex items-center justify-between gap-3'><div><CardTitle>Поиск товара</CardTitle><p className='mt-1 text-sm text-muted-foreground'>Название, МНН, производитель, SKU или штрихкод</p></div><Barcode className='size-6 text-primary'/></div></CardHeader>
          <CardContent className='pt-4'><form onSubmit={scanSubmit} className='flex gap-2'><div className='relative min-w-0 flex-1'><Search className='absolute left-3 top-3 size-4 text-muted-foreground'/><Input ref={searchRef} value={query} onChange={e => setQuery(e.target.value)} placeholder='Сканируйте штрихкод или введите название…' className='h-11 pl-9' autoComplete='off' aria-label='Поиск товара по названию или штрихкоду'/></div><Button type='submit' className='h-11'><Barcode className='mr-2 size-4'/><span className='hidden sm:inline'>Найти / сканировать</span><span className='sm:hidden'>Найти</span></Button></form><p className='mt-2 text-xs text-muted-foreground'>USB-сканер в режиме клавиатуры можно использовать прямо в поле поиска; для точного добавления нужен совпадающий локальный штрихкод.</p></CardContent>
        </Card>
        <Card><CardHeader className='pb-3'><div className='flex items-center justify-between gap-2'><CardTitle>Товары аптеки</CardTitle><Badge variant='secondary'>Склад и цена</Badge></div></CardHeader><CardContent className='space-y-3'>
          {loading && <p className='py-5 text-center text-sm text-muted-foreground'>Поиск по каталогу…</p>}
          {localError && <p className='rounded-lg bg-destructive/10 p-3 text-sm text-destructive'>Не удалось загрузить локальный каталог. Проверьте подключение к API и права доступа.</p>}
          {!loading && !localError && query.trim().length >= 2 && localResults.length === 0 && <p className='py-5 text-center text-sm text-muted-foreground'>В локальном каталоге совпадений нет.</p>}
          {localResults.map(product => <div key={product.id} className='flex flex-col gap-3 rounded-xl border p-3 transition-colors hover:border-primary/40 hover:bg-muted/20 sm:flex-row sm:items-center sm:justify-between'>
            <div className='min-w-0 flex-1'><div className='flex flex-wrap items-center gap-2'><p className='font-semibold'>{product.name}</p>{product.medicinal_product_id && <Badge variant='secondary'>МНН связано</Badge>}</div><p className='mt-1 text-sm text-muted-foreground'>{[product.inn_name, product.dosage_strength, product.dosage_form, product.manufacturer].filter(Boolean).join(' · ') || 'Нет дополнительных сведений'}</p><p className='text-xs text-muted-foreground'>SKU: {product.sku}{(product.barcode || product.gtin) ? ` · ШК: ${product.barcode || product.gtin}` : ''}</p></div>
            <div className='flex items-center justify-between gap-4 sm:justify-end'><div className='text-right'><p className='font-bold tabular-nums'>{money(product.price)}</p><p className={'text-xs '+(product.stock < 1 ? 'text-destructive' : product.stock <= 5 ? 'text-amber-600' : 'text-emerald-600')}>Остаток: {product.stock}</p></div><Button size='sm' onClick={() => addToCart(product)} disabled={product.stock < 1}><Plus className='mr-1 size-4'/>В чек</Button></div>
          </div>)}
          {query.trim().length < 2 && <div className='rounded-lg border border-dashed p-6 text-center'><Search className='mx-auto mb-2 size-6 text-muted-foreground'/><p className='text-sm font-medium'>Начните вводить название или отсканируйте штрихкод</p><p className='mt-1 text-xs text-muted-foreground'>Поиск покажет только реальные товары из каталога вашей аптеки.</p></div>}
          {query.trim().length >= 2 && <details className='border-t pt-3'><summary className='cursor-pointer text-sm font-medium text-muted-foreground'>Международный справочник лекарств (не склад)</summary><div className='mt-3 space-y-2'>{referenceLoading && <p className='text-sm text-muted-foreground'>Поиск справочника…</p>}{referenceError && <p className='text-sm text-destructive'>Справочник недоступен.</p>}{referenceResults.map(item => <div key={item.medicinal_product_id} className='rounded-lg bg-muted/40 p-3'><div className='flex flex-wrap items-center gap-2'><p className='font-medium'>{item.brand_name || [item.inn_name, item.strength].filter(Boolean).join(' ')}</p><Badge variant='outline'>Только справочник</Badge></div><p className='text-xs text-muted-foreground'>{[item.inn_name, item.strength, item.dosage_form, item.manufacturer].filter(Boolean).join(' · ')}</p></div>)}</div><p className='mt-2 text-xs text-muted-foreground'>Справочная запись не подтверждает местную регистрацию, цену или наличие. Добавить её в чек напрямую нельзя.</p></details>}
        </CardContent></Card>
      </section>
      <aside className='space-y-4'>
        <Card className='h-fit overflow-hidden border-primary/20 shadow-sm'><CardHeader className='bg-primary/[0.05] pb-3'><div className='flex items-center justify-between'><CardTitle className='flex items-center gap-2'><ReceiptIcon/>Текущий чек</CardTitle><Badge>{quantity} ед.</Badge></div><p className='text-xs text-muted-foreground'>Черновик продажи · цены из каталога</p></CardHeader><CardContent className='space-y-4 pt-4'>
          {cart.length === 0 ? <div className='rounded-xl border border-dashed p-7 text-center'><ShoppingCart className='mx-auto mb-2 size-7 text-muted-foreground'/><p className='text-sm font-medium'>Чек пока пуст</p><p className='mt-1 text-xs text-muted-foreground'>Добавьте препарат из локального каталога.</p></div> : <div className='max-h-[360px] space-y-3 overflow-auto pr-1'>{cart.map(item => <div key={item.id} className='rounded-lg border p-3'><div className='flex items-start justify-between gap-2'><div className='min-w-0'><p className='text-sm font-semibold leading-snug'>{item.name}</p><p className='mt-1 text-xs text-muted-foreground'>{money(item.price)} за ед. · остаток {item.stock}</p></div><Button variant='ghost' size='icon' className='size-7 shrink-0 text-muted-foreground hover:text-destructive' aria-label={`Удалить ${item.name}`} onClick={() => setCart(items => items.filter(row => row.id !== item.id))}><Trash2 className='size-4'/></Button></div><div className='mt-3 flex items-center justify-between'><div className='flex items-center gap-2'><Button variant='outline' size='icon' className='size-8' aria-label='Уменьшить количество' onClick={() => updateQuantity(item.id, -1)}><Minus className='size-3'/></Button><span className='w-6 text-center text-sm font-semibold tabular-nums'>{item.quantity}</span><Button variant='outline' size='icon' className='size-8' aria-label='Увеличить количество' disabled={item.quantity >= item.stock} onClick={() => updateQuantity(item.id, 1)}><Plus className='size-3'/></Button></div><span className='font-semibold tabular-nums'>{money(item.price * item.quantity)}</span></div></div>)}</div>}
          <div className='rounded-xl bg-muted/40 p-3'><div className='mb-2 flex items-center gap-2 text-sm font-medium'><UserRound className='size-4 text-muted-foreground'/>Покупатель / карта лояльности</div><Input value={customer} onChange={e => setCustomer(e.target.value)} placeholder='Телефон или номер карты'/><p className='mt-1 text-xs text-muted-foreground'>Поле для идентификации; начисление бонусов ещё не подключено.</p></div>
          <div className='rounded-xl border p-3'><div className='mb-2 flex items-center gap-2 text-sm font-medium'><Tag className='size-4 text-muted-foreground'/>Скидка на чек</div><div className='flex items-center gap-2'><Input type='number' min='0' max='100' step='0.5' value={discount} onChange={e => setDiscount(e.target.value)} aria-label='Скидка в процентах'/><span className='text-sm text-muted-foreground'>%</span><div className='flex gap-1'>{[0,5,10].map(value => <Button key={value} variant={discountPercent === value ? 'default' : 'outline'} size='sm' onClick={() => setDiscount(String(value))}>{value}%</Button>)}</div></div></div>
          <div className='space-y-2 border-t pt-4 text-sm'><div className='flex justify-between text-muted-foreground'><span>Сумма</span><span className='tabular-nums'>{money(subtotal)}</span></div><div className='flex justify-between text-rose-600'><span>Скидка</span><span className='tabular-nums'>−{money(discountAmount)}</span></div><div className='flex items-end justify-between gap-3 pt-1'><span className='font-semibold'>К оплате</span><span className='text-2xl font-bold tracking-tight tabular-nums'>{money(total)}</span></div></div>
          <Button className='h-12 w-full text-base' size='lg' onClick={beginPayment} disabled={!cart.length}><CreditCard className='mr-2 size-5'/>Перейти к оплате</Button>
          <p className='text-xs leading-relaxed text-muted-foreground'>Оплата открывает проверку суммы, но не проводит продажу. Сохранение чека и списание остатков требуют серверной транзакции.</p>
        </CardContent></Card>
        <div className='grid grid-cols-3 gap-2'>{[{label:'Позиции',value:String(cart.length),color:'text-sky-600 bg-sky-500/10'},{label:'Единицы',value:String(quantity),color:'text-emerald-600 bg-emerald-500/10'},{label:'Скидка',value:`${discountPercent}%`,color:'text-rose-600 bg-rose-500/10'}].map(metric => <div key={metric.label} className='rounded-xl border p-3'><div className={`mb-2 flex size-8 items-center justify-center rounded-lg ${metric.color}`}><Check className='size-4'/></div><p className='text-xl font-bold tabular-nums'>{metric.value}</p><p className='text-xs text-muted-foreground'>{metric.label}</p></div>)}</div>
      </aside>
    </div>
    {paymentOpen && <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4' role='presentation' onMouseDown={e => { if (e.target === e.currentTarget) setPaymentOpen(false) }}><section role='dialog' aria-modal='true' aria-labelledby='payment-title' className='w-full max-w-md rounded-2xl border bg-background p-5 shadow-2xl'><div className='mb-4 flex items-center justify-between'><div><h2 id='payment-title' className='text-xl font-bold'>Оплата чека</h2><p className='text-sm text-muted-foreground'>Проверьте сумму перед проведением</p></div><Button variant='ghost' size='icon' onClick={() => setPaymentOpen(false)} aria-label='Закрыть'><X className='size-4'/></Button></div><div className='rounded-xl bg-primary/5 p-4'><p className='text-sm text-muted-foreground'>Итого к оплате</p><p className='text-3xl font-bold tabular-nums'>{money(total)}</p></div><label className='mt-4 block text-sm font-medium' htmlFor='cash-received'>Получено наличными, ₴</label><Input id='cash-received' type='number' min='0' step='0.01' value={cashReceived} onChange={e => setCashReceived(e.target.value)} className='mt-2 h-11'/><div className='mt-3 flex justify-between rounded-lg border p-3 text-sm'><span className='text-muted-foreground'>Сдача</span><strong className={cash < total ? 'text-destructive' : 'text-emerald-600'}>{money(Math.max(0, cash - total))}</strong></div><div className='mt-4 rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm'>Проведение продажи временно недоступно: backend пока не сохраняет строки чека, оплату и списание остатков одной атомарной операцией.</div><Button className='mt-4 w-full' onClick={confirmPayment}><Check className='mr-2 size-4'/>Проверить и закрыть</Button></section></div>}
  </div>
}

function ReceiptIcon() { return <span className='flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary'><ShoppingCart className='size-4'/></span> }

import { useEffect, useState, type ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import { Activity, ArrowDownRight, ArrowRight, ArrowUpRight, Boxes, ClipboardList, RefreshCw, ShoppingCart, UsersRound } from 'lucide-react'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api-client'

type Summary = {
  as_of: string
  patients: { active: number }
  sales: { today: number; by_category: { category: string; lines: number; packs: number; revenue: number }[] }
  revenue: { month: number }
  orders: { month: number; completed_month: number }
  prescriptions: { month: number }
  inventory: { retail_value: number; items: number; low_stock: number; days_on_hand: number | null; expired: number; critical_expiry: number; warning_expiry: number; expiry_green: number }
  attention: { stockout_items: number; near_expiry_value: number; slow_moving_items: number; slow_moving_stock_value: number; slow_moving: { id: number; name: string; packs_90d: number; stock: number; stock_value: number }[] }
  top_products: { id: number; name: string; packs: number; revenue: number; stock: number }[]
  reorder_attention: { id: number; name: string; available_packs: number; reorder_level: number; packs_30d: number; days_on_hand: number | null; stock_value: number }[]
}
const money = (value: number) => new Intl.NumberFormat('uk-UA', { style: 'currency', currency: 'UAH', maximumFractionDigits: 0 }).format(value)
const number = (value: number) => new Intl.NumberFormat('uk-UA').format(value)

export function Dashboard() {
  const [data, setData] = useState<Summary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const load = () => {
    setLoading(true); setError('')
    apiFetch<Summary>('/api/v1/dashboard/summary')
      .then(setData)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Не удалось загрузить аналитику'))
      .finally(() => setLoading(false))
  }
  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer) }, [])
  const inventory = data?.inventory
  const expiryTotal = (inventory?.expired ?? 0) + (inventory?.critical_expiry ?? 0) + (inventory?.warning_expiry ?? 0) + (inventory?.expiry_green ?? 0)
  const cards = [
    { label: 'Продажи сегодня', value: money(data?.sales.today ?? 0), hint: 'Фактические продажи', progress: (data?.sales.today ?? 0) > 0 ? 100 : 0, color: '#f59e0b', track: '#fef3c7', icon: ShoppingCart },
    { label: 'Выручка за месяц', value: money(data?.revenue.month ?? 0), hint: `${number(data?.orders.completed_month ?? 0)} заказов выполнено`, progress: (data?.revenue.month ?? 0) > 0 ? 100 : 0, color: '#f97316', track: '#ffedd5', icon: Activity },
    { label: 'Товары на складе', value: number(inventory?.items ?? 0), hint: `${number(inventory?.low_stock ?? 0)} требуют пополнения`, progress: inventory?.items ? Math.max(5, 100 - (inventory.low_stock / inventory.items) * 100) : 0, color: '#10b981', track: '#d1fae5', icon: Boxes },
    { label: 'Активные пациенты', value: number(data?.patients.active ?? 0), hint: `${number(data?.prescriptions.month ?? 0)} рецептов за месяц`, progress: (data?.patients.active ?? 0) > 0 ? 100 : 0, color: '#d946ef', track: '#fae8ff', icon: UsersRound },
  ]
  return <>
    <Header><Search/><ThemeSwitch/><ConfigDrawer/><ProfileDropdown/></Header>
    <Main>
      <div className='pharmaviyum-dashboard space-y-5'>
        <section className='pharmacy-dashboard-hero relative flex flex-col gap-4 rounded-2xl border p-5 sm:flex-row sm:items-center sm:justify-between sm:p-7'>
          <div className='relative z-10'><div className='mb-2 flex items-center gap-2'><Badge variant='secondary' className='rounded-md'>PHARMAVIYUM ERP</Badge><span className='text-xs text-muted-foreground'>Аптечная аналитика</span></div><h1 className='text-2xl font-bold tracking-tight sm:text-3xl'>Добро пожаловать в аптеку</h1><p className='mt-2 max-w-2xl text-sm text-muted-foreground'>Продажи, остатки, сроки годности и ключевые показатели в одном рабочем пространстве.</p></div>
          <div className='relative z-10 flex shrink-0 gap-2'><Button variant='outline' onClick={load} disabled={loading}><RefreshCw className={'mr-2 size-4 '+(loading?'animate-spin':'')}/>Обновить</Button><Button asChild><Link to='/pos'><ShoppingCart className='mr-2 size-4'/>Открыть кассу</Link></Button></div>
        </section>
        {error && <div role='alert' className='flex flex-wrap items-center justify-between gap-3 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm'><span>Не удалось загрузить реальные показатели: {error}</span><Button variant='outline' size='sm' onClick={load}>Повторить</Button></div>}
        <section><div className='mb-3 flex items-end justify-between gap-3'><div><h2 className='text-base font-bold'>Показатели аптеки</h2><p className='text-sm text-muted-foreground'>Данные из API · без демонстрационных продаж</p></div><span className='text-xs text-muted-foreground'>{data?.as_of ? new Date(data.as_of).toLocaleString('uk-UA') : '—'}</span></div>
          <div className='grid gap-3 sm:grid-cols-2 xl:grid-cols-4'>{cards.map(card => <div key={card.label} className='flex min-w-0 items-center gap-4 rounded-2xl border bg-card p-4 sm:p-5'><RingMetric progress={card.progress} color={card.color} track={card.track} value={card.value} icon={<card.icon className='size-5'/>}/><div className='min-w-0 flex-1'><p className='text-sm font-medium text-muted-foreground'>{card.label}</p><p className='mt-1 truncate text-xl font-bold tracking-tight tabular-nums'>{loading ? '…' : card.value}</p><p className='mt-1 text-xs text-muted-foreground'>{card.hint}</p></div></div>)}</div>
        </section>
        <section className='grid gap-4 xl:grid-cols-[minmax(0,1.25fr)_minmax(320px,.75fr)]'>
          <div className='rounded-2xl border bg-card p-4 sm:p-5'><div className='mb-4 flex items-center justify-between gap-3'><div><h2 className='font-bold'>Состояние запасов</h2><p className='text-xs text-muted-foreground'>Остатки и контроль сроков годности</p></div><Boxes className='size-5 text-muted-foreground'/></div>
            <div className='grid gap-4 sm:grid-cols-2'><div className='flex items-center gap-4'><RingMetric progress={inventory?.items ? Math.max(0, 100 - inventory.low_stock / inventory.items * 100) : 0} color='#10b981' track='#d1fae5' value={number(inventory?.items ?? 0)} icon={<Boxes className='size-5'/>} size={104}/><div><p className='text-sm font-semibold'>Общий ассортимент</p><p className='mt-1 text-xs text-muted-foreground'>Розничная стоимость</p><p className='mt-1 font-bold tabular-nums'>{money(inventory?.retail_value ?? 0)}</p></div></div>
            <div className='flex items-center gap-4'><RingMetric progress={expiryTotal ? (inventory?.expiry_green ?? 0) / expiryTotal * 100 : 0} color='#d946ef' track='#fae8ff' value={number(inventory?.expiry_green ?? 0)} icon={<Activity className='size-5'/>} size={104}/><div><p className='text-sm font-semibold'>Сроки в норме</p><p className='mt-1 text-xs text-muted-foreground'>Позиции с запасом более 12 мес.</p><p className='mt-1 font-bold'>{number(inventory?.expiry_green ?? 0)} позиций</p></div></div></div>
            <div className='mt-5 space-y-3'>{[{label:'Просрочено',value:inventory?.expired??0,color:'#ef4444'},{label:'Критично · до 3 месяцев',value:inventory?.critical_expiry??0,color:'#f97316'},{label:'Внимание · 3–12 месяцев',value:inventory?.warning_expiry??0,color:'#f59e0b'},{label:'В норме · более 12 месяцев',value:inventory?.expiry_green??0,color:'#10b981'}].map(row=><div key={row.label} className='flex items-center gap-3 text-sm'><span className='size-2.5 rounded-full' style={{background:row.color}}/><span className='flex-1 text-muted-foreground'>{row.label}</span><span className='font-semibold tabular-nums'>{number(row.value)}</span></div>)}</div>
          </div>
          <div className='rounded-2xl border bg-card p-4 sm:p-5'><div className='mb-4 flex items-center justify-between'><div><h2 className='font-bold'>Требуют внимания</h2><p className='text-xs text-muted-foreground'>Операционные сигналы</p></div><Activity className='size-5 text-amber-500'/></div>
            <div className='space-y-3'>{[{label:'Нулевой остаток',value:data?.attention.stockout_items??0,detail:'товаров закончились',color:'bg-rose-500/10 text-rose-600'},{label:'Низкий остаток',value:inventory?.low_stock??0,detail:'товаров на пополнение',color:'bg-amber-500/10 text-amber-600'},{label:'Скоро истекает срок',value:inventory?.critical_expiry??0,detail:'позиций до 3 месяцев',color:'bg-orange-500/10 text-orange-600'},{label:'Медленно движется',value:data?.attention.slow_moving_items??0,detail:'позиций без продаж за 90 дней',color:'bg-violet-500/10 text-violet-600'}].map(row=><div key={row.label} className='flex items-center gap-3 rounded-xl border p-3'><div className={'flex size-10 shrink-0 items-center justify-center rounded-xl text-lg font-bold '+row.color}>{loading?'…':number(row.value)}</div><div className='min-w-0'><p className='text-sm font-semibold'>{row.label}</p><p className='text-xs text-muted-foreground'>{row.detail}</p></div><ArrowDownRight className='ml-auto size-4 shrink-0 text-muted-foreground'/></div>)}</div>
            <Button variant='outline' className='mt-4 w-full' asChild><Link to='/inventory'>Перейти к складу<ArrowRight className='ml-2 size-4'/></Link></Button>
          </div>
        </section>
        <section className='grid gap-4 xl:grid-cols-2'>
          <div className='rounded-2xl border bg-card p-4 sm:p-5'><div className='mb-4 flex items-center justify-between'><div><h2 className='font-bold'>Популярные товары</h2><p className='text-xs text-muted-foreground'>По фактическим продажам</p></div><ShoppingCart className='size-5 text-muted-foreground'/></div>
            {loading ? <p className='py-6 text-center text-sm text-muted-foreground'>Загрузка…</p> : !data?.top_products.length ? <EmptyState text='Пока нет данных о завершённых продажах.'/> : <div className='overflow-x-auto'><table className='w-full text-sm'><thead><tr className='border-b text-left text-muted-foreground'><th className='pb-2 font-medium'>Товар</th><th className='pb-2 text-right font-medium'>Продано</th><th className='pb-2 text-right font-medium'>Выручка</th></tr></thead><tbody>{data.top_products.slice(0,6).map(product=><tr key={product.id} className='border-b last:border-0'><td className='max-w-[240px] py-3 pr-3'><p className='truncate font-medium'>{product.name}</p><p className='text-xs text-muted-foreground'>Остаток: {number(product.stock)}</p></td><td className='py-3 text-right tabular-nums'>{number(product.packs)}</td><td className='py-3 text-right font-semibold tabular-nums'>{money(product.revenue)}</td></tr>)}</tbody></table></div>}
          </div>
          <div className='rounded-2xl border bg-card p-4 sm:p-5'><div className='mb-4 flex items-center justify-between'><div><h2 className='font-bold'>Пополнение запасов</h2><p className='text-xs text-muted-foreground'>Товары на уровне точки заказа</p></div><ClipboardList className='size-5 text-muted-foreground'/></div>
            {loading ? <p className='py-6 text-center text-sm text-muted-foreground'>Загрузка…</p> : !data?.reorder_attention.length ? <EmptyState text='Нет товаров ниже точки заказа.'/> : <div className='space-y-3'>{data.reorder_attention.slice(0,5).map(item=><div key={item.id} className='flex items-center gap-3'><div className='flex size-9 shrink-0 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600'><Boxes className='size-4'/></div><div className='min-w-0 flex-1'><p className='truncate text-sm font-semibold'>{item.name}</p><p className='text-xs text-muted-foreground'>Доступно: {item.available_packs} уп. · порог {item.reorder_level}</p></div><div className='text-right'><Badge variant='outline' className='border-amber-500/30 text-amber-600'>{item.days_on_hand == null ? 'Нет спроса' : `${item.days_on_hand} дн.`}</Badge><p className='mt-1 text-xs text-muted-foreground'>{money(item.stock_value)}</p></div></div>)}</div>}
            <Button variant='outline' className='mt-4 w-full' asChild><Link to='/procurement'>Открыть закупки<ArrowUpRight className='ml-2 size-4'/></Link></Button>
          </div>
        </section>
        <p className='text-center text-xs text-muted-foreground'>Метрики отображают данные API на момент последнего обновления. Пустые значения не заменяются вымышленными показателями.</p>
      </div>
    </Main>
  </>
}

function RingMetric({ progress, color, track, value, icon, size = 88 }: { progress: number; color: string; track: string; value: string; icon: ReactNode; size?: number }) {
  const radius = 34
  const circumference = 2 * Math.PI * radius
  const safeProgress = Math.max(0, Math.min(100, progress))
  return <div className='relative shrink-0' style={{ width: size, height: size }} aria-label={`Показатель ${value}`}>
    <svg viewBox='0 0 88 88' className='size-full -rotate-90' role='img' aria-hidden='true'><circle cx='44' cy='44' r={radius} fill='none' stroke={track} strokeWidth='7'/><circle cx='44' cy='44' r={radius} fill='none' stroke={color} strokeWidth='7' strokeLinecap='round' strokeDasharray={circumference} strokeDashoffset={circumference * (1 - safeProgress / 100)} style={{transition:'stroke-dashoffset 500ms ease'}}/></svg>
    <div className='absolute inset-0 flex items-center justify-center' style={{color}}>{icon}</div>
  </div>
}
function EmptyState({ text }: { text: string }) { return <div className='rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground'>{text}</div> }

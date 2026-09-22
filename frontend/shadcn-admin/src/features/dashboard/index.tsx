import { useEffect, useState } from 'react'
import { Activity, ArrowUpRight, CircleDollarSign, PackageCheck, Pill, Users } from 'lucide-react'
import { apiFetch } from '@/lib/api-client'
import { ConfigDrawer } from '@/components/config-drawer'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'

export function Dashboard() {
  const [stats, setStats] = useState<PatientStatistics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<PatientStatistics>('/api/v1/patients/statistics').then(setStats).finally(() => setLoading(false))
  }, [])

  const loyalty = stats ? Object.entries(stats.by_loyalty_tier).filter(([tier]) => tier.toLowerCase() !== 'standard').reduce((sum, [, count]) => sum + count, 0) : 0
  const countries = stats ? Object.keys(stats.by_country).length : 0

  return (
    <>
      <Header>
        <Search />
        <ThemeSwitch />
        <ConfigDrawer />
        <ProfileDropdown />
      </Header>
      <Main>
        <div className='mb-6'>
          <p className='text-xs font-semibold uppercase tracking-[0.18em] text-primary'>Pharmacy operations</p>
          <h1 className='mt-1 text-2xl font-bold tracking-tight'>Dashboard</h1>
          <p className='mt-1 text-sm text-muted-foreground'>A live overview of patients, revenue, prescriptions and pharmacy activity.</p>
        </div>

        {loading ? <div className='rounded-2xl border p-6 text-sm text-muted-foreground'>Loading pharmacy intelligence...</div> : (
          <div className='space-y-7'>
            <div className='grid gap-4 lg:grid-cols-3'>
              <HeroCard icon={CircleDollarSign} title='Revenue' value={formatCurrency(stats?.total_purchase_value ?? 0)} detail='Recorded patient purchase value' />
              <HeroCard icon={Users} title='Patients' value={(stats?.total ?? 0).toLocaleString()} detail={(stats?.active ?? 0).toLocaleString() + ' active profiles'} />
              <HeroCard icon={Pill} title='Loyalty & care' value={loyalty.toLocaleString()} detail='Patients in loyalty tiers' />
            </div>

            <div>
              <div className='mb-4 flex items-center justify-between'>
                <div><h2 className='font-semibold'>Operational metrics</h2><p className='text-xs text-muted-foreground'>Live indicators from the pharmacy database.</p></div>
                <Activity className='size-5 text-primary' />
              </div>
              <div className='grid gap-5 sm:grid-cols-2 xl:grid-cols-5'>
                <CircleMetric icon={Users} label='Active patients' value={stats?.active ?? 0} percent={stats?.total ? Math.round((stats.active / stats.total) * 100) : 0} />
                <CircleMetric icon={PackageCheck} label='Inactive' value={stats?.inactive ?? 0} percent={stats?.total ? Math.round((stats.inactive / stats.total) * 100) : 0} />
                <CircleMetric icon={Pill} label='Bonus points' value={stats?.total_loyalty_points ?? 0} percent={Math.min(100, Math.round((stats?.total_loyalty_points ?? 0) / Math.max(stats?.total ?? 1, 1)))} />
                <CircleMetric icon={ArrowUpRight} label='Loyalty members' value={loyalty} percent={stats?.total ? Math.round((loyalty / stats.total) * 100) : 0} />
                <CircleMetric icon={Activity} label='Countries' value={countries} percent={Math.min(100, countries * 10)} />
              </div>
            </div>

            <div className='grid gap-6 xl:grid-cols-[1.35fr_1fr]'>
              <section className='rounded-2xl border bg-card p-5 shadow-sm'>
                <div className='mb-5'><h2 className='font-semibold'>Pharmacy pipelines</h2><p className='text-xs text-muted-foreground'>Color-coded operational stages for quick scanning.</p></div>
                <div className='grid gap-3 sm:grid-cols-2'>
                  <Pipeline title='Patient care' stages={['Registered', 'Active', 'Follow-up']} tones={['blue','green','cyan']} />
                  <Pipeline title='Prescription flow' stages={['Received', 'Processing', 'Ready']} tones={['violet','amber','green']} />
                  <Pipeline title='Inventory' stages={['Healthy', 'Low stock', 'Critical']} tones={['green','amber','red']} />
                  <Pipeline title='Orders' stages={['Pending', 'Processing', 'Completed']} tones={['blue','orange','green']} />
                </div>
              </section>

              <section className='rounded-2xl border bg-card p-5 shadow-sm'>
                <div className='mb-5'><h2 className='font-semibold'>Patient distribution</h2><p className='text-xs text-muted-foreground'>Top countries in the live patient database.</p></div>
                <div className='space-y-3'>
                  {Object.entries(stats?.by_country ?? {}).sort((a,b) => b[1]-a[1]).slice(0,6).map(([country,count]) => (
                    <div key={country}><div className='mb-1 flex justify-between text-sm'><span className='font-medium text-foreground'>{country}</span><span className='text-muted-foreground'>{count}</span></div><div className='h-2 overflow-hidden rounded-full bg-muted'><div className='h-full rounded-full bg-primary' style={{width: Math.min(100, count / Math.max(stats?.total ?? 1, 1) * 100) + '%'}} /></div></div>
                  ))}
                  {!Object.keys(stats?.by_country ?? {}).length && <p className='text-sm text-muted-foreground'>No geographic data recorded.</p>}
                </div>
              </section>
            </div>
          </div>
        )}
      </Main>
    </>
  )
}

type PatientStatistics = { total:number; active:number; inactive:number; total_purchase_value:number; total_loyalty_points:number; by_loyalty_tier:Record<string,number>; by_country:Record<string,number> }

function formatCurrency(value:number) { return new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(value) }

function HeroCard({icon:Icon,title,value,detail}:{icon:typeof CircleDollarSign;title:string;value:string;detail:string}) {
  return <div className='group rounded-2xl border bg-card p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md'><div className='flex items-start justify-between'><div className='flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary'><Icon className='size-5'/></div><ArrowUpRight className='size-4 text-muted-foreground transition group-hover:text-primary'/></div><p className='mt-6 text-sm font-medium text-muted-foreground'>{title}</p><p className='mt-1 text-3xl font-bold tracking-tight text-foreground'>{value}</p><p className='mt-1 text-xs text-muted-foreground'>{detail}</p></div>
}

function CircleMetric({icon:Icon,label,value,percent}:{icon:typeof Users;label:string;value:number;percent:number}) {
  const safe=Math.max(0,Math.min(100,percent))
  return <div className='flex items-center gap-4 rounded-2xl border bg-card p-4 shadow-sm'><div className='relative flex size-16 shrink-0 items-center justify-center rounded-full' style={{background:'conic-gradient(var(--primary) '+safe+'%, hsl(var(--muted)) 0)'}}><div className='flex size-12 items-center justify-center rounded-full bg-card'><Icon className='size-5 text-primary'/></div></div><div className='min-w-0'><p className='text-xs text-muted-foreground'>{label}</p><p className='text-xl font-bold'>{value.toLocaleString()}</p><p className='text-[11px] text-primary'>{safe}% indicator</p></div></div>
}

type Tone='blue'|'green'|'cyan'|'violet'|'amber'|'red'|'orange'
function Pipeline({title,stages,tones}:{title:string;stages:string[];tones:Tone[]}) {
  const colors:Record<Tone,string>={blue:'bg-sky-500',green:'bg-emerald-500',cyan:'bg-cyan-500',violet:'bg-violet-500',amber:'bg-amber-500',red:'bg-red-500',orange:'bg-orange-500'}
  return <div className='rounded-xl border bg-muted/20 p-4'><p className='mb-3 text-sm font-semibold'>{title}</p><div className='space-y-2'>{stages.map((stage,i)=><div key={stage} className='flex items-center gap-2 text-xs'><span className={'size-2.5 rounded-full '+colors[tones[i]]}/><span className='text-foreground'>{stage}</span><span className='ms-auto text-muted-foreground'>{i+1}</span></div>)}</div></div>
}

import { useEffect, useMemo, useState } from 'react'
import { Activity, Bot, CircleDollarSign, Globe2, Loader2, PackageCheck, Pill, RotateCcw, Users } from 'lucide-react'
import { createFileRoute } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { apiFetch } from '@/lib/api-client'

export const Route=createFileRoute('/_authenticated/mortarium-ai')({component:MortariumAI})

const languageCodes=['af','am','ar','az','be','bg','bn','bs','ca','cs','cy','da','de','el','en','es','et','eu','fa','fi','fil','fr','ga','gl','gu','he','hi','hr','hu','hy','id','is','it','ja','ka','kk','km','kn','ko','ky','lo','lt','lv','mk','ml','mn','mr','ms','mt','my','ne','nl','no','pa','pl','pt','ro','ru','sk','sl','so','sq','sr','sv','sw','ta','te','tg','th','tk','tr','uk','ur','uz','vi','zh','zu']
const fallbackNames:Record<string,string>={en:'English',ru:'Русский',uk:'Українська'}

function languageName(code:string){try{return new Intl.DisplayNames(['en'],{type:'language'}).of(code)??fallbackNames[code]??code}catch{return fallbackNames[code]??code}}

function MortariumAI(){
 const [language,setLanguage]=useState(()=>localStorage.getItem('pharmaviyum-ai-language')||'en')
 const [pharmacyId,setPharmacyId]=useState<number>(); const [query,setQuery]=useState(''); const [answer,setAnswer]=useState(''); const [loading,setLoading]=useState(false)
 useEffect(()=>{localStorage.setItem('pharmaviyum-ai-language',language)},[language])
 useEffect(()=>{apiFetch<{pharmacies:{id:number}[]}>('/api/v1/ai/context').then(({pharmacies})=>setPharmacyId(pharmacies[0]?.id)).catch(()=>undefined)},[])
 async function ask(text:string){if(!text.trim()||!pharmacyId||loading)return;setLoading(true);setQuery('');try{const result=await apiFetch<{answer:string}>('/api/v1/ai/query',{method:'POST',body:JSON.stringify({query:text.trim(),pharmacy_id:pharmacyId,language,country:'VN'})});setAnswer(result.answer)}catch(error){setAnswer(error instanceof Error?error.message:'AI processing failed')}finally{setLoading(false)}}
 const languages=useMemo(()=>languageCodes.map(code=>({code,name:languageName(code)})).sort((a,b)=>a.name.localeCompare(b.name,'en')) ,[])
 const currentName=languageName(language)
 return <div className='min-h-full space-y-6 p-6'>
  <header className='flex flex-wrap items-start justify-between gap-4'>
   <div><div className='flex items-center gap-3'><div className='flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary'><Bot className='size-6'/></div><div><p className='text-xs font-semibold uppercase tracking-[0.18em] text-primary'>Pharmacy Intelligence</p><h1 className='text-2xl font-bold tracking-tight text-foreground'>Mortarium AI</h1></div></div><p className='mt-3 max-w-2xl text-sm text-muted-foreground'>AI intelligence for patients, sales, inventory, prescriptions, forecasts and pharmacy operations.</p></div>
   <div className='flex items-center gap-2'>
    <DropdownMenu><DropdownMenuTrigger asChild><Button variant='outline' className='gap-2 rounded-xl'><Globe2 className='size-4 text-primary'/><span className='font-semibold'>{language.toUpperCase()}</span><span className='text-muted-foreground'>· {currentName}</span></Button></DropdownMenuTrigger><DropdownMenuContent align='end' className='max-h-[420px] w-64 overflow-y-auto'>{languages.map(({code,name})=><DropdownMenuItem key={code} onClick={()=>setLanguage(code)} className={language===code?'bg-primary/10 text-primary':''}><span className='w-8 font-semibold'>{code.toUpperCase()}</span><span>{name}</span></DropdownMenuItem>)}</DropdownMenuContent></DropdownMenu>
    <Button variant='outline' className='gap-2 rounded-xl' onClick={()=>{setAnswer('');setQuery('')}}><RotateCcw className='size-4'/>New conversation</Button>
   </div>
  </header>

  <div className='grid gap-4 sm:grid-cols-2 xl:grid-cols-5'>
   <AiMetric icon={Users} label='Patient insights' value='Live' />
   <AiMetric icon={CircleDollarSign} label='Sales intelligence' value='Ready' />
   <AiMetric icon={PackageCheck} label='Inventory intelligence' value='Live' />
   <AiMetric icon={Pill} label='Prescription analysis' value='Ready' />
   <AiMetric icon={Activity} label='Forecasting' value='AI' />
  </div>

  <div className='grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]'>
   <section className='rounded-2xl border bg-card p-6 shadow-sm'><div className='flex min-h-[390px] flex-col items-center justify-center text-center'><div className='mb-5 flex size-16 items-center justify-center rounded-2xl bg-primary/10 text-primary'><Bot className='size-8'/></div><h2 className='text-xl font-semibold'>{answer?'Mortarium response':'How can Mortarium help?'}</h2><p className='mt-2 max-w-lg whitespace-pre-wrap text-sm text-muted-foreground'>{answer||'Ask natural-language questions using the pharmacy CRM context.'}</p><div className='mt-6 w-full max-w-2xl'><div className='mb-3 flex gap-2'><input value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Enter')void ask(query)}} placeholder='Ask Mortarium AI…' className='flex-1 rounded-xl border bg-background px-3 py-2.5 text-sm'/><Button className='rounded-xl' onClick={()=>void ask(query)} disabled={!pharmacyId||loading||!query.trim()}>{loading?<Loader2 className='size-4 animate-spin'/>:'Ask'}</Button></div><div className='grid gap-2 sm:grid-cols-2'>{['What products are below reorder level?','Show this month’s revenue trend','Which batches expire within 30 days?','Analyze patient purchase activity'].map(prompt=><button key={prompt} type='button' onClick={()=>void ask(prompt)} className='rounded-xl border p-3 text-left text-sm transition hover:border-primary/40 hover:bg-primary/5'>{prompt}</button>)}</div></div></div></section>
   <aside className='rounded-2xl border bg-card p-5 shadow-sm'><p className='text-xs font-semibold uppercase tracking-[0.16em] text-primary'>AI workspace</p><h2 className='mt-1 font-semibold'>Intelligence modules</h2><div className='mt-4 space-y-2'>{['Overview','Patients Analytics','Sales & Revenue','Inventory Intelligence','Prescriptions','Forecasting','Reports','Conversations'].map((item,index)=><div key={item} className='flex items-center gap-3 rounded-xl border p-3'><span className='flex size-7 items-center justify-center rounded-lg bg-primary/10 text-xs font-bold text-primary'>{index+1}</span><span className='text-sm font-medium text-foreground'>{item}</span></div>)}</div></aside>
  </div>
 </div>
}

function AiMetric({icon:Icon,label,value}:{icon:typeof Users;label:string;value:string}){return <div className='rounded-2xl border bg-card p-4 shadow-sm'><div className='flex size-9 items-center justify-center rounded-xl bg-primary/10 text-primary'><Icon className='size-4'/></div><p className='mt-4 text-xs text-muted-foreground'>{label}</p><p className='mt-1 font-semibold text-foreground'>{value}</p></div>}

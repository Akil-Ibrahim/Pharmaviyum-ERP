import { useEffect, useMemo, useState } from 'react'
import { Activity, CircleCheck, CircleDot, RefreshCw, Search } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { apiFetch } from '@/lib/api-client'

type EntityPageProps={title:string;description:string;endpoint?:string;columns?:string[];status?:string}
type Row=Record<string,unknown>
const STATUS_COLORS:Record<string,string>={active:'bg-green-500/15 text-green-700 dark:text-green-300',completed:'bg-green-500/15 text-green-700 dark:text-green-300',success:'bg-green-500/15 text-green-700 dark:text-green-300',pending:'bg-amber-500/15 text-amber-700 dark:text-amber-300',processing:'bg-blue-500/15 text-blue-700 dark:text-blue-300',cancelled:'bg-red-500/15 text-red-700 dark:text-red-300',failed:'bg-red-500/15 text-red-700 dark:text-red-300',inactive:'bg-muted text-muted-foreground'}

export function EntityPage({title,description,endpoint,columns=[],status}:EntityPageProps){
 const [rows,setRows]=useState<Row[]>([]),[loading,setLoading]=useState(Boolean(endpoint)),[error,setError]=useState<string|null>(null),[query,setQuery]=useState('')
 const load=()=>{if(!endpoint)return;setLoading(true);setError(null);apiFetch<Row[]>(endpoint).then(setRows).catch((err:unknown)=>setError(err instanceof Error?err.message:'Unable to load data')).finally(()=>setLoading(false))}
 useEffect(()=>{load()},[endpoint])
 const visibleColumns=columns.length?columns:(rows[0]?Object.keys(rows[0]).slice(0,6):[])
 const filteredRows=useMemo(()=>{const q=query.trim().toLowerCase();return q?rows.filter(row=>Object.values(row).some(v=>formatValue(v).toLowerCase().includes(q))):rows},[rows,query])
 const statusCounts=useMemo(()=>{const result:Record<string,number>={};rows.forEach(row=>{const value=row.status??row.is_active;if(value!==undefined&&value!==null){const key=typeof value==='boolean'?(value?'active':'inactive'):String(value).toLowerCase();result[key]=(result[key]??0)+1}});return result},[rows])
 const statusEntries=Object.entries(statusCounts).slice(0,3)
 return <div className='space-y-6 p-6'>
   <div className='flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between'><div><p className='text-xs font-semibold uppercase tracking-[0.18em] text-primary'>Pharmaviyum entity</p><h1 className='mt-1 text-2xl font-bold tracking-tight text-foreground'>{title}</h1><p className='mt-1 text-sm text-muted-foreground'>{description}</p></div>{endpoint&&<Button variant='outline' size='sm' onClick={load} disabled={loading}><RefreshCw className='mr-2 size-4'/>Refresh</Button>}</div>
   {status&&<Badge variant='secondary'>{status}</Badge>}
   {rows.length>0&&<div className='grid gap-4 sm:grid-cols-2 lg:grid-cols-4'><Metric label='Total records' value={rows.length} icon={Activity} percent={100}/>{statusEntries.map(([key,value],i)=><Metric key={key} label={formatLabel(key)} value={value} icon={i===0?CircleCheck:CircleDot} percent={Math.round(value/Math.max(rows.length,1)*100)}/>)}</div>}
   <Card className='overflow-hidden shadow-sm'><CardHeader className='border-b bg-card'><div className='flex items-center justify-between gap-3'><CardTitle className='text-foreground'>{title} records</CardTitle>{rows.length>0&&<span className='text-xs text-muted-foreground'>{filteredRows.length} of {rows.length}</span>}</div>{rows.length>0&&<div className='relative max-w-sm'><Search className='absolute left-2.5 top-2.5 size-4 text-muted-foreground'/><Input value={query} onChange={e=>setQuery(e.target.value)} placeholder={'Search '+title.toLowerCase()+'...'} className='pl-9'/></div>}</CardHeader><CardContent className='p-0'>
   {loading&&<p className='p-5 text-sm text-muted-foreground'>Loading {title.toLowerCase()}...</p>}{error&&<p className='p-5 text-sm text-destructive'>{error}</p>}{!loading&&!error&&rows.length===0&&<p className='p-5 text-sm text-muted-foreground'>No records found.</p>}
   {!loading&&!error&&filteredRows.length>0&&<div className='overflow-x-auto'><table className='w-full text-sm'><thead><tr className='border-b bg-muted/40 text-left'>{visibleColumns.map(column=><th key={column} className='whitespace-nowrap p-3 font-medium text-foreground'>{formatLabel(column)}</th>)}</tr></thead><tbody>{filteredRows.map((row,index)=><tr key={String(row.id??index)} className='border-b last:border-0 hover:bg-muted/30'>{visibleColumns.map(column=><td key={column} className='max-w-[280px] p-3 align-top text-foreground'>{formatCell(row[column],column)}</td>)}</tr>)}</tbody></table></div>}
   {!loading&&!error&&rows.length>0&&filteredRows.length===0&&<p className='p-5 text-sm text-muted-foreground'>No records match your search.</p>}{!endpoint&&<p className='p-5 text-xs text-muted-foreground'>API endpoint is not yet exposed for this entity.</p>}
   </CardContent></Card>
 </div>
}

function Metric({label,value,icon:Icon,percent}:{label:string;value:number;icon:typeof Activity;percent:number}){
 const safe=Math.max(0,Math.min(100,percent))
 return <Card className='rounded-2xl'><CardContent className='flex items-center gap-4 p-4'><div className='relative flex size-14 shrink-0 items-center justify-center rounded-full' style={{background:'conic-gradient(var(--primary) '+safe+'%, hsl(var(--muted)) 0)'}}><div className='flex size-10 items-center justify-center rounded-full bg-card'><Icon className='size-4 text-primary'/></div></div><div><p className='text-xs text-muted-foreground'>{label}</p><p className='text-2xl font-bold text-foreground'>{value.toLocaleString()}</p></div></CardContent></Card>
}
function formatLabel(value:string){return value.replace(/_/g,' ').replace(/\b\w/g,char=>char.toUpperCase())}
function formatCell(value:unknown,column:string){if(value===null||value===undefined||value==='')return '—';if(column==='status'||column==='is_active'){const key=typeof value==='boolean'?(value?'active':'inactive'):String(value).toLowerCase();return <Badge variant='outline' className={STATUS_COLORS[key]??''}>{formatLabel(key)}</Badge>}return formatValue(value)}
function formatValue(value:unknown){if(value===null||value===undefined||value==='')return '—';if(typeof value==='object')return JSON.stringify(value);return String(value)}

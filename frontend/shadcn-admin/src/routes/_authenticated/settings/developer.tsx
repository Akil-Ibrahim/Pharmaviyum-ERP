import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_authenticated/settings/developer')({
  component: DeveloperToolsPage,
})

function DeveloperToolsPage() {
  return (
    <div className='p-6'>
      <div className='rounded-2xl border bg-card p-6 shadow-sm'>
        <h1 className='text-2xl font-bold tracking-tight'>Developer Tools</h1>
        <p className='mt-2 text-sm text-muted-foreground'>Technical settings and developer diagnostics for the Pharmaviyum frontend.</p>
        <div className='mt-6 rounded-xl border border-dashed p-6 text-sm text-muted-foreground'>
          Frontend workspace placeholder. Business data and backend actions will be connected in the next implementation phase.
        </div>
      </div>
    </div>
  )
}

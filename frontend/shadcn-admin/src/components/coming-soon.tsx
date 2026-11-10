import { Telescope } from 'lucide-react'

export function ComingSoon() {
  return (
    <div
      className='flex w-full items-center justify-center px-4 py-8 md:min-h-svh'
      style={{ minHeight: 'calc(100svh - 3.5rem)' }}
    >
      <div className='flex w-full flex-col items-center justify-center gap-2'>
        <Telescope size={72} />
        <h1
          className='text-3xl leading-tight font-bold sm:text-4xl'
        >
          Coming Soon!
        </h1>
        <p className='text-center text-muted-foreground'>
          This page has not been created yet. <br />
          Stay tuned though!
        </p>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { Link } from '@tanstack/react-router'
import {
  Activity,
  Bell,
  BookOpen,
  CircleHelp,
  FileText,
  Search as SearchIcon,
  UserRound,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProfileStore } from '@/stores/profile-store'
import { useSearch } from '@/context/search-provider'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type HeaderProps = React.HTMLAttributes<HTMLElement> & {
  fixed?: boolean
  ref?: React.Ref<HTMLElement>
}

const documentationUrl =
  'https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/blob/main/docs/README.md'
const setupGuideUrl =
  'https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/blob/main/docs/guides/ENVIRONMENT_SETUP.md'
const operationsGuideUrl =
  'https://github.com/Akil-Ibrahim/Pharmaviyum-ERP/blob/main/docs/operations/INCIDENT_RUNBOOK.md'

export function Header({ className, fixed, children, ...props }: HeaderProps) {
  const [offset, setOffset] = useState(0)
  const profile = useProfileStore((state) => state.profile)
  const { setOpen: setSearchOpen } = useSearch()
  const fullName = [profile.firstName, profile.lastName].filter(Boolean).join(' ')
  const initials = [profile.firstName, profile.lastName]
    .filter(Boolean)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'IA'

  useEffect(() => {
    const onScroll = () => {
      setOffset(document.body.scrollTop || document.documentElement.scrollTop)
    }
    document.addEventListener('scroll', onScroll, { passive: true })
    return () => document.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      className={cn(
        'z-50 h-16',
        fixed && 'header-fixed peer/header sticky top-0 w-[inherit]',
        offset > 10 && fixed ? 'shadow' : 'shadow-none',
        className
      )}
      {...props}
    >
      <div
        className={cn(
          'relative flex h-full items-center gap-3 p-4 sm:gap-4',
          offset > 10 &&
            fixed &&
            'after:absolute after:inset-0 after:-z-10 after:bg-background/20 after:backdrop-blur-lg'
        )}
      >
        {children}
        <div className='ms-auto flex min-w-0 items-center gap-1 sm:gap-2'>
          <Button
            type='button'
            variant='ghost'
            size='icon'
            aria-label='Search'
            title='Search'
            onClick={() => setSearchOpen(true)}
          >
            <SearchIcon className='size-4' />
          </Button>
          <Popover>
            <PopoverTrigger asChild>
              <Button
                type='button'
                variant='ghost'
                size='icon'
                aria-label='Notifications'
                title='Notifications'
              >
                <Bell className='size-4' />
              </Button>
            </PopoverTrigger>
            <PopoverContent align='end' className='w-80'>
              <div className='space-y-1'>
                <p className='text-sm font-medium'>Notifications</p>
                <p className='text-xs text-muted-foreground'>
                  You’re all caught up. New notifications will appear here.
                </p>
              </div>
              <Separator className='my-3' />
              <div className='flex flex-col items-center gap-2 py-6 text-center'>
                <span className='flex size-10 items-center justify-center rounded-full bg-muted'>
                  <Bell className='size-5 text-muted-foreground' />
                </span>
                <p className='text-sm font-medium'>No notifications yet</p>
                <p className='max-w-56 text-xs text-muted-foreground'>
                  There are no new notifications to show.
                </p>
              </div>
            </PopoverContent>
          </Popover>
          <Button asChild variant='ghost' size='icon'>
            <Link
              to='/system-status'
              aria-label='System Status'
              title='System Status'
            >
              <Activity className='size-4' />
            </Link>
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type='button'
                variant='ghost'
                size='icon'
                aria-label='Help'
                title='Help'
              >
                <CircleHelp className='size-4' />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end' className='w-60'>
              <DropdownMenuLabel>Help & Documentation</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <a href={documentationUrl} target='_blank' rel='noreferrer'>
                  <BookOpen />
                  Documentation
                </a>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <a href={setupGuideUrl} target='_blank' rel='noreferrer'>
                  <FileText />
                  Setup & deployment guide
                </a>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <a href={operationsGuideUrl} target='_blank' rel='noreferrer'>
                  <Activity />
                  Operations runbook
                </a>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Separator orientation='vertical' className='mx-1 h-6' />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type='button'
                aria-label='Open profile menu'
                className='flex max-w-full items-center gap-2 rounded-md p-1.5 text-start outline-none transition-colors hover:bg-accent focus-visible:ring-2 focus-visible:ring-ring'
              >
                <Avatar className='size-9 shrink-0'>
                  <AvatarImage src={profile.avatar || undefined} alt={fullName} />
                  <AvatarFallback className='bg-primary/10 text-xs font-semibold text-primary'>
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <span className='hidden min-w-0 sm:grid'>
                  <span className='truncate text-sm font-medium leading-5'>{fullName}</span>
                </span>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end' className='w-56'>
              <div className='flex items-center gap-2 px-2 py-2'>
                <Avatar className='size-9 shrink-0'>
                  <AvatarImage src={profile.avatar || undefined} alt={fullName} />
                  <AvatarFallback className='bg-primary/10 text-xs font-semibold text-primary'>
                    {initials}
                  </AvatarFallback>
                </Avatar>
                <div className='grid min-w-0'>
                  <span className='truncate text-sm font-medium'>{fullName}</span>
                </div>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to='/settings'>
                  <UserRound />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link to='/settings/appearance'>
                  <Settings />
                  Settings
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}

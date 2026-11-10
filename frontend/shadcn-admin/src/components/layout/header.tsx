import { useEffect, useState } from 'react'
import { Link } from '@tanstack/react-router'
import { UserRound, Settings } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProfileStore } from '@/stores/profile-store'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

type HeaderProps = React.HTMLAttributes<HTMLElement> & {
  fixed?: boolean
  ref?: React.Ref<HTMLElement>
}

export function Header({ className, fixed, children, ...props }: HeaderProps) {
  const [offset, setOffset] = useState(0)
  const profile = useProfileStore((state) => state.profile)
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
        <div className='ms-auto flex min-w-0 items-center'>
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
                  <span className='truncate text-xs text-muted-foreground leading-4'>
                    {profile.email || 'Profile'}
                  </span>
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
                  <span className='truncate text-xs text-muted-foreground'>
                    {profile.email || ' '}
                  </span>
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

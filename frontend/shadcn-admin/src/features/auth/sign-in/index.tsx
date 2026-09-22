import { Link, useSearch } from '@tanstack/react-router'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { AuthLayout } from '../auth-layout'
import { UserAuthForm } from './components/user-auth-form'

export function SignIn() {
  const { redirect } = useSearch({ from: '/(auth)/sign-in' })

  return (
    <AuthLayout>
      <div className='w-full max-w-sm'>
        <div className='mb-6 overflow-hidden rounded-xl border bg-card shadow-sm'>
          <img
            src='https://raw.githubusercontent.com/ibrahimengpy/Pharmaviyum-CRM/main/assets/pharmaviyum.png'
            alt='Pharmaviyum CRM'
            className='h-auto w-full object-cover'
          />
        </div>

        <Card className='gap-4'>
          <CardHeader>
            <CardTitle className='text-lg tracking-tight'>Sign in</CardTitle>
            <CardDescription>
              Enter your login and password below to access Pharmaviyum CRM.
              <br className='max-sm:hidden' /> Don't have an account?{' '}
              <Link
                to='/sign-up'
                className='text-nowrap underline underline-offset-4 hover:text-primary'
              >
                Sign Up
              </Link>
            </CardDescription>
          </CardHeader>
          <CardContent>
            <UserAuthForm redirectTo={redirect} />
          </CardContent>
          <CardFooter>
            <p className='px-8 text-center text-sm text-muted-foreground'>
              By clicking sign in, you agree to our{' '}
              <a
                href='/terms'
                className='underline underline-offset-4 hover:text-primary'
              >
                Terms of Service
              </a>{' '}
              and{' '}
              <a
                href='/privacy'
                className='underline underline-offset-4 hover:text-primary'
              >
                Privacy Policy
              </a>
              .
            </p>
          </CardFooter>
        </Card>
      </div>
    </AuthLayout>
  )
}

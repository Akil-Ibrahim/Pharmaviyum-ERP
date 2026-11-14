import { useState } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Link, useNavigate } from '@tanstack/react-router'
import { Loader2, KeyRound } from 'lucide-react'
import { toast } from 'sonner'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { PasswordInput } from '@/components/password-input'
import { AuthLayout } from '../auth-layout'

const formSchema = z
  .object({
    newPassword: z.string().min(8, 'Password must be at least 8 characters.'),
    confirmPassword: z.string().min(8, 'Please confirm your password.'),
  })
  .refine((values) => values.newPassword === values.confirmPassword, {
    message: 'Passwords do not match.',
    path: ['confirmPassword'],
  })

type ResetPasswordProps = {
  token?: string
}

export function ResetPassword({ token }: ResetPasswordProps) {
  const [isLoading, setIsLoading] = useState(false)
  const navigate = useNavigate()

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { newPassword: '', confirmPassword: '' },
  })

  async function onSubmit(values: z.infer<typeof formSchema>) {
    if (!token) {
      toast.error('This password setup link is missing or invalid.')
      return
    }

    setIsLoading(true)
    try {
      const apiBaseUrl = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')
      const response = await fetch(`${apiBaseUrl}/api/v1/auth/reset-password/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: values.newPassword }),
      })
      const result = await response.json().catch(() => ({}))

      if (!response.ok) {
        throw new Error(
          typeof result?.detail === 'string'
            ? result.detail
            : `Password reset failed (HTTP ${response.status})`
        )
      }

      form.reset()
      toast.success('Password set successfully. You can now sign in.')
      await navigate({ to: '/sign-in', replace: true })
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Unable to set your password.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <AuthLayout>
      <Card className='mx-auto w-full max-w-sm gap-4'>
        <CardHeader>
          <CardTitle className='flex items-center gap-2 text-lg tracking-tight'>
            <KeyRound className='size-5' />
            Set your password
          </CardTitle>
          <CardDescription>
            Choose a new password for your Pharmaviyum account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!token ? (
            <p className='text-sm text-destructive'>
              This password setup link is missing. Request a new link or contact
              your administrator.
            </p>
          ) : (
            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className='grid gap-3'
              >
                <FormField
                  control={form.control}
                  name='newPassword'
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>New password</FormLabel>
                      <FormControl>
                        <PasswordInput autoComplete='new-password' {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name='confirmPassword'
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Confirm password</FormLabel>
                      <FormControl>
                        <PasswordInput autoComplete='new-password' {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button className='mt-2' disabled={isLoading}>
                  {isLoading ? (
                    <Loader2 className='animate-spin' />
                  ) : (
                    <KeyRound />
                  )}
                  Set password
                </Button>
              </form>
            </Form>
          )}
        </CardContent>
        <CardFooter>
          <p className='mx-auto text-center text-sm text-muted-foreground'>
            <Link
              to='/sign-in'
              className='underline underline-offset-4 hover:text-primary'
            >
              Back to sign in
            </Link>
          </p>
        </CardFooter>
      </Card>
    </AuthLayout>
  )
}

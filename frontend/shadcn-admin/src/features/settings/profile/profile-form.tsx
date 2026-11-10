import { useEffect, useRef, useState } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Camera, Trash2 } from 'lucide-react'
import { showSubmittedData } from '@/lib/show-submitted-data'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { DatePicker } from '@/components/date-picker'
import {
  Avatar,
  AvatarFallback,
  AvatarImage,
} from '@/components/ui/avatar'

const profileFormSchema = z.object({
  firstName: z
    .string()
    .trim()
    .min(2, 'First name must be at least 2 characters.')
    .max(50, 'First name must not be longer than 50 characters.'),
  lastName: z
    .string()
    .trim()
    .min(2, 'Last name must be at least 2 characters.')
    .max(50, 'Last name must not be longer than 50 characters.'),
  dateOfBirth: z.date().optional(),
  email: z.email('Please enter a valid email address.'),
})

type ProfileFormValues = z.infer<typeof profileFormSchema>

const defaultValues: ProfileFormValues = {
  firstName: '',
  lastName: '',
  email: '',
}

const MAX_AVATAR_SIZE = 5 * 1024 * 1024

export function ProfileForm() {
  const [avatarPreview, setAvatarPreview] = useState<string>()
  const [avatarError, setAvatarError] = useState<string>()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues,
    mode: 'onChange',
  })

  useEffect(() => {
    if (!avatarPreview) return
    return () => URL.revokeObjectURL(avatarPreview)
  }, [avatarPreview])

  function handleAvatarChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.type.startsWith('image/')) {
      setAvatarError('Please choose an image file.')
      event.target.value = ''
      return
    }

    if (file.size > MAX_AVATAR_SIZE) {
      setAvatarError('Image must be 5 MB or smaller.')
      event.target.value = ''
      return
    }

    setAvatarError(undefined)
    setAvatarPreview(URL.createObjectURL(file))
  }

  function removeAvatar() {
    setAvatarPreview(undefined)
    setAvatarError(undefined)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <Form {...form}>
      <form
        onSubmit={form.handleSubmit((data) => showSubmittedData(data))}
        className='space-y-8'
      >
        <div className='space-y-4'>
          <div className='space-y-1'>
            <h3 className='text-base font-medium'>Profile photo</h3>
            <p className='text-sm text-muted-foreground'>
              Add a photo so your colleagues can recognize you.
            </p>
          </div>
          <div className='flex flex-wrap items-center gap-4'>
            <Avatar className='size-20'>
              {avatarPreview ? (
                <AvatarImage src={avatarPreview} alt='Profile photo preview' />
              ) : null}
              <AvatarFallback className='text-xl'>
                <Camera className='size-7 text-muted-foreground' />
              </AvatarFallback>
            </Avatar>
            <div className='flex flex-wrap gap-2'>
              <input
                ref={fileInputRef}
                type='file'
                accept='image/*'
                className='sr-only'
                aria-label='Choose profile photo'
                onChange={handleAvatarChange}
              />
              <Button
                type='button'
                variant='outline'
                onClick={() => fileInputRef.current?.click()}
              >
                <Camera className='me-2 size-4' />
                {avatarPreview ? 'Change photo' : 'Upload photo'}
              </Button>
              {avatarPreview ? (
                <Button
                  type='button'
                  variant='ghost'
                  onClick={removeAvatar}
                >
                  <Trash2 className='me-2 size-4' />
                  Remove
                </Button>
              ) : null}
            </div>
          </div>
          <p className='text-xs text-muted-foreground'>
            JPG, PNG or other image formats. Maximum file size: 5 MB.
          </p>
          {avatarError ? (
            <p role='alert' className='text-sm text-destructive'>
              {avatarError}
            </p>
          ) : null}
        </div>

        <div className='space-y-4'>
          <div className='space-y-1'>
            <h3 className='text-base font-medium'>Personal information</h3>
            <p className='text-sm text-muted-foreground'>
              Your name and date of birth.
            </p>
          </div>
          <div className='grid gap-6 sm:grid-cols-2'>
            <FormField
              control={form.control}
              name='firstName'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>First name</FormLabel>
                  <FormControl>
                    <Input placeholder='Your first name' autoComplete='given-name' {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name='lastName'
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Last name</FormLabel>
                  <FormControl>
                    <Input placeholder='Your last name' autoComplete='family-name' {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
          <FormField
            control={form.control}
            name='dateOfBirth'
            render={({ field }) => (
              <FormItem className='flex flex-col sm:max-w-sm'>
                <FormLabel>Date of birth</FormLabel>
                <DatePicker
                  selected={field.value}
                  onSelect={field.onChange}
                />
                <FormDescription>
                  Optional. Your date of birth is only used for your profile.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <div className='space-y-4'>
          <div className='space-y-1'>
            <h3 className='text-base font-medium'>Contact information</h3>
            <p className='text-sm text-muted-foreground'>
              The email address associated with your profile.
            </p>
          </div>
          <FormField
            control={form.control}
            name='email'
            render={({ field }) => (
              <FormItem className='sm:max-w-md'>
                <FormLabel>Email address</FormLabel>
                <FormControl>
                  <Input
                    type='email'
                    placeholder='you@example.com'
                    autoComplete='email'
                    {...field}
                  />
                </FormControl>
                <FormDescription>
                  Email changes may require verification.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        <Button type='submit' disabled={!form.formState.isValid}>
          Save changes
        </Button>
      </form>
    </Form>
  )
}

import { useEffect, useMemo, useRef, useState } from 'react'
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { Camera, Loader2, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { useProfileStore } from '@/stores/profile-store'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
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
  deleteProfileAvatar,
  uploadProfileAvatar,
} from '@/features/settings/profile/api'
import { useProfileAvatar } from '@/features/settings/profile/use-profile-avatar'

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

const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const ALLOWED_AVATAR_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

export function ProfileForm() {
  const profile = useProfileStore((state) => state.profile)
  const setProfile = useProfileStore((state) => state.setProfile)
  const { avatarUrl } = useProfileAvatar()
  const queryClient = useQueryClient()
  const [avatarFile, setAvatarFile] = useState<File | null>(null)
  const [avatarRemoved, setAvatarRemoved] = useState(false)
  const [avatarError, setAvatarError] = useState<string>()
  const [isSaving, setIsSaving] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const localAvatarUrl = useMemo(
    () => (avatarFile ? URL.createObjectURL(avatarFile) : undefined),
    [avatarFile]
  )
  const avatarPreview = avatarRemoved
    ? undefined
    : (localAvatarUrl ?? avatarUrl)

  useEffect(
    () => () => {
      if (localAvatarUrl) URL.revokeObjectURL(localAvatarUrl)
    },
    [localAvatarUrl]
  )

  const form = useForm<ProfileFormValues>({
    resolver: zodResolver(profileFormSchema),
    defaultValues: {
      firstName: profile.firstName || 'Ibrahim',
      lastName: profile.lastName || 'Akil',
      email: profile.email,
      dateOfBirth: profile.dateOfBirth
        ? new Date(`${profile.dateOfBirth}T00:00:00`)
        : undefined,
    },
    mode: 'onChange',
  })

  function handleAvatarChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    if (!ALLOWED_AVATAR_TYPES.has(file.type)) {
      setAvatarError('Choose a JPG, PNG, or WebP image.')
      event.target.value = ''
      return
    }

    if (file.size > MAX_AVATAR_SIZE) {
      setAvatarError('Image must be 2 MB or smaller.')
      event.target.value = ''
      return
    }

    setAvatarError(undefined)
    setAvatarRemoved(false)
    setAvatarFile(file)
  }

  function removeAvatar() {
    setAvatarFile(null)
    setAvatarRemoved(true)
    setAvatarError(undefined)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function onSubmit(data: ProfileFormValues) {
    setIsSaving(true)
    setAvatarError(undefined)

    try {
      setProfile({
        firstName: data.firstName,
        lastName: data.lastName,
        email: data.email,
        dateOfBirth: data.dateOfBirth?.toISOString().slice(0, 10) || '',
      })

      if (avatarFile) {
        await uploadProfileAvatar(avatarFile)
      } else if (avatarRemoved) {
        await deleteProfileAvatar()
      }

      await queryClient.invalidateQueries({ queryKey: ['profile-avatar'] })
      setAvatarFile(null)
      setAvatarRemoved(false)
      toast.success('Profile updated successfully.')
    } catch (error) {
      const message =
        error instanceof Error ? error.message : 'Unable to save profile photo.'
      setAvatarError(message)
      toast.error(message)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className='space-y-8'>
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
                accept='image/jpeg,image/png,image/webp'
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
                <Button type='button' variant='ghost' onClick={removeAvatar}>
                  <Trash2 className='me-2 size-4' />
                  Remove
                </Button>
              ) : null}
            </div>
          </div>
          <p className='text-xs text-muted-foreground'>
            JPG, PNG, or WebP. Maximum file size: 2 MB.
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
                    <Input
                      placeholder='Your first name'
                      autoComplete='given-name'
                      {...field}
                    />
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
                    <Input
                      placeholder='Your last name'
                      autoComplete='family-name'
                      {...field}
                    />
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
                <DatePicker selected={field.value} onSelect={field.onChange} />
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

        <Button type='submit' disabled={!form.formState.isValid || isSaving}>
          {isSaving ? <Loader2 className='size-4 animate-spin' /> : null}
          Save changes
        </Button>
      </form>
    </Form>
  )
}

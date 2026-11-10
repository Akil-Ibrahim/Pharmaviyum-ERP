import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth-store'
import { useProfileStore } from '@/stores/profile-store'
import { fetchProfileAvatar, uploadProfileAvatar } from './api'

const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const ALLOWED_AVATAR_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/webp',
])

async function fetchOrMigrateProfileAvatar(): Promise<Blob | null> {
  const serverAvatar = await fetchProfileAvatar()
  const legacyAvatar = useProfileStore.getState().profile.avatar

  if (serverAvatar) {
    if (legacyAvatar) {
      useProfileStore.getState().setProfile({ avatar: '' })
    }
    return serverAvatar
  }

  if (!legacyAvatar.startsWith('data:image/')) return null

  const legacyResponse = await fetch(legacyAvatar)
  if (!legacyResponse.ok) return null

  const legacyBlob = await legacyResponse.blob()
  if (
    legacyBlob.size > MAX_AVATAR_SIZE ||
    !ALLOWED_AVATAR_TYPES.has(legacyBlob.type)
  ) {
    return null
  }

  await uploadProfileAvatar(
    new File([legacyBlob], 'profile-avatar', { type: legacyBlob.type })
  )
  useProfileStore.getState().setProfile({ avatar: '' })

  return fetchProfileAvatar()
}

export function useProfileAvatar() {
  const accessToken = useAuthStore((state) => state.auth.accessToken)
  const accountNo = useAuthStore((state) => state.auth.user?.accountNo ?? '')
  const legacyAvatar = useProfileStore((state) => state.profile.avatar)

  const query = useQuery({
    queryKey: ['profile-avatar', accountNo],
    queryFn: fetchOrMigrateProfileAvatar,
    enabled: Boolean(accessToken),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  const remoteAvatarUrl = useMemo(
    () => (query.data ? URL.createObjectURL(query.data) : undefined),
    [query.data]
  )

  useEffect(
    () => () => {
      if (remoteAvatarUrl) URL.revokeObjectURL(remoteAvatarUrl)
    },
    [remoteAvatarUrl]
  )

  return {
    avatarUrl: remoteAvatarUrl ?? (legacyAvatar || undefined),
    isLoading: query.isLoading,
  }
}

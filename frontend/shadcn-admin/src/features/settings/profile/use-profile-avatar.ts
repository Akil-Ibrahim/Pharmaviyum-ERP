import { useEffect, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth-store'
import { useProfileStore } from '@/stores/profile-store'
import { fetchProfileAvatar } from './api'
import { migrateLegacyAvatarOnce } from './legacy-avatar-migration'

export function useProfileAvatar() {
  const accessToken = useAuthStore((state) => state.auth.accessToken)
  const accountNo = useAuthStore((state) => state.auth.user?.accountNo ?? '')
  const legacyAvatar = useProfileStore((state) => state.profile.avatar)
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['profile-avatar', accountNo],
    queryFn: fetchProfileAvatar,
    enabled: Boolean(accessToken),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  const migration = useMutation({
    mutationFn: ({
      accountNo,
      legacyAvatar,
    }: {
      accountNo: string
      legacyAvatar: string
    }) => migrateLegacyAvatarOnce(accountNo, legacyAvatar),
    onSuccess: async (migrated, variables) => {
      if (!migrated) return

      useProfileStore.getState().setProfile({ avatar: '' })
      await queryClient.invalidateQueries({
        queryKey: ['profile-avatar', variables.accountNo],
      })
    },
  })

  useEffect(() => {
    if (!query.isSuccess) return

    if (query.data) {
      if (legacyAvatar) {
        useProfileStore.getState().setProfile({ avatar: '' })
      }
      return
    }

    if (legacyAvatar.startsWith('data:image/')) {
      migration.mutate({ accountNo, legacyAvatar })
    }
  }, [accountNo, legacyAvatar, migration.mutate, query.data, query.isSuccess])

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

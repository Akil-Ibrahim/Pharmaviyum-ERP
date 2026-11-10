import { useEffect, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/auth-store'
import { fetchProfileAvatar } from './api'

export function useProfileAvatar() {
  const accessToken = useAuthStore((state) => state.auth.accessToken)
  const accountNo = useAuthStore((state) => state.auth.user?.accountNo ?? '')

  const query = useQuery({
    queryKey: ['profile-avatar', accountNo],
    queryFn: fetchProfileAvatar,
    enabled: Boolean(accessToken),
    staleTime: 5 * 60 * 1000,
    retry: false,
  })

  const avatarUrl = useMemo(
    () => (query.data ? URL.createObjectURL(query.data) : undefined),
    [query.data]
  )

  useEffect(
    () => () => {
      if (avatarUrl) URL.revokeObjectURL(avatarUrl)
    },
    [avatarUrl]
  )

  return { avatarUrl, isLoading: query.isLoading }
}

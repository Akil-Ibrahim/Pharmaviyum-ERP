import { apiFetch, apiFetchBlob } from '@/lib/api-client'

const AVATAR_ENDPOINT = '/users/me/avatar'

export function fetchProfileAvatar(): Promise<Blob | null> {
  return apiFetchBlob(AVATAR_ENDPOINT)
}

export function uploadProfileAvatar(file: File): Promise<void> {
  const formData = new FormData()
  formData.append('file', file)

  return apiFetch<void>(AVATAR_ENDPOINT, {
    method: 'PUT',
    body: formData,
  })
}

export function deleteProfileAvatar(): Promise<void> {
  return apiFetch<void>(AVATAR_ENDPOINT, { method: 'DELETE' })
}

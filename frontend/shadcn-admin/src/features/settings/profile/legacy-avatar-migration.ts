import { uploadProfileAvatar } from './api'

const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const ALLOWED_AVATAR_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp'])

const inFlightMigrations = new Map<string, Promise<boolean>>()

async function migrateLegacyAvatarDataUrl(
  legacyAvatar: string
): Promise<boolean> {
  const response = await fetch(legacyAvatar)
  if (!response.ok) return false

  const blob = await response.blob()
  if (
    blob.size === 0 ||
    blob.size > MAX_AVATAR_SIZE ||
    !ALLOWED_AVATAR_TYPES.has(blob.type)
  ) {
    return false
  }

  await uploadProfileAvatar(
    new File([blob], 'profile-avatar', { type: blob.type })
  )
  return true
}

/**
 * Share an in-flight migration across header/profile consumers.
 * The server PUT endpoint is an upsert, but duplicate uploads are unnecessary.
 */
export function migrateLegacyAvatarOnce(
  accountNo: string,
  legacyAvatar: string
): Promise<boolean> {
  const existing = inFlightMigrations.get(accountNo)
  if (existing) return existing

  const migration = migrateLegacyAvatarDataUrl(legacyAvatar).finally(() => {
    inFlightMigrations.delete(accountNo)
  })
  inFlightMigrations.set(accountNo, migration)
  return migration
}

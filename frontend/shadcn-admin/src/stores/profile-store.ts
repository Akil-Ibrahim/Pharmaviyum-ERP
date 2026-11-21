import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export interface ProfileIdentity {
  firstName: string
  lastName: string
  email: string
  dateOfBirth: string
  avatar: string
}

interface ProfileState {
  profile: ProfileIdentity
  setProfile: (profile: Partial<ProfileIdentity>) => void
}

const defaultProfile: ProfileIdentity = {
  firstName: 'Ibrahim',
  lastName: 'Akil',
  email: '',
  dateOfBirth: '',
  avatar: '',
}

export const useProfileStore = create<ProfileState>()(
  persist(
    (set) => ({
      profile: defaultProfile,
      setProfile: (profile) =>
        set((state) => ({
          profile: { ...state.profile, ...profile },
        })),
    }),
    {
      name: 'pharmaviyum-profile',
      version: 2,
      storage: createJSONStorage(() => localStorage),
      migrate: (persistedState) => {
        const persisted = persistedState as {
          profile?: Partial<ProfileIdentity>
        }
        const legacyProfile = persisted.profile ?? {}

        // Keep the previous local photo until it has been migrated to PostgreSQL.
        return {
          profile: {
            firstName: legacyProfile.firstName ?? defaultProfile.firstName,
            lastName: legacyProfile.lastName ?? defaultProfile.lastName,
            email: legacyProfile.email ?? defaultProfile.email,
            dateOfBirth:
              legacyProfile.dateOfBirth ?? defaultProfile.dateOfBirth,
            avatar: legacyProfile.avatar ?? defaultProfile.avatar,
          },
        }
      },
      partialize: (state) => ({ profile: state.profile }),
    }
  )
)

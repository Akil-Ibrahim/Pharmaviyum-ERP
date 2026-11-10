import { create } from 'zustand'
import { createJSONStorage, persist } from 'zustand/middleware'

export interface ProfileIdentity {
  firstName: string
  lastName: string
  email: string
  dateOfBirth: string
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
          profile?: Partial<ProfileIdentity> & { avatar?: string }
        }
        const legacyProfile = persisted.profile ?? {}

        // Remove the old base64 avatar from persisted browser storage.
        return {
          profile: {
            firstName: legacyProfile.firstName ?? defaultProfile.firstName,
            lastName: legacyProfile.lastName ?? defaultProfile.lastName,
            email: legacyProfile.email ?? defaultProfile.email,
            dateOfBirth: legacyProfile.dateOfBirth ?? defaultProfile.dateOfBirth,
          },
        }
      },
      partialize: (state) => ({ profile: state.profile }),
    }
  )
)

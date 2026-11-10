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

export const useProfileStore = create<ProfileState>()(
  persist(
    (set) => ({
      profile: {
        firstName: 'Ibrahim',
        lastName: 'Akil',
        email: '',
        dateOfBirth: '',
        avatar: '',
      },
      setProfile: (profile) =>
        set((state) => ({
          profile: { ...state.profile, ...profile },
        })),
    }),
    {
      name: 'pharmaviyum-profile',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ profile: state.profile }),
    }
  )
)

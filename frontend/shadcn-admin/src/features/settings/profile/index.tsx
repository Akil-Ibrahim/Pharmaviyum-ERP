import { ContentSection } from '../components/content-section'
import { ProfileForm } from './profile-form'

export function SettingsProfile() {
  return (
    <ContentSection
      title='Profile'
      desc='Manage your personal details, profile photo, and contact email.'
    >
      <ProfileForm />
    </ContentSection>
  )
}

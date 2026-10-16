import { describe, expect, it } from 'vitest'
import { sidebarData } from './sidebar-data'

describe('Pharmaviyum sidebar navigation', () => {
  it('keeps the primary operational items in the agreed order', () => {
    const operations = sidebarData.navGroups.find(
      (group) => group.title === 'Operations'
    )

    expect(operations?.items.map((item) => item.title)).toEqual([
      'POS',
      'Mortarium AI',
      'Dashboard',
      'Drug Reference',
      'Patients',
      'Orders',
      'Prescriptions',
      'Pharmacy',
    ])
  })

  it('groups the seven pharmacy entities under Pharmacy', () => {
    const operations = sidebarData.navGroups.find(
      (group) => group.title === 'Operations'
    )
    const pharmacy = operations?.items.find((item) => item.title === 'Pharmacy')

    expect(pharmacy?.items?.map((item) => item.title)).toEqual([
      'Inventory',
      'Procurement',
      'Transfers',
      'Expiry Control',
      'Batches',
      'Pharmacies',
      'Suppliers',
    ])
  })

  it('groups ERP Overview and Sync Events under ERP Systems', () => {
    const integrations = sidebarData.navGroups.find(
      (group) => group.title === 'Integrations'
    )
    const erpSystems = integrations?.items.find(
      (item) => item.title === 'ERP Systems'
    )

    expect(erpSystems?.items?.map((item) => item.title)).toEqual([
      'ERP Overview',
      'Sync Events',
    ])
  })

  it('keeps Developer Tools under Settings and hides legacy top-level links', () => {
    const administration = sidebarData.navGroups.find(
      (group) => group.title === 'Administration'
    )
    const settings = administration?.items.find(
      (item) => item.title === 'Settings'
    )
    const visibleTitles = sidebarData.navGroups.flatMap((group) =>
      group.items.map((item) => item.title)
    )

    expect(settings?.items?.map((item) => item.title)).toContain(
      'Developer Tools'
    )
    expect(visibleTitles).not.toContain('Products')
    expect(visibleTitles).not.toContain('Pharmacist Workspace')
  })
})

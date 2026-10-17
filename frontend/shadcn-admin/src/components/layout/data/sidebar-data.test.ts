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
    const pharmacy = operations?.items.find(
      (item) => item.title === 'Pharmacy'
    )

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

  it('keeps ERP Systems, Sync Events, and Tasks as separate final navigation items', () => {
    const integrations = sidebarData.navGroups.find(
      (group) => group.title === 'Integrations'
    )

    expect(integrations?.items.map((item) => item.title)).toEqual([
      'ERP Systems',
      'Sync Events',
      'Tasks',
    ])
  })

  it('keeps Developer Tools under Settings and hides legacy sidebar links', () => {
    const administration = sidebarData.navGroups.find(
      (group) => group.title === 'Administration'
    )
    const settings = administration?.items.find(
      (item) => item.title === 'Settings'
    )
    const visibleTitles = sidebarData.navGroups.flatMap((group) =>
      group.items.flatMap((item) => [
        item.title,
        ...(item.items?.map((subItem) => subItem.title) ?? []),
      ])
    )

    expect(settings?.items?.map((item) => item.title)).toContain(
      'Developer Tools'
    )
    expect(sidebarData.user.name).toBe('admin')
    expect(
      sidebarData.navGroups.map((group) => group.title)
    ).toEqual(['Operations', 'Administration', 'Integrations'])
    const integrations = sidebarData.navGroups.find(
      (group) => group.title === 'Integrations'
    )
    expect(integrations?.items.map((item) => item.title)).toEqual([
      'ERP Systems',
      'Tasks',
    ])
    expect(visibleTitles).not.toContain('Products')
    expect(visibleTitles).not.toContain('Pharmacist Workspace')
  })
})

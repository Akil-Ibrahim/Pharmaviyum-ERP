import { describe, expect, it } from 'vitest'
import { sidebarData } from './sidebar-data'

describe('Pharmaviyum sidebar navigation', () => {
  const group = (title: string) =>
    sidebarData.navGroups.find((item) => item.title === title)

  const itemTitles = (title: string) =>
    group(title)?.items.map((item) => item.title)

  it('keeps the compact operational navigation in the agreed order', () => {
    expect(itemTitles('Operations')).toEqual([
      'Dashboard',
      'POS',
      'Mortarium AI',
      'Patients',
      'Prescriptions',
      'Inventory',
      'Procurement',
      'Pharmacies',
    ])
  })

  it('groups inventory capabilities under Inventory', () => {
    const inventory = group('Operations')?.items.find(
      (item) => item.title === 'Inventory'
    )

    expect(inventory?.items?.map((item) => item.title)).toEqual([
      'Drug Catalog',
      'Catalog Review',
      'Stock Overview',
      'Batches',
      'Expiry Management',
      'Transfers',
    ])
  })

  it('groups procurement capabilities under Procurement', () => {
    const procurement = group('Operations')?.items.find(
      (item) => item.title === 'Procurement'
    )

    expect(procurement?.items?.map((item) => item.title)).toEqual([
      'Suppliers',
      'Purchase Orders',
      'Receiving',
    ])
  })

  it('keeps Users and Settings in Administration', () => {
    expect(itemTitles('Administration')).toEqual(['Users', 'Settings'])

    const settings = group('Administration')?.items.find(
      (item) => item.title === 'Settings'
    )

    expect(settings?.items?.map((item) => item.title)).toEqual([
      'Profile',
      'Account',
      'Appearance',
      'Notifications',
      'Developer Tools',
    ])
  })

  it('groups ERP connections and sync history under System integrations', () => {
    expect(itemTitles('System')).toEqual(['Integrations', 'Background Tasks'])

    const integrations = group('System')?.items.find(
      (item) => item.title === 'Integrations'
    )

    expect(integrations?.items?.map((item) => item.title)).toEqual([
      'ERP Connections',
      'Sync History',
    ])
  })

  it('preserves the Mortarium AI destination and removes redundant top-level links', () => {
    const mortarium = group('Operations')?.items.find(
      (item) => item.title === 'Mortarium AI'
    )
    const allTopLevelTitles = sidebarData.navGroups.flatMap((navGroup) =>
      navGroup.items.map((item) => item.title)
    )

    expect(mortarium?.url).toBe('/mortarium-ai')
    expect(allTopLevelTitles).not.toContain('Drug Reference')
    expect(allTopLevelTitles).not.toContain('Catalog Review')
    expect(allTopLevelTitles).not.toContain('Purchase Ledger')
    expect(allTopLevelTitles).not.toContain('Orders')
    expect(sidebarData.navGroups.map((navGroup) => navGroup.title)).toEqual([
      'Operations',
      'Administration',
      'System',
    ])
  })
})

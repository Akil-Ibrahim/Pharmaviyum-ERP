import { describe, expect, it } from 'vitest'
import { sidebarData } from './sidebar-data'

describe('Pharmaviyum sidebar navigation', () => {
  const group = (title: string) =>
    sidebarData.navGroups.find((item) => item.title === title)

  const itemTitles = (title: string) =>
    group(title)?.items.map((item) => item.title)

  it('keeps the compact operational navigation in the agreed order', () => {
    expect(itemTitles('Operations')).toEqual([
      'Dashboard', 'POS', 'Mortarium AI', 'Patients', 'Prescriptions',
      'Inventory', 'Procurement', 'Pharmacies',
    ])
  })

  it('groups inventory capabilities under Inventory', () => {
    const inventory = group('Operations')?.items.find((item) => item.title === 'Inventory')
    expect(inventory?.items?.map((item) => item.title)).toEqual([
      'Drug Catalog', 'Catalog Review', 'Stock Overview', 'Batches',
      'Expiry Management', 'Transfers',
    ])
  })

  it('groups procurement capabilities under Procurement', () => {
    const procurement = group('Operations')?.items.find((item) => item.title === 'Procurement')
    expect(procurement?.items?.map((item) => item.title)).toEqual([
      'Suppliers', 'Purchase Orders', 'Receiving',
    ])
  })

  it('nests System Status and Integrations under Developer Settings', () => {
    expect(itemTitles('Administration')).toEqual(['Users', 'Settings'])
    const settings = group('Administration')?.items.find((item) => item.title === 'Settings')
    expect(settings?.items?.map((item) => item.title)).toEqual([
      'Profile', 'Appearance', 'Notifications', 'Developer Settings',
    ])

    const developer = settings?.items?.find((item) => item.title === 'Developer Settings')
    expect(developer?.url).toBe('/settings/developer')
    expect(developer?.items?.map((item) => item.title)).toEqual([
      'System Status', 'Integrations',
    ])

    const integrations = developer?.items?.find((item) => item.title === 'Integrations')
    expect(integrations?.items?.map((item) => item.title)).toEqual([
      'ERP Connections', 'Sync History',
    ])
    expect(integrations?.items?.map((item) => item.url)).toEqual([
      '/erp-systems', '/sync-events',
    ])
  })

  it('keeps Background Tasks in the System group', () => {
    expect(itemTitles('System')).toEqual(['Background Tasks'])
  })

  it('preserves Mortarium AI and the agreed top-level group order', () => {
    const mortarium = group('Operations')?.items.find((item) => item.title === 'Mortarium AI')
    const allTopLevelTitles = sidebarData.navGroups.flatMap((navGroup) =>
      navGroup.items.map((item) => item.title)
    )
    expect(mortarium?.url).toBe('/mortarium-ai')
    expect(allTopLevelTitles).not.toContain('Drug Reference')
    expect(allTopLevelTitles).not.toContain('Catalog Review')
    expect(allTopLevelTitles).not.toContain('Purchase Ledger')
    expect(allTopLevelTitles).not.toContain('Orders')
    expect(sidebarData.navGroups.map((navGroup) => navGroup.title)).toEqual([
      'Operations', 'Administration', 'System',
    ])
  })
})

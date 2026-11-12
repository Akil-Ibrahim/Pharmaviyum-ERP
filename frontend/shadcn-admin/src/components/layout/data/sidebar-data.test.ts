import { describe, expect, it } from 'vitest'
import { sidebarData } from './sidebar-data'

describe('Pharmaviyum sidebar navigation', () => {
  const group = (title: string) => sidebarData.navGroups.find((item) => item.title === title)
  const itemTitles = (title: string) => group(title)?.items.map((item) => item.title)

  it('keeps the compact operational navigation in the agreed order', () => {
    expect(itemTitles('Operations')).toEqual(['Dashboard', 'POS', 'Mortarium AI', 'Patients', 'Prescriptions', 'Inventory', 'Procurement', 'Pharmacies'])
  })

  it('groups inventory capabilities under Inventory', () => {
    const inventory = group('Operations')?.items.find((item) => item.title === 'Inventory')
    expect(inventory?.items?.map((item) => item.title)).toEqual(['Drug Catalog', 'Catalog Review', 'Stock Overview', 'Batches', 'Expiry Management', 'Transfers'])
  })

  it('groups procurement capabilities under Procurement', () => {
    const procurement = group('Operations')?.items.find((item) => item.title === 'Procurement')
    expect(procurement?.items?.map((item) => item.title)).toEqual(['Suppliers', 'Purchase Orders', 'Receiving'])
  })

  it('exposes Ansible documentation under Developer Settings', () => {
    const settings = group('Administration')?.items.find((item) => item.title === 'Settings')
    const developer = settings?.items?.find((item) => item.title === 'Developer Settings')
    const ansible = developer?.items?.find((item) => item.title === 'Ansible')
    expect(developer?.url).toBe('/settings/developer')
    expect(ansible?.items?.map((item) => item.title)).toEqual(['Documentation'])
    expect(ansible?.items?.[0]?.url).toBe('/settings/developer/ansible')
  })

  it('keeps Background Tasks in the System group', () => {
    expect(itemTitles('System')).toEqual(['Background Tasks'])
  })

  it('preserves Mortarium AI and navigation group order', () => {
    const mortarium = group('Operations')?.items.find((item) => item.title === 'Mortarium AI')
    expect(mortarium?.url).toBe('/mortarium-ai')
    expect(sidebarData.navGroups.map((item) => item.title)).toEqual(['Operations', 'Administration', 'System'])
  })
})

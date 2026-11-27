import { describe, expect, it } from 'vitest'
import { sidebarData } from './sidebar-data'

describe('Pharmaviyum sidebar navigation', () => {
  const group = (title: string) =>
    sidebarData.navGroups.find((item) => item.title === title)

  const item = (groupTitle: string, itemTitle: string) =>
    group(groupTitle)?.items.find((entry) => entry.title === itemTitle)

  const child = (
    groupTitle: string,
    parentTitle: string,
    childTitle: string
  ) =>
    item(groupTitle, parentTitle)?.items?.find(
      (entry) => entry.title === childTitle
    )

  const itemTitles = (title: string) =>
    group(title)?.items.map((entry) => entry.title)

  it('keeps the approved Operations hierarchy and order', () => {
    expect(itemTitles('Operations')).toEqual([
      'Dashboard',
      'POS',
      'Mortarium AI',
      'Clinical Care',
      'Inventory',
      'Procurement',
      'Pharmacies',
    ])
  })

  it('groups patient and prescription workflows under Clinical Care', () => {
    expect(
      item('Operations', 'Clinical Care')?.items?.map((entry) => entry.title)
    ).toEqual(['Patients', 'Prescriptions'])
  })

  it('keeps Inventory focused on its four agreed capabilities', () => {
    expect(
      item('Operations', 'Inventory')?.items?.map((entry) => entry.title)
    ).toEqual([
      'Drug Catalog',
      'Stock Management',
      'Transfers',
      'Defectura',
    ])
  })

  it('provides a dedicated Defectura route', () => {
    expect(child('Operations', 'Inventory', 'Defectura')).toMatchObject({
      title: 'Defectura',
      url: '/defectura',
    })
  })

  it('keeps Catalog Review and stock sub-capabilities out of the sidebar', () => {
    const inventoryTitles =
      item('Operations', 'Inventory')?.items?.map((entry) => entry.title)

    expect(inventoryTitles).not.toContain('Catalog Review')
    expect(inventoryTitles).not.toContain('Stock Overview')
    expect(inventoryTitles).not.toContain('Batches')
    expect(inventoryTitles).not.toContain('Expiry Management')
  })

  it('groups supplier and order workflows under Procurement', () => {
    expect(
      item('Operations', 'Procurement')?.items?.map((entry) => entry.title)
    ).toEqual(['Suppliers', 'Purchase Orders', 'Receiving'])
  })

  it('keeps Administration and System navigation compact', () => {
    expect(itemTitles('Administration')).toEqual(['Users', 'Settings'])
    expect(itemTitles('System')).toEqual(['Background Tasks'])
    expect(sidebarData.navGroups.map((entry) => entry.title)).toEqual([
      'Operations',
      'Administration',
      'System',
    ])
  })

  it('gives every sidebar destination a route and keeps every item enabled', () => {
    for (const navGroup of sidebarData.navGroups) {
      for (const entry of navGroup.items) {
        if (entry.items) {
          for (const childEntry of entry.items) {
            expect(childEntry.url, childEntry.title).toBeTruthy()
            expect(childEntry.disabled, childEntry.title).not.toBe(true)
          }
        } else {
          expect(entry.url, entry.title).toBeTruthy()
          expect(entry.disabled, entry.title).not.toBe(true)
        }
      }
    }
  })

  it('keeps Dashboard and POS as the first two Operations destinations', () => {
    expect(item('Operations', 'Dashboard')?.url).toBe('/')
    expect(item('Operations', 'POS')?.url).toBe('/pos')
  })
})

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

  it('keeps Defectura as one destination without inventing a route', () => {
    const defectura = child('Operations', 'Inventory', 'Defectura')

    expect(defectura).toMatchObject({
      title: 'Defectura',
      disabled: true,
    })
    expect(defectura?.url).toBeUndefined()
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

  it('disables destinations whose routes are not ready', () => {
    const unavailableItems = [
      item('Operations', 'Mortarium AI'),
      child('Operations', 'Clinical Care', 'Patients'),
      child('Operations', 'Clinical Care', 'Prescriptions'),
      child('Operations', 'Inventory', 'Drug Catalog'),
      child('Operations', 'Inventory', 'Stock Management'),
      child('Operations', 'Inventory', 'Transfers'),
      child('Operations', 'Inventory', 'Defectura'),
      child('Operations', 'Procurement', 'Suppliers'),
      child('Operations', 'Procurement', 'Purchase Orders'),
      child('Operations', 'Procurement', 'Receiving'),
      item('Operations', 'Pharmacies'),
    ]

    for (const entry of unavailableItems) {
      expect(entry?.disabled).toBe(true)
      expect(entry?.disabledReason).toBeTruthy()
    }
  })

  it('keeps implemented Dashboard and POS destinations enabled', () => {
    expect(item('Operations', 'Dashboard')?.disabled).toBeUndefined()
    expect(item('Operations', 'POS')?.disabled).toBeUndefined()
  })

  it('keeps available admin and system destinations enabled', () => {
    expect(item('Administration', 'Users')?.disabled).toBeUndefined()
    expect(item('Administration', 'Settings')?.disabled).toBeUndefined()
    expect(item('System', 'Background Tasks')?.disabled).toBeUndefined()
  })
})

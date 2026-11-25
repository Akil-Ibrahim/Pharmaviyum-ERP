import {
  ArrowLeftRight,
  BookOpenCheck,
  Bot,
  Boxes,
  ClipboardList,
  FileText,
  LayoutDashboard,
  ListChecks,
  PackageCheck,
  ReceiptText,
  Settings,
  ShoppingCart,
  Stethoscope,
  Store,
  Truck,
  UserRound,
  UsersRound,
} from 'lucide-react'
import { type SidebarData } from '../types'

const unavailable = 'Page is being prepared.'

export const sidebarData: SidebarData = {
  user: {
    name: 'admin',
    email: 'admin@pharmaviyum.local',
    avatar: '/avatars/shadcn.jpg',
  },
  teams: [
    {
      name: 'Pharmaviyum',
      logo: '/images/pharmaviyum_logo.png',
      plan: 'Pharmacy workflow',
    },
  ],
  navGroups: [
    {
      title: 'Operations',
      items: [
        {
          title: 'Dashboard',
          url: '/',
          icon: LayoutDashboard,
          disabled: true,
          disabledReason: unavailable,
        },
        {
          title: 'POS',
          url: '/pos',
          icon: ReceiptText,
          disabled: true,
          disabledReason: unavailable,
        },
        {
          title: 'Mortarium AI',
          url: '/mortarium-ai',
          icon: Bot,
          disabled: true,
          disabledReason: unavailable,
        },
        {
          title: 'Clinical Care',
          icon: Stethoscope,
          items: [
            {
              title: 'Patients',
              url: '/patients',
              icon: UserRound,
              disabled: true,
              disabledReason: unavailable,
            },
            {
              title: 'Prescriptions',
              url: '/prescriptions',
              icon: FileText,
              disabled: true,
              disabledReason: unavailable,
            },
          ],
        },
        {
          title: 'Inventory',
          icon: Boxes,
          items: [
            {
              title: 'Drug Catalog',
              url: '/drug-reference',
              icon: BookOpenCheck,
              disabled: true,
              disabledReason: unavailable,
            },
            {
              title: 'Stock Management',
              url: '/inventory',
              icon: PackageCheck,
              disabled: true,
              disabledReason: unavailable,
            },
            {
              title: 'Transfers',
              url: '/transfers',
              icon: ArrowLeftRight,
              disabled: true,
              disabledReason: unavailable,
            },
            {
              title: 'Defectura',
              icon: ClipboardList,
              disabled: true,
              disabledReason: unavailable,
            },
          ],
        },
        {
          title: 'Procurement',
          icon: ShoppingCart,
          items: [
            {
              title: 'Suppliers',
              url: '/suppliers',
              icon: Truck,
              disabled: true,
              disabledReason: unavailable,
            },
            {
              title: 'Purchase Orders',
              url: '/orders',
              icon: ClipboardList,
              disabled: true,
              disabledReason: unavailable,
            },
            {
              title: 'Receiving',
              url: '/procurement',
              icon: PackageCheck,
              disabled: true,
              disabledReason: unavailable,
            },
          ],
        },
        {
          title: 'Pharmacies',
          url: '/pharmacies',
          icon: Store,
          disabled: true,
          disabledReason: unavailable,
        },
      ],
    },
    {
      title: 'Administration',
      items: [
        { title: 'Users', url: '/users', icon: UsersRound },
        { title: 'Settings', url: '/settings', icon: Settings },
      ],
    },
    {
      title: 'System',
      items: [{ title: 'Background Tasks', url: '/tasks', icon: ListChecks }],
    },
  ],
}

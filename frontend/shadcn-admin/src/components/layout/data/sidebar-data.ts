import {
  Activity,
  ArrowLeftRight,
  BookOpenCheck,
  Bot,
  Boxes,
  Bug,
  ClipboardList,
  Code2,
  FileText,
  FlaskConical,
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
        },
        {
          title: 'POS',
          url: '/pos',
          icon: ReceiptText,
        },
        {
          title: 'Mortarium AI',
          url: '/mortarium-ai',
          icon: Bot,
        },
        {
          title: 'Clinical Care',
          icon: Stethoscope,
          items: [
            {
              title: 'Patients',
              url: '/patients',
              icon: UserRound,
            },
            {
              title: 'Prescriptions',
              url: '/prescriptions',
              icon: FileText,
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
            },
            {
              title: 'Stock Management',
              url: '/inventory',
              icon: PackageCheck,
            },
            {
              title: 'Transfers',
              url: '/transfers',
              icon: ArrowLeftRight,
            },
            {
              title: 'Defectura',
              url: '/defectura',
              icon: ClipboardList,
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
            },
            {
              title: 'Purchase Orders',
              url: '/orders',
              icon: ClipboardList,
            },
            {
              title: 'Receiving',
              url: '/procurement',
              icon: PackageCheck,
            },
          ],
        },
        {
          title: 'Pharmacies',
          url: '/pharmacies',
          icon: Store,
        },
      ],
    },
    {
      title: 'Developer',
      items: [
        {
          title: 'Developer Overview',
          url: '/developer',
          icon: Code2,
          badge: 'QA',
        },
        {
          title: 'QA Copilot',
          url: '/developer/qa-copilot',
          icon: Bot,
        },
        {
          title: 'Agentic Testing',
          url: '/developer/agentic-testing',
          icon: FlaskConical,
        },
        {
          title: 'QA Intelligence',
          url: '/developer/qa-intelligence',
          icon: Bug,
        },
        {
          title: 'Test Runs & Evidence',
          url: '/developer/test-runs',
          icon: ClipboardList,
        },
        {
          title: 'System & Agent Logs',
          url: '/developer/agent-logs',
          icon: Activity,
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

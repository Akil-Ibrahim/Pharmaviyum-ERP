# Pharmaviyum CRM - Frontend

Modern admin dashboard for pharmacy management, integrated with ERP systems.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- pnpm (recommended)

### Installation

```bash
cd frontend
pnpm install
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration
```

### Development

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

```bash
pnpm build
pnpm start
```

## 📚 Technology Stack

- **Framework**: Next.js 16.2.4
- **UI Library**: React 19.2.4
- **Component System**: Shadcn/UI + Radix UI
- **Styling**: Tailwind CSS 4
- **Database**: Drizzle ORM + PostgreSQL (Neon)
- **Authentication**: Better Auth
- **Form Validation**: React Hook Form + Zod
- **State Management**: Zustand
- **Charts**: Recharts
- **Type Safety**: TypeScript

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                # Next.js App Router
│   ├── components/         # Reusable UI components
│   ├── lib/               # Utilities and helpers
│   ├── contexts/          # React contexts (Auth, Theme, Font)
│   ├── hooks/             # Custom React hooks
│   ├── db/                # Database schemas and queries
│   └── config/            # Configuration files
├── public/                # Static assets
├── scripts/               # Utility scripts (seeding, etc.)
└── package.json
```

## 🔧 Available Scripts

### Development
```bash
pnpm dev          # Start development server
pnpm lint         # Run ESLint
pnpm format       # Format with Prettier
```

### Database
```bash
pnpm db:generate  # Generate migrations
pnpm db:migrate   # Run migrations
pnpm db:push      # Push schema to database
pnpm db:studio    # Open Drizzle Studio
pnpm db:seed      # Seed test data
```

### Production
```bash
pnpm build        # Build for production
pnpm start        # Start production server
```

## 📖 Features

- ✅ Modern Dashboard
- ✅ User Management
- ✅ Authentication (Email/Password, GitHub, Google)
- ✅ Real-time Analytics
- ✅ Inventory Management
- ✅ Order Processing
- ✅ Dark/Light Theme
- ✅ Responsive Design
- ✅ Type-safe Development

## 🔐 Environment Variables

See `.env.example` for required environment variables.

## 📝 License

This project is part of Pharmaviyum CRM platform.

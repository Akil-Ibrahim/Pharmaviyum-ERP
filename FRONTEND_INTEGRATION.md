# 🚀 Frontend-Backend Integration Setup Complete

Your Pharmaviyum-CRM project is now fully configured for frontend-backend communication!

## 📋 What Was Set Up

### 1. **Environment Configuration** 
- ✅ `.env.local` - Frontend environment with backend API URLs
- ✅ Backend CORS enabled for all origins (development)

### 2. **Frontend API Client** (`lib/api-client.ts`)
- ✅ Typed HTTP client with GET, POST, PUT, PATCH, DELETE methods
- ✅ Automatic auth token handling
- ✅ Error handling and type safety

### 3. **React Hooks** (`lib/api-hooks.ts`)
- ✅ `useQuery` - For fetching data from backend
- ✅ `useMutation` - For creating/updating/deleting data
- ✅ `useBackendHealth` - For checking backend availability

### 4. **Backend Proxy Route** (`app/api/backend/route.ts`)
- ✅ Server-side proxying for CORS handling
- ✅ Request forwarding to backend API

### 5. **Docker Support**
- ✅ Frontend service added to `docker-compose.yml`
- ✅ Development overrides in `docker-compose.override.yml`
- ✅ Dockerfile ready for Next.js containerization

## 🎯 Quick Start

### Option 1: Local Development (Recommended)

**Terminal 1 - Start Backend:**
```bash
python -m uvicorn src.pharmaviyum.main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend/shadcn-admin
npm run dev
```

Then open: **http://localhost:3000**

### Option 2: Using Start Script

```bash
# One command to start everything
bash scripts/start-dev.sh
```

### Option 3: Docker Compose

```bash
docker compose up --build
```

## 📝 Usage Examples

### Fetch Data from Backend

```typescript
import { useQuery } from '@/lib/api-hooks';

export function Dashboard() {
  const { data: users, loading, error } = useQuery<User[]>('/users');

  if (loading) return <div>Loading users...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {users?.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}
```

### Mutate Data (Create, Update, Delete)

```typescript
import { useMutation } from '@/lib/api-hooks';

export function CreateUserForm() {
  const { mutate: createUser, loading } = useMutation<User, CreateUserDto>(
    '/users',
    'post',
    {
      onSuccess: (user) => {
        console.log('User created:', user);
        // Handle success
      },
      onError: (error) => {
        console.error('Failed to create user:', error);
      }
    }
  );

  const handleSubmit = async (formData: CreateUserDto) => {
    await createUser(formData);
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleSubmit({ name: 'John', email: 'john@example.com' });
    }}>
      <input type="submit" value={loading ? 'Creating...' : 'Create'} disabled={loading} />
    </form>
  );
}
```

### Direct API Calls

```typescript
import { api } from '@/lib/api-client';

// GET
const users = await api.get<User[]>('/users');

// POST
const newUser = await api.post<User>('/users', {
  name: 'Jane',
  email: 'jane@example.com'
});

// PUT
await api.put<User>('/users/1', { name: 'Jane Doe' });

// DELETE
await api.delete('/users/1');
```

## 🔗 Backend API Endpoints

The backend API is available at: `http://localhost:8000/api/v1`

### Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/users` | List/Create users |
| GET/PUT/DELETE | `/users/{id}` | Get/Update/Delete user |
| GET/POST | `/products` | List/Create products |
| GET/PUT/DELETE | `/products/{id}` | Get/Update/Delete product |
| GET/POST | `/orders` | List/Create orders |
| GET/PUT/DELETE | `/orders/{id}` | Get/Update/Delete order |

## 🐳 Docker Environment Variables

When running with Docker, set these in `.env`:

```env
# Frontend
FRONTEND_PORT=3000
BETTER_AUTH_SECRET=your-secret-key
BETTER_AUTH_URL=http://localhost:3000

# Backend
BACKEND_PORT=8000
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=pharmaviyum

# AI Service
MORTARIUM_PORT=8001
MODEL_PATH=/app/models/qwen2.5-7b-instruct-q4_k_m.gguf

# Nginx
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
```

## 🔍 Troubleshooting

### Frontend can't connect to backend?
1. Check backend is running: `curl http://localhost:8000/health`
2. Verify `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for CORS errors

### CORS errors?
The backend has CORS enabled for all origins in development mode. For production, update:
```python
# In src/pharmaviyum/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Docker compose errors?
```bash
# Clean up and rebuild
docker compose down -v
docker compose up --build
```

## 📚 Documentation

- [Integration Details](./frontend/shadcn-admin/INTEGRATION.md)
- [Backend Docs](./README.md)
- [Frontend Docs](./frontend/shadcn-admin/README.md)

## ✨ Features

- ✅ TypeScript support for API responses
- ✅ Automatic auth token management
- ✅ CORS handling
- ✅ Server-side request proxying
- ✅ Loading and error states
- ✅ Refetch capabilities
- ✅ Docker containerization
- ✅ Development hot-reload

## 🎓 Next Steps

1. Update `.env.local` with your configuration
2. Configure OAuth providers (GitHub, Google) if needed
3. Set up database migrations with Drizzle ORM
4. Build your first API-connected component!

---

Happy coding! 🚀

# Frontend-Backend Integration Guide

## Setup

The frontend is now configured to communicate with the backend API.

### Environment Configuration

The `.env.local` file contains:
- `NEXT_PUBLIC_API_URL=http://localhost:8000` — Backend base URL
- `NEXT_PUBLIC_API_BASE=/api/v1` — API version prefix
- `NEXT_PUBLIC_AI_SERVICE_URL=http://localhost:8001` — AI service (Mortarium)

### Running Locally

**Terminal 1 - Start Backend:**
```bash
# From project root
python -m uvicorn src.pharmaviyum.main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend/shadcn-admin
npm run dev  # Runs on http://localhost:3000
```

### Using the API Client

#### Basic API Calls

```typescript
import { api } from '@/lib/api-client';

// GET request
const users = await api.get('/users');

// POST request
const newUser = await api.post('/users', {
  name: 'John',
  email: 'john@example.com'
});

// PUT/PATCH/DELETE
await api.put('/users/1', { name: 'Updated' });
await api.delete('/users/1');
```

#### Using React Hooks

```typescript
import { useQuery, useMutation } from '@/lib/api-hooks';

export function UserList() {
  // Fetch data
  const { data: users, loading, error } = useQuery<User[]>('/users');
  
  // Mutate data
  const { mutate: createUser, loading: creating } = useMutation<User, CreateUserDto>(
    '/users',
    'post',
    {
      onSuccess: (user) => console.log('User created:', user),
      onError: (error) => console.error('Failed:', error),
    }
  );

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      {users?.map(user => (
        <div key={user.id}>{user.name}</div>
      ))}
      <button 
        onClick={() => createUser({ name: 'New User', email: 'user@example.com' })}
        disabled={creating}
      >
        {creating ? 'Creating...' : 'Create User'}
      </button>
    </div>
  );
}
```

### Backend API Endpoints

The backend API is available at `/api/v1`:

- **Health Check:** `GET /health`
- **Users:** `GET|POST /users`, `GET|PUT|DELETE /users/{id}`
- **Products:** `GET|POST /products`, `GET|PUT|DELETE /products/{id}`
- **Orders:** `GET|POST /orders`, `GET|PUT|DELETE /orders/{id}`

### CORS Configuration

The backend has CORS enabled for all origins (development mode):
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, update `src/pharmaviyum/main.py` to restrict origins.

### Docker Deployment

When running with Docker, update `.env.local`:
```
NEXT_PUBLIC_API_URL=http://backend:8000
```

The services will communicate through the shared Docker network.

### Troubleshooting

**CORS errors?**
- Check backend CORS configuration is enabled
- Verify `NEXT_PUBLIC_API_URL` is correct
- Use browser DevTools Network tab to see actual requests

**Backend not reachable?**
- Ensure backend is running on port 8000
- Check firewall/network settings
- Try `curl http://localhost:8000/health` to test backend

**Build errors?**
- Run `npm install` in `frontend/shadcn-admin`
- Clear `.next` folder: `rm -rf .next`
- Rebuild: `npm run build`

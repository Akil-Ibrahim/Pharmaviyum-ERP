import { StrictMode } from 'react'
import ReactDOM from 'react-dom/client'
import {
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query'
import { RouterProvider, createRouter } from '@tanstack/react-router'
import { toast } from 'sonner'
import { handleServerError } from '@/lib/handle-server-error'
import { getHttpStatus, shouldRetryQuery } from '@/lib/query-error-policy'
import { useAuthStore } from '@/stores/auth-store'
import { DirectionProvider } from './context/direction-provider'
import { FontProvider } from './context/font-provider'
import { ThemeProvider } from './context/theme-provider'
// Generated Routes
import { routeTree } from './routeTree.gen'
// Styles
import './styles/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // eslint-disable-next-line no-console
        if (import.meta.env.DEV) console.log({ failureCount, error })

        return shouldRetryQuery(failureCount, error, import.meta.env.DEV)
      },
      refetchOnWindowFocus: import.meta.env.PROD,
      staleTime: 10 * 1000, // 10s
    },
    mutations: {
      onError: (error) => {
        if (getHttpStatus(error) === 401) {
          queryClient.clear()
          toast.error('Session expired!')
          useAuthStore.getState().auth.reset()
          const redirect = `${router.history.location.href}`
          router.navigate({ to: '/sign-in', search: { redirect } })
          return
        }

        handleServerError(error)

        if (getHttpStatus(error) === 304) {
          toast.error('Content not modified!')
        }
      },
    },
  },
  queryCache: new QueryCache({
    onError: (error) => {
      const status = getHttpStatus(error)
      if (status === 401) {
        queryClient.clear()
        toast.error('Session expired!')
        useAuthStore.getState().auth.reset()
        const redirect = `${router.history.location.href}`
        router.navigate({ to: '/sign-in', search: { redirect } })
      }
      if (status !== undefined && status >= 500) {
        toast.error('Internal Server Error!')
        // Only navigate to error page in production to avoid disrupting HMR in development
        if (import.meta.env.PROD) {
          router.navigate({ to: '/500' })
        }
      }
      if (status === 403) {
        // router.navigate("/forbidden", { replace: true });
      }
    },
  }),
})

// Create a new router instance
const router = createRouter({
  routeTree,
  context: { queryClient },
  defaultPreload: 'intent',
  defaultPreloadStaleTime: 0,
})

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

// Render the app
const rootElement = document.getElementById('root')!
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement)
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <FontProvider>
            <DirectionProvider>
              <RouterProvider router={router} />
            </DirectionProvider>
          </FontProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </StrictMode>
  )
}

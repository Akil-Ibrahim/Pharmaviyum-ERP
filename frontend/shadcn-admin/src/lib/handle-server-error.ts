import { AxiosError } from 'axios'
import { toast } from 'sonner'
import { ApiError } from '@/lib/api-error'

export function handleServerError(error: unknown) {
  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.log(error)
  }

  let errMsg = 'Something went wrong!'

  if (
    error &&
    typeof error === 'object' &&
    'status' in error &&
    Number(error.status) === 204
  ) {
    errMsg = 'No content.'
  }

  if (error instanceof ApiError) {
    const payload = error.payload
    const title =
      payload && typeof payload === 'object' && 'title' in payload
        ? payload.title
        : undefined
    errMsg =
      typeof title === 'string' && title.length > 0 ? title : error.message
  }

  if (error instanceof AxiosError) {
    const title = error.response?.data?.title
    const detail = error.response?.data?.detail
    if (typeof title === 'string' && title.length > 0) {
      errMsg = title
    } else if (typeof detail === 'string' && detail.length > 0) {
      errMsg = detail
    }
  }

  toast.error(errMsg)
}

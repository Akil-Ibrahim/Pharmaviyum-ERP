/**
 * Toast hook for showing notifications.
 * 
 * Usage:
 *   const { success, error } = useToast();
 *   success('Patient created successfully!');
 */
import { toast } from 'sonner';

export function useToast() {
  return {
    success: (message: string, description?: string) => {
      toast.success(message, { description });
    },
    
    error: (message: string, description?: string) => {
      toast.error(message, { description });
    },
    
    warning: (message: string, description?: string) => {
      toast.warning(message, { description });
    },
    
    info: (message: string, description?: string) => {
      toast.info(message, { description });
    },
    
    loading: async <T>(
      promise: Promise<T>,
      loadingMessage: string,
      successMessage?: string,
      errorMessage?: string,
    ): Promise<T> => {
      return toast.promise(promise, {
        loading: loadingMessage,
        success: successMessage || 'Success!',
        error: errorMessage || 'Operation failed',
      });
    },
  };
}

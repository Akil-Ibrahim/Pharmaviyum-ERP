/**
 * Toast Provider using Sonner.
 * Beautiful, animated toast notifications with theme support.
 */
import { Toaster } from 'sonner';
import { useTheme } from '../hooks/useTheme';

export function ToastProvider() {
  const { resolvedTheme } = useTheme();
  
  return (
    <Toaster
      theme={resolvedTheme}
      position="top-right"
      richColors
      closeButton
      toastOptions={{ duration: 4000 }}
    />
  );
}

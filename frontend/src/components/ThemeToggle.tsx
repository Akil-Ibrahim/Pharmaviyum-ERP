/**
 * Theme toggle button group.
 */
import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from '../hooks/useTheme';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  
  const buttons = [
    { value: 'light' as const, icon: Sun, label: 'Light theme' },
    { value: 'dark' as const, icon: Moon, label: 'Dark theme' },
    { value: 'system' as const, icon: Monitor, label: 'System theme' },
  ];
  
  return (
    <div className="flex items-center gap-1 rounded-lg border p-1">
      {buttons.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          type="button"
          onClick={() => setTheme(value)}
          aria-label={label}
          aria-pressed={theme === value}
          className={`h-8 w-8 inline-flex items-center justify-center rounded-md transition-colors
            ${theme === value ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-muted'}
          `}
        >
          <Icon className="h-4 w-4" />
        </button>
      ))}
    </div>
  );
}

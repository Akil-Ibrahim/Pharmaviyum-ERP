/**
 * Shared Button component for email templates.
 */
import { Button as EmailButton } from '@react-email/components';

interface ButtonProps {
  href: string;
  children: React.ReactNode;
  variant?: 'primary' | 'secondary';
}

export function Button({ href, children, variant = 'primary' }: ButtonProps) {
  const styles = {
    primary: {
      backgroundColor: '#1a73e8',
      color: 'white',
    },
    secondary: {
      backgroundColor: '#f0f0f0',
      color: '#333',
    },
  };

  return (
    <EmailButton
      href={href}
      style={{
        ...styles[variant],
        padding: '12px 24px',
        borderRadius: '6px',
        textDecoration: 'none',
        display: 'inline-block',
      }}
    >
      {children}
    </EmailButton>
  );
}

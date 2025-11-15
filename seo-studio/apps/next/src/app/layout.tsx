// app/layout.tsx
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../styles/globals.css';
import '../styles/tokens.css';
import { ThemeProvider } from '@/components/temit/ThemeProvider';
import { cookies } from 'next/headers';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SEO Studio',
  description: 'A data-driven CMS for the modern web.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const theme = cookies().get('theme')?.value || 'studio-classic';
  const variant = (cookies().get('variant')?.value as 'light' | 'dark') || 'light';

  return (
    <html lang="en" className={variant}>
      <body className={inter.className}>
        <ThemeProvider initialTheme={theme} initialVariant={variant}>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

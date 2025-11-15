// app/page.tsx
'use client'; // This page uses hooks, so it must be a client component

import { useTheme } from '@/components/temit/ThemeProvider';

export default function HomePage() {
  const { theme } = useTheme();

  // Dynamically render the slots defined in the current theme
  const Header = theme.slots.header;
  const Hero = theme.slots.hero;
  const Content = theme.slots.content;
  const Sidebar = theme.slots.sidebar;
  const Footer = theme.slots.footer;

  return (
    <div>
      <Header />
      <Hero />
      <main className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Content />
          </div>
          <div>
            <Sidebar />
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

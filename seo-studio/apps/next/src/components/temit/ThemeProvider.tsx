// components/temit/ThemeProvider.tsx
'use client';

import React from 'react';
import { themes, Theme } from './registry';

interface ThemeContextType {
  theme: Theme;
  variant: 'light' | 'dark';
  setTheme: (themeId: string) => void;
  setVariant: (variant: 'light' | 'dark') => void;
}

const ThemeContext = React.createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider = ({
  initialTheme = 'studio-classic',
  initialVariant = 'light',
  children,
}: {
  initialTheme?: string;
  initialVariant?: 'light' | 'dark';
  children: React.ReactNode;
}) => {
  const [themeId, setThemeId] = React.useState(initialTheme);
  const [variant, setVariant] = React.useState(initialVariant);

  const theme = themes[themeId] || themes['studio-classic'];

  React.useEffect(() => {
    // Update CSS variables and dark mode class on the root element
    document.documentElement.classList.remove('dark', 'light');
    document.documentElement.classList.add(variant);

    const tokens = theme.tokens[variant] || {};
    for (const [key, value] of Object.entries(tokens)) {
      document.documentElement.style.setProperty(`--${key}`, value);
    }
  }, [theme, variant]);

  const value = {
    theme,
    variant,
    setTheme: setThemeId,
    setVariant,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};

export const useTheme = () => {
  const context = React.useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

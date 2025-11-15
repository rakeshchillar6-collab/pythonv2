// components/temit/registry.ts
import { HeaderClassic } from './slots/Header';
import { HeroSplit } from './slots/Hero';
import { FooterMinimal } from './slots/Footer';

// Define the shape of a theme
export interface Theme {
  slots: {
    [key: string]: React.FC<any>;
  };
  tokens: {
    light: { [key: string]: string };
    dark: { [key: string]: string };
  };
}

// A simple placeholder for a component
const Placeholder = ({ name }: { name: string }) => <div className="border-2 border-dashed p-4">Slot: {name}</div>;

export const themes: { [key: string]: Theme } = {
  "studio-classic": {
    slots: {
      header: (props) => <HeaderClassic {...props} />,
      hero: (props) => <HeroSplit {...props} />,
      content: (props) => <Placeholder name="Content" {...props} />,
      sidebar: (props) => <Placeholder name="Sidebar" {...props} />,
      footer: (props) => <FooterMinimal {...props} />,
      banner: (props) => <Placeholder name="Banner" {...props} />,
    },
    tokens: {
      light: {
        radius: '0.5rem',
        shadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        // ... other light theme tokens
      },
      dark: {
        radius: '0.5rem',
        shadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        // ... other dark theme tokens
      },
    },
  },
};

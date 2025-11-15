// components/temit/slots/Footer.tsx
import React from 'react';

export const FooterMinimal = () => {
  return (
    <footer className="bg-white dark:bg-gray-800 border-t mt-8">
      <div className="container mx-auto px-4 py-6 text-center text-gray-500">
        <p>&copy; {new Date().getFullYear()} SEO Studio. All rights reserved.</p>
      </div>
    </footer>
  );
};

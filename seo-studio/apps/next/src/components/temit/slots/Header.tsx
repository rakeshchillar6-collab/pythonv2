// components/temit/slots/Header.tsx
import React from 'react';

export const HeaderClassic = () => {
  return (
    <header className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">SEO Studio</h1>
        <nav className="space-x-4">
          <a href="/" className="hover:underline">Home</a>
          <a href="/blog" className="hover:underline">Blog</a>
          <a href="/search" className="hover:underline">Search</a>
        </nav>
      </div>
    </header>
  );
};

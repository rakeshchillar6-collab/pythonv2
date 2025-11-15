// components/temit/slots/Hero.tsx
import React from 'react';

export const HeroSplit = () => {
  return (
    <section className="bg-gray-100 dark:bg-gray-700">
      <div className="container mx-auto px-4 py-16 grid md:grid-cols-2 gap-8 items-center">
        <div>
          <h2 className="text-4xl font-bold mb-4">Welcome to SEO Studio</h2>
          <p className="text-lg text-gray-600 dark:text-gray-300">
            A data-driven CMS for the modern web.
          </p>
        </div>
        <div className="bg-gray-300 dark:bg-gray-600 h-64 rounded-lg flex items-center justify-center">
          <span className="text-gray-500">Image Placeholder</span>
        </div>
      </div>
    </section>
  );
};

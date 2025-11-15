// components/content/Details.tsx
'use client';

import React from 'react';

interface DetailsProps {
  summary: string;
  children: React.ReactNode;
}

export const Details = ({ summary, children }: DetailsProps) => {
  return (
    <details className="group border rounded-lg overflow-hidden">
      <summary className="cursor-pointer p-4 bg-gray-50 dark:bg-gray-700 font-medium group-open:bg-gray-100 dark:group-open:bg-gray-600 transition-colors">
        {summary}
      </summary>
      <div className="border-t">
        {children}
      </div>
    </details>
  );
};

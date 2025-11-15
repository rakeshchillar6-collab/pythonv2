// components/content/FAQ.tsx
'use client';

import React from 'react';
import { Details } from './Details';

interface FaqItem {
  question: string;
  answer: string;
}

interface FAQProps {
  items: FaqItem[];
}

export const FAQ = ({ items }: FAQProps) => {
  if (!items || items.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      {items.map((item, index) => (
        <Details key={index} summary={item.question}>
          <div className="p-4" dangerouslySetInnerHTML={{ __html: item.answer }} />
        </Details>
      ))}
    </div>
  );
};

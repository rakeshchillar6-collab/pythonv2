// lib/schema.ts
import Script from 'next/script';
import React from 'react';

export const injectJsonLd = (jsonld: any[] | undefined) => {
  if (!jsonld || jsonld.length === 0) {
    return null;
  }

  return (
    <Script
      id="json-ld"
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(jsonld, null, 2),
      }}
    />
  );
};

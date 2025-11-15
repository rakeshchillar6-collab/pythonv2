// components/content/RenderHTML.tsx
import React from 'react';
import { unified } from 'unified';
import rehypeParse from 'rehype-parse';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { toReact } from 'rehype-react';

import { FAQ } from './FAQ';
import { Details } from './Details';
// Import other content components as needed

// Extend the default sanitization schema to allow our custom elements
const schema = {
  ...defaultSchema,
  tagNames: [...(defaultSchema.tagNames || []), 'faq-block', 'variable'],
  attributes: {
    ...defaultSchema.attributes,
    'faq-block': ['items'],
    variable: ['name'],
  },
};

interface RenderHTMLProps {
  html: string;
  variables?: Record<string, string>;
}

export const RenderHTML = ({ html, variables }: RenderHTMLProps) => {
  const processor = unified()
    .use(rehypeParse, { fragment: true })
    .use(rehypeSanitize, schema)
    .use(toReact, {
      createElement: React.createElement,
      components: {
        'faq-block': (props: any) => {
          try {
            const items = JSON.parse(props.items || '[]');
            return <FAQ items={items} />;
          } catch (e) {
            return <div className="text-red-500">Error parsing FAQ block</div>;
          }
        },
        'variable': (props: any) => {
            const varName = props.name || '';
            return <span className="font-semibold text-primary">{variables?.[varName] || `[${varName}]`}</span>;
        },
        details: (props: any) => {
            const summary = props.children?.find((c: any) => c.type === 'summary')?.props?.children;
            const content = props.children?.filter((c: any) => c.type !== 'summary');
            return <Details summary={summary}>{content}</Details>;
        }
        // ... add mappings for Table, Figure, etc.
      },
    });

  return <div className="prose dark:prose-invert max-w-none">{processor.processSync(html).result}</div>;
};

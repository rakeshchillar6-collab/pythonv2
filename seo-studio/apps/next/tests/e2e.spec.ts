// tests/e2e.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dynamic Post Page', () => {
  test('should load and display the post content and SEO metadata', async ({ page }) => {
    // Mock the API response for the post
    await page.route('http://localhost:8000/api/content/render/test-post/', async route => {
      const json = {
        id: '123',
        slug: 'test-post',
        html: '<h1>Test Post Title</h1><p>This is the content.</p>',
        meta: {
          title: 'Test Post Title',
          seo_title: 'SEO Title for Test Post',
          seo_description: 'This is the SEO description.',
        },
        jsonld: [
          {
            '@context': 'https://schema.org',
            '@type': 'Article',
            headline: 'SEO Title for Test Post',
          },
        ],
      };
      await route.fulfill({ json });
    });

    // Navigate to the page
    await page.goto('/test-post');

    // Check for the correct title
    await expect(page).toHaveTitle('SEO Title for Test Post');

    // Check that the main heading is rendered
    await expect(page.getByRole('heading', { name: 'Test Post Title' })).toBeVisible();

    // Check that the paragraph content is rendered
    expect(await page.textContent('p')).toContain('This is the content.');

    // Check that the JSON-LD script was injected correctly
    const jsonLdScript = await page.locator('script[type="application/ld+json"]');
    await expect(jsonLdScript).toBeAttached();

    const jsonLdContent = JSON.parse(await jsonLdScript.textContent() || '[]');
    expect(jsonLdContent[0]['@type']).toBe('Article');
    expect(jsonLdContent[0].headline).toBe('SEO Title for Test Post');
  });
});

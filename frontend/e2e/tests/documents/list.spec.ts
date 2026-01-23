import { test, expect } from '@playwright/test';

test.describe('Document List', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display document list', async ({ page }) => {
    // Check for document list container
    await expect(page.locator('[data-testid="document-list"]')).toBeVisible();
    
    // Check for at least one document item
    await expect(page.locator('[data-testid="document-item"]')).toHaveCount(1);
  });

  test('should display document details', async ({ page }) => {
    // Check for document filename
    await expect(page.locator('[data-testid="document-filename"]')).toBeVisible();
    
    // Check for document type badge
    await expect(page.locator('[data-testid="document-type"]')).toBeVisible();
    
    // Check for document status
    await expect(page.locator('[data-testid="document-status"]')).toBeVisible();
    
    // Check for confidence score
    await expect(page.locator('[data-testid="document-confidence"]')).toBeVisible();
  });

  test('should filter documents by type', async ({ page }) => {
    // Click on filter dropdown
    await page.click('[data-testid="filter-dropdown"]');
    
    // Select invoice type
    await page.click('text=Invoice');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    // Check that only invoices are shown
    const documentTypes = await page.locator('[data-testid="document-type"]').allTextContents();
    documentTypes.forEach(type => {
      expect(type).toContain('invoice');
    });
  });

  test('should search documents', async ({ page }) => {
    // Type in search box
    await page.fill('[data-testid="search-input"]', 'Acme');
    
    // Wait for search results
    await page.waitForTimeout(500);
    
    // Check that results contain search term
    const filenames = await page.locator('[data-testid="document-filename"]').allTextContents();
    filenames.forEach(filename => {
      expect(filename.toLowerCase()).toContain('acme');
    });
  });

  test('should navigate to document details', async ({ page }) => {
    // Click on first document
    await page.click('[data-testid="document-item"]');
    
    // Check that we navigated to details page
    await expect(page).toHaveURL(/\/documents\/[a-f0-9]+/);
    
    // Check for document details
    await expect(page.locator('[data-testid="document-details"]')).toBeVisible();
  });
});

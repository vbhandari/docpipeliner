import { test, expect } from '@playwright/test';

test.describe('Search and Filtering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should search documents by text', async ({ page }) => {
    // Type in search box
    await page.fill('[data-testid="search-input"]', 'Acme Corporation');
    
    // Wait for search results
    await page.waitForTimeout(500);
    
    // Check for search results
    await expect(page.locator('[data-testid="search-results"]')).toBeVisible();
    
    // Check that results contain search term
    const filenames = await page.locator('[data-testid="result-filename"]').allTextContents();
    filenames.forEach(filename => {
      expect(filename.toLowerCase()).toContain('acme');
    });
  });

  test('should highlight search terms in results', async ({ page }) => {
    // Type in search box
    await page.fill('[data-testid="search-input"]', 'Acme');
    
    // Wait for search results
    await page.waitForTimeout(500);
    
    // Check for highlighted text
    const highlightedText = await page.locator('[data-testid="result-filename"]').textContent();
    expect(highlightedText).toContain('<mark>Acme</mark>');
  });

  test('should filter documents by type', async ({ page }) => {
    // Click on filter dropdown
    await page.click('[data-testid="filter-dropdown"]');
    
    // Select invoice type
    await page.click('text=Invoice');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    // Check for filter badge
    await expect(page.locator('[data-testid="filter-applied"]')).toBeVisible();
    await expect(page.locator('[data-testid="filter-applied"]')).toHaveText('invoice');
    
    // Check that only invoices are shown
    const documentTypes = await page.locator('[data-testid="result-type"]').allTextContents();
    documentTypes.forEach(type => {
      expect(type.toLowerCase()).toContain('invoice');
    });
  });

  test('should filter documents by status', async ({ page }) => {
    // Click on status filter
    await page.click('[data-testid="status-filter"]');
    
    // Select completed status
    await page.click('text=Completed');
    
    // Wait for filter to apply
    await page.waitForTimeout(500);
    
    // Check that only completed documents are shown
    const statuses = await page.locator('[data-testid="result-status"]').allTextContents();
    statuses.forEach(status => {
      expect(status.toLowerCase()).toContain('completed');
    });
  });

  test('should apply multiple filters', async ({ page }) => {
    // Apply type filter
    await page.click('[data-testid="filter-dropdown"]');
    await page.click('text=Invoice');
    
    // Apply status filter
    await page.click('[data-testid="status-filter"]');
    await page.click('text=Completed');
    
    // Apply confidence filter
    await page.fill('[data-testid="confidence-min"]', '0.8');
    await page.click('[data-testid="apply-filters"]');
    
    // Wait for filters to apply
    await page.waitForTimeout(500);
    
    // Check for multiple filter badges
    await expect(page.locator('[data-testid="filter-badge"]')).toHaveCount(3);
    
    // Check that results match all filters
    const documentTypes = await page.locator('[data-testid="result-type"]').allTextContents();
    const statuses = await page.locator('[data-testid="result-status"]').allTextContents();
    const confidences = await page.locator('[data-testid="result-confidence"]').allTextContents();
    
    documentTypes.forEach(type => {
      expect(type.toLowerCase()).toContain('invoice');
    });
    statuses.forEach(status => {
      expect(status.toLowerCase()).toContain('completed');
    });
    confidences.forEach(conf => {
      expect(parseFloat(conf)).toBeGreaterThanOrEqual(0.8);
    });
  });

  test('should clear filters', async ({ page }) => {
    // Apply a filter
    await page.click('[data-testid="filter-dropdown"]');
    await page.click('text=Invoice');
    
    // Click clear filters button
    await page.click('[data-testid="clear-filters"]');
    
    // Wait for filters to clear
    await page.waitForTimeout(500);
    
    // Check that filter badge is removed
    await expect(page.locator('[data-testid="filter-applied"]')).not.toBeVisible();
    
    // Check that all documents are shown
    await expect(page.locator('[data-testid="result-item"]')).toHaveCount(10);
  });

  test('should sort results', async ({ page }) => {
    // Click on sort dropdown
    await page.click('[data-testid="sort-dropdown"]');
    
    // Select sort by date descending
    await page.click('text=Date (Newest)');
    
    // Wait for sort to apply
    await page.waitForTimeout(500);
    
    // Get dates from results
    const dates = await page.locator('[data-testid="result-date"]').allTextContents();
    
    // Check that dates are in descending order
    for (let i = 0; i < dates.length - 1; i++) {
      const date1 = new Date(dates[i]);
      const date2 = new Date(dates[i + 1]);
      expect(date1.getTime()).toBeGreaterThanOrEqual(date2.getTime());
    }
  });
});

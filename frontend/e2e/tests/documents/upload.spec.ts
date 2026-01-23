import { test, expect } from '@playwright/test';

test.describe('Document Upload', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should navigate to upload page', async ({ page }) => {
    await page.click('text=Upload');
    await expect(page).toHaveURL(/.*upload/);
  });

  test('should show upload form', async ({ page }) => {
    await page.goto('/upload');
    
    // Check for upload area
    await expect(page.locator('[data-testid="upload-area"]')).toBeVisible();
    
    // Check for file input
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).toBeVisible();
    
    // Check for submit button
    await expect(page.locator('[data-testid="upload-button"]')).toBeVisible();
  });

  test('should upload a single document successfully', async ({ page }) => {
    await page.goto('/upload');
    
    // Create a mock file
    const file = await page.evaluate(() => {
      const blob = new Blob(['test content'], { type: 'application/pdf' });
      return new File([blob], 'test-invoice.pdf', { type: 'application/pdf' });
    });
    
    // Upload the file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(file);
    
    // Click upload button
    await page.click('[data-testid="upload-button"]');
    
    // Check for success message
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 10000 });
    
    // Check for document status
    await expect(page.locator('[data-testid="document-status"]')).toHaveText('queued');
  });

  test('should show validation error for invalid file type', async ({ page }) => {
    await page.goto('/upload');
    
    // Create a non-PDF file
    const file = await page.evaluate(() => {
      const blob = new Blob(['test content'], { type: 'text/plain' });
      return new File([blob], 'test-file.txt', { type: 'text/plain' });
    });
    
    // Upload the file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(file);
    
    // Click upload button
    await page.click('[data-testid="upload-button"]');
    
    // Check for error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-error"]')).toHaveText(
      'Invalid file type. Please upload a PDF file.'
    );
  });

  test('should show validation error for file size limit', async ({ page }) => {
    await page.goto('/upload');
    
    // Create a large file (mock)
    const file = await page.evaluate(() => {
      const blob = new Blob(['x'.repeat(51 * 1024 * 1024)], { type: 'application/pdf' });
      return new File([blob], 'large-file.pdf', { type: 'application/pdf' });
    });
    
    // Upload the file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles(file);
    
    // Click upload button
    await page.click('[data-testid="upload-button"]');
    
    // Check for error message
    await expect(page.locator('[data-testid="upload-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-error"]')).toHaveText(
      /File size exceeds.*50.*MB/
    );
  });

  test('should support drag and drop upload', async ({ page }) => {
    await page.goto('/upload');
    
    // Create a mock file
    const file = await page.evaluate(() => {
      const blob = new Blob(['test content'], { type: 'application/pdf' });
      return new File([blob], 'drag-drop.pdf', { type: 'application/pdf' });
    });
    
    // Get the data transfer object
    const dataTransfer = await page.evaluateHandle((file) => {
      const dt = new DataTransfer();
      dt.items.add(file);
      return dt;
    }, file);
    
    // Simulate drag and drop
    const uploadArea = page.locator('[data-testid="upload-area"]');
    await uploadArea.dispatchEvent('drop', { dataTransfer });
    
    // Check for success message
    await expect(page.locator('[data-testid="upload-success"]')).toBeVisible({ timeout: 10000 });
  });
});

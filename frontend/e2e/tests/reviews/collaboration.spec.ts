import { test, expect } from '@playwright/test';

test.describe('Collaborative Review', () => {
  test.beforeEach(async ({ page, context }) => {
    // Mock authentication
    await context.addInitScript(() => {
      localStorage.setItem('auth_token', 'test-token');
    });
    await page.goto('/reviews');
  });

  test('should display review list', async ({ page }) => {
    // Check for review list container
    await expect(page.locator('[data-testid="review-list"]')).toBeVisible();
    
    // Check for at least one review item
    await expect(page.locator('[data-testid="review-item"]')).toHaveCount(1);
  });

  test('should add comment to a field', async ({ page }) => {
    // Navigate to review page
    await page.click('[data-testid="review-item"]');
    
    // Click on comment button for a field
    await page.click('[data-testid="field-comment-button"]');
    
    // Type comment
    await page.fill('[data-testid="comment-input"]', 'Please verify this amount');
    
    // Submit comment
    await page.click('[data-testid="comment-submit"]');
    
    // Check for success message
    await expect(page.locator('[data-testid="comment-added"]')).toBeVisible();
    
    // Check that comment is displayed
    await expect(page.locator('[data-testid="comment-text"]')).toHaveText(
      'Please verify this amount'
    );
  });

  test('should add annotation to a field', async ({ page }) => {
    // Navigate to review page
    await page.click('[data-testid="review-item"]');
    
    // Click on annotate button for a field
    await page.click('[data-testid="field-annotate-button"]');
    
    // Select annotation type
    await page.click('[data-testid="annotation-type"]');
    await page.click('text=Question');
    
    // Type note
    await page.fill('[data-testid="annotation-note"]', 'Is this correct?');
    
    // Submit annotation
    await page.click('[data-testid="annotation-submit"]');
    
    // Check for success message
    await expect(page.locator('[data-testid="annotation-added"]')).toBeVisible();
    
    // Check that annotation is displayed
    await expect(page.locator('[data-testid="annotation-type"]')).toHaveText('question');
  });

  test('should assign review to another user', async ({ page }) => {
    // Navigate to review page
    await page.click('[data-testid="review-item"]');
    
    // Click on assign button
    await page.click('[data-testid="assign-button"]');
    
    // Type assignee email
    await page.fill('[data-testid="assignee-input"]', 'user@example.com');
    
    // Type message
    await page.fill('[data-testid="assign-message"]', 'Please review this invoice');
    
    // Submit assignment
    await page.click('[data-testid="assign-submit"]');
    
    // Check for success message
    await expect(page.locator('[data-testid="assign-success"]')).toBeVisible();
    
    // Check that assignee is displayed
    await expect(page.locator('[data-testid="assigned-to"]')).toHaveText('user@example.com');
  });

  test('should approve review', async ({ page }) => {
    // Navigate to review page
    await page.click('[data-testid="review-item"]');
    
    // Click on approve button
    await page.click('[data-testid="approve-button"]');
    
    // Confirm approval
    await page.click('[data-testid="confirm-approve"]');
    
    // Check for success message
    await expect(page.locator('[data-testid="approve-success"]')).toBeVisible();
    
    // Check that review status is updated
    await expect(page.locator('[data-testid="review-status"]')).toHaveText('completed');
  });

  test('should display threaded comments', async ({ page }) => {
    // Navigate to review page
    await page.click('[data-testid="review-item"]');
    
    // Click on comment button
    await page.click('[data-testid="field-comment-button"]');
    
    // Add a comment
    await page.fill('[data-testid="comment-input"]', 'Initial comment');
    await page.click('[data-testid="comment-submit"]');
    
    // Wait for comment to appear
    await expect(page.locator('[data-testid="comment-text"]')).toBeVisible();
    
    // Add a reply
    await page.click('[data-testid="reply-button"]');
    await page.fill('[data-testid="reply-input"]', 'This is a reply');
    await page.click('[data-testid="reply-submit"]');
    
    // Check that reply is displayed
    await expect(page.locator('[data-testid="reply-text"]')).toHaveText('This is a reply');
  });
});

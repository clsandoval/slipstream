import { describe, it, expect } from 'vitest';
import { theme } from '../theme';

// Helper to convert rem to pixels (assuming 16px base)
function remToPixels(rem: string): number {
  return parseFloat(rem) * 16;
}

describe('Theme', () => {
  // Test 1: Has dark background
  it('defines dark background colors', () => {
    expect(theme.colors.background).toBe('#0f172a'); // slate-900
  });

  // Test 2: Has readable text colors
  it('defines high-contrast text', () => {
    expect(theme.colors.text).toBe('#f8fafc'); // slate-50
  });

  // Test 3: Giant text size defined (8rem = 128px)
  it('defines giant text size for rates', () => {
    expect(remToPixels(theme.fontSize.giant)).toBeGreaterThanOrEqual(96);
  });

  // Test 4: Large text readable from 10ft (4rem = 64px)
  it('defines large text for poolside visibility', () => {
    expect(remToPixels(theme.fontSize.large)).toBeGreaterThanOrEqual(48);
  });

  // Test 5: Monospace font for numbers
  it('uses monospace for numeric displays', () => {
    expect(theme.fontFamily.mono).toContain('mono');
  });

  // Additional tests
  it('defines surface color for cards', () => {
    expect(theme.colors.surface).toBe('#1e293b');
  });

  it('defines muted color for secondary text', () => {
    expect(theme.colors.muted).toBe('#94a3b8');
  });

  it('defines accent color for highlights', () => {
    expect(theme.colors.accent).toBe('#38bdf8');
  });

  it('defines success color for positive states', () => {
    expect(theme.colors.success).toBe('#22c55e');
  });

  it('defines medium font size (2rem = 32px)', () => {
    expect(remToPixels(theme.fontSize.medium)).toBeGreaterThanOrEqual(24);
  });
});

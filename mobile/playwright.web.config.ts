import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/deployment',
  timeout: 90000,
  expect: { timeout: 30000 },
  workers: 1,
  outputDir: './test-results-web',
  reporter: [['list']],
  use: {
    baseURL: process.env.MUSIC_WEB_URL ?? 'http://localhost:43729',
    acceptDownloads: true,
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'web-desktop', use: { browserName: 'chromium', viewport: { width: 1280, height: 900 } } },
    { name: 'web-phone', use: { browserName: 'chromium', viewport: { width: 393, height: 851 }, isMobile: true, hasTouch: true } },
  ],
});

import { defineConfig, devices } from '@playwright/test';
export default defineConfig({
  testDir: './tests/browser',
  timeout: 90000,
  expect: { timeout: 20000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:4173', acceptDownloads: true, trace: 'retain-on-failure' },
  projects: [
    { name: 'android-chromium', use: { browserName: 'chromium', viewport: { width: 393, height: 851 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true } },
    { name: 'ios-webkit', use: { browserName: 'webkit', viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true } },
  ],
  webServer: { command: 'npm run preview', url: 'http://127.0.0.1:4173', reuseExistingServer: true, timeout: 30000 },
});

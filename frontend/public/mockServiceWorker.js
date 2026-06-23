/**
 * Mock Service Worker - generated placeholder
 * Run `npx msw init public/` after npm install to generate the real file.
 * For development without MSW, this file provides a no-op service worker.
 */
if (typeof self !== 'undefined') {
  self.addEventListener('install', () => {
    self.skipWaiting()
  })

  self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim())
  })

  self.addEventListener('fetch', (event) => {
    // Pass through - actual MSW will intercept after `npx msw init`
  })
}

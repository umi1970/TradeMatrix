// Service Worker for Web Push Notifications
// Handles push events and displays notifications

self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received:', event);

  const data = event.data ? event.data.json() : {};
  const title = data.title || 'TradeMatrix Alert';
  const options = {
    body: data.body || 'New liquidity level alert',
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png',
    vibrate: [200, 100, 200],
    data: data.data || {},
    actions: [
      {
        action: 'view',
        title: 'View Dashboard',
      },
      {
        action: 'close',
        title: 'Dismiss',
      },
    ],
    requireInteraction: true,  // Keep notification visible
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  console.log('[Service Worker] Notification Click:', event);

  event.notification.close();

  if (event.action === 'view') {
    // Open dashboard
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});

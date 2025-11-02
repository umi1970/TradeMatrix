'use client'

import { useState, useEffect } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'

interface PushSubscription {
  endpoint: string
  keys: {
    p256dh: string
    auth: string
  }
}

export function usePushNotifications() {
  const [isSupported, setIsSupported] = useState(false)
  const [isSubscribed, setIsSubscribed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const supabase = createBrowserClient()

  // VAPID Public Key (get from environment or backend)
  const VAPID_PUBLIC_KEY = process.env.NEXT_PUBLIC_VAPID_PUBLIC_KEY || ''

  useEffect(() => {
    checkPushSupport()
  }, [])

  async function checkPushSupport() {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setIsSupported(false)
      setLoading(false)
      return
    }

    setIsSupported(true)

    // Check if already subscribed
    try {
      // Check if a service worker is already registered
      const registration = await navigator.serviceWorker.getRegistration()

      if (registration) {
        const subscription = await registration.pushManager.getSubscription()
        setIsSubscribed(!!subscription)
      } else {
        // No service worker registered yet
        setIsSubscribed(false)
      }
    } catch (err) {
      console.error('Error checking push subscription:', err)
      setIsSubscribed(false)
    }

    setLoading(false)
  }

  async function subscribeToPush(): Promise<boolean> {
    if (!isSupported) {
      setError('Push notifications not supported')
      return false
    }

    setLoading(true)
    setError(null)

    try {
      // Request notification permission
      const permission = await Notification.requestPermission()

      if (permission !== 'granted') {
        setError('Notification permission denied')
        setLoading(false)
        return false
      }

      // Register service worker
      const registration = await navigator.serviceWorker.register('/sw.js')
      await navigator.serviceWorker.ready

      // Subscribe to push notifications
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY),
      })

      // Save subscription to database
      const subscriptionJSON = subscription.toJSON()

      const { data: userData } = await supabase.auth.getUser()
      if (!userData.user) {
        throw new Error('User not authenticated')
      }

      const { error: dbError } = await supabase
        .from('user_push_subscriptions')
        .upsert({
          user_id: userData.user.id,
          endpoint: subscriptionJSON.endpoint,
          p256dh: subscriptionJSON.keys?.p256dh || '',
          auth: subscriptionJSON.keys?.auth || '',
          user_agent: navigator.userAgent,
          last_used_at: new Date().toISOString(),
        })

      if (dbError) throw dbError

      setIsSubscribed(true)
      setLoading(false)
      return true
    } catch (err) {
      console.error('Error subscribing to push:', err)
      setError(err instanceof Error ? err.message : 'Failed to subscribe')
      setLoading(false)
      return false
    }
  }

  async function unsubscribeFromPush(): Promise<boolean> {
    setLoading(true)
    setError(null)

    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()

      if (subscription) {
        await subscription.unsubscribe()

        // Remove from database
        const { data: userData } = await supabase.auth.getUser()
        if (userData.user) {
          await supabase
            .from('user_push_subscriptions')
            .delete()
            .eq('user_id', userData.user.id)
            .eq('endpoint', subscription.endpoint)
        }
      }

      setIsSubscribed(false)
      setLoading(false)
      return true
    } catch (err) {
      console.error('Error unsubscribing from push:', err)
      setError(err instanceof Error ? err.message : 'Failed to unsubscribe')
      setLoading(false)
      return false
    }
  }

  return {
    isSupported,
    isSubscribed,
    loading,
    error,
    subscribeToPush,
    unsubscribeFromPush,
  }
}

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')

  const rawData = window.atob(base64)
  const outputArray = new Uint8Array(rawData.length)

  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i)
  }
  return outputArray
}

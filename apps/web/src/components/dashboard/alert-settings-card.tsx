'use client'

import { useEffect, useState } from 'react'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Bell, BellOff, Loader2 } from 'lucide-react'
import { usePushNotifications } from '@/hooks/usePushNotifications'

interface Symbol {
  id: string
  symbol: string
  name: string
}

interface AlertSubscription {
  symbol_id: string
  yesterday_high_enabled: boolean
  yesterday_low_enabled: boolean
  pivot_point_enabled: boolean
}

export function AlertSettingsCard() {
  const [symbols, setSymbols] = useState<Symbol[]>([])
  const [subscriptions, setSubscriptions] = useState<Record<string, AlertSubscription>>({})
  const [loading, setLoading] = useState(true)

  const {
    isSupported,
    isSubscribed,
    loading: pushLoading,
    error: pushError,
    subscribeToPush,
    unsubscribeFromPush,
  } = usePushNotifications()

  const supabase = createBrowserClient()

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    try {
      // Fetch symbols
      const { data: symbolsData } = await supabase
        .from('symbols')
        .select('id, symbol, name')
        .eq('is_active', true)
        .order('symbol')

      setSymbols(symbolsData || [])

      // Fetch user subscriptions
      const { data: userData } = await supabase.auth.getUser()
      if (userData.user) {
        const { data: subsData } = await supabase
          .from('alert_subscriptions')
          .select('*')
          .eq('user_id', userData.user.id)

        const subsMap: Record<string, AlertSubscription> = {}
        subsData?.forEach((sub) => {
          subsMap[sub.symbol_id] = sub
        })
        setSubscriptions(subsMap)
      }
    } catch (err) {
      console.error('Error fetching data:', err)
    } finally {
      setLoading(false)
    }
  }

  async function toggleAlert(symbolId: string, alertType: keyof AlertSubscription) {
    const { data: userData } = await supabase.auth.getUser()
    if (!userData.user) return

    const currentSub = subscriptions[symbolId] || {
      yesterday_high_enabled: false,
      yesterday_low_enabled: false,
      pivot_point_enabled: false,
    }

    const newValue = !currentSub[alertType]

    try {
      const { error } = await supabase
        .from('alert_subscriptions')
        .upsert(
          {
            user_id: userData.user.id,
            symbol_id: symbolId,
            yesterday_high_enabled: alertType === 'yesterday_high_enabled' ? newValue : currentSub.yesterday_high_enabled,
            yesterday_low_enabled: alertType === 'yesterday_low_enabled' ? newValue : currentSub.yesterday_low_enabled,
            pivot_point_enabled: alertType === 'pivot_point_enabled' ? newValue : currentSub.pivot_point_enabled,
          },
          {
            onConflict: 'user_id,symbol_id',
          }
        )

      if (error) {
        console.error('Supabase error:', error)
        return
      }

      setSubscriptions({
        ...subscriptions,
        [symbolId]: {
          ...currentSub,
          [alertType]: newValue,
        },
      })
    } catch (err) {
      console.error('Error updating subscription:', err)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Alert Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Bell className="h-5 w-5" />
          Liquidity Level Alerts
        </CardTitle>
        <CardDescription>
          Get notified when price reaches key liquidity levels
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Push Notification Toggle */}
        <div className="mb-6 p-4 border rounded-lg bg-muted/50">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Browser Notifications</h3>
              <p className="text-sm text-muted-foreground">
                {isSupported
                  ? isSubscribed
                    ? 'You will receive realtime alerts'
                    : 'Enable to receive alerts'
                  : 'Not supported in this browser'}
              </p>
            </div>
            <Button
              onClick={isSubscribed ? unsubscribeFromPush : subscribeToPush}
              disabled={!isSupported || pushLoading}
              variant={isSubscribed ? 'destructive' : 'default'}
            >
              {pushLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : isSubscribed ? (
                <>
                  <BellOff className="mr-2 h-4 w-4" />
                  Disable
                </>
              ) : (
                <>
                  <Bell className="mr-2 h-4 w-4" />
                  Enable
                </>
              )}
            </Button>
          </div>
          {pushError && (
            <p className="mt-2 text-sm text-red-600">{pushError}</p>
          )}
        </div>

        {/* Per-Symbol Alert Settings */}
        <div className="space-y-4">
          <h3 className="font-semibold">Alert Preferences</h3>

          {symbols.map((symbol) => {
            const sub = subscriptions[symbol.id] || {
              yesterday_high_enabled: false,
              yesterday_low_enabled: false,
              pivot_point_enabled: false,
            }

            return (
              <div key={symbol.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <Badge variant="outline" className="font-mono">
                      {symbol.symbol}
                    </Badge>
                    <p className="text-sm text-muted-foreground mt-1">
                      {symbol.name}
                    </p>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor={`${symbol.id}-high`} className="text-sm">
                      🔴 Yesterday High (Short Setup)
                    </Label>
                    <Switch
                      id={`${symbol.id}-high`}
                      checked={sub.yesterday_high_enabled}
                      onCheckedChange={() =>
                        toggleAlert(symbol.id, 'yesterday_high_enabled')
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor={`${symbol.id}-low`} className="text-sm">
                      🟢 Yesterday Low (Long Setup)
                    </Label>
                    <Switch
                      id={`${symbol.id}-low`}
                      checked={sub.yesterday_low_enabled}
                      onCheckedChange={() =>
                        toggleAlert(symbol.id, 'yesterday_low_enabled')
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor={`${symbol.id}-pivot`} className="text-sm">
                      🟡 Pivot Point
                    </Label>
                    <Switch
                      id={`${symbol.id}-pivot`}
                      checked={sub.pivot_point_enabled}
                      onCheckedChange={() =>
                        toggleAlert(symbol.id, 'pivot_point_enabled')
                      }
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

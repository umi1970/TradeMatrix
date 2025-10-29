'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { createBrowserClient } from '@/lib/supabase/client'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Copy, Eye, EyeOff, Lock, Clock, Bell, AlertCircle } from 'lucide-react'

interface Profile {
  id: string
  email: string
  full_name?: string
  avatar_url?: string
  subscription_tier: 'free' | 'starter' | 'pro' | 'expert'
  created_at: string
  updated_at: string
}

interface NotificationPreferences {
  email_alerts: boolean
  daily_reports: boolean
  trade_signals: boolean
  risk_warnings: boolean
}

interface TradingHours {
  enabled: boolean
  start_time: string
  end_time: string
  timezone: string
}

export default function ProfilePage() {
  const router = useRouter()
  const supabase = createBrowserClient()

  const [profile, setProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Form states
  const [fullName, setFullName] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')

  // Preferences
  const [notifications, setNotifications] = useState<NotificationPreferences>({
    email_alerts: true,
    daily_reports: true,
    trade_signals: true,
    risk_warnings: true,
  })

  const [tradingHours, setTradingHours] = useState<TradingHours>({
    enabled: false,
    start_time: '09:00',
    end_time: '17:00',
    timezone: 'UTC',
  })

  // API Keys
  const [apiKey, setApiKey] = useState<string | null>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [copiedKey, setCopiedKey] = useState(false)

  // Load user profile
  useEffect(() => {
    const loadProfile = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()

        if (!user) {
          router.push('/login')
          return
        }

        // Fetch profile from profiles table
        const { data: profileData, error: profileError } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', user.id)
          .single()

        if (profileError && profileError.code !== 'PGRST116') {
          throw profileError
        }

        const userProfile: Profile = {
          id: user.id,
          email: user.email || '',
          full_name: profileData?.full_name,
          avatar_url: profileData?.avatar_url,
          subscription_tier: profileData?.subscription_tier || 'free',
          created_at: user.created_at || new Date().toISOString(),
          updated_at: profileData?.updated_at || new Date().toISOString(),
        }

        setProfile(userProfile)
        setFullName(userProfile.full_name || '')

        // Mock API Key (in production, fetch from database)
        setApiKey(`sk_live_${Math.random().toString(36).substr(2, 32)}`)

        setLoading(false)
      } catch (err) {
        console.error('Error loading profile:', err)
        setError('Failed to load profile')
        setLoading(false)
      }
    }

    loadProfile()
  }, [supabase, router])

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) return

      const { error } = await supabase
        .from('profiles')
        .update({
          full_name: fullName,
          updated_at: new Date().toISOString(),
        })
        .eq('id', user.id)

      if (error) throw error

      setSuccess('Profile updated successfully')
      if (profile) {
        setProfile({ ...profile, full_name: fullName })
      }
    } catch (err) {
      console.error('Error updating profile:', err)
      setError('Failed to update profile')
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    try {
      const { error } = await supabase.auth.updateUser({
        password: newPassword,
      })

      if (error) throw error

      setSuccess('Password changed successfully')
      setNewPassword('')
      setConfirmPassword('')
    } catch (err) {
      console.error('Error changing password:', err)
      setError('Failed to change password')
    }
  }

  const handleUpdatePreferences = async (
    key: keyof NotificationPreferences | keyof TradingHours,
    value: any
  ) => {
    setError(null)
    setSuccess(null)

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) return

      // Update local state
      if (key in notifications) {
        const updatedNotifications = {
          ...notifications,
          [key]: value,
        }
        setNotifications(updatedNotifications)
      } else {
        const updatedHours = {
          ...tradingHours,
          [key]: value,
        }
        setTradingHours(updatedHours)
      }

      // Mock update (in production, save to database)
      setSuccess('Settings saved')
    } catch (err) {
      console.error('Error updating preferences:', err)
      setError('Failed to save settings')
    }
  }

  const copyApiKey = () => {
    if (apiKey) {
      navigator.clipboard.writeText(apiKey)
      setCopiedKey(true)
      setTimeout(() => setCopiedKey(false), 2000)
    }
  }

  const regenerateApiKey = () => {
    // Mock regeneration
    setApiKey(`sk_live_${Math.random().toString(36).substr(2, 32)}`)
    setSuccess('API key regenerated')
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading profile...</p>
        </div>
      </div>
    )
  }

  if (!profile) {
    return (
      <div className="space-y-6">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>Failed to load profile</AlertDescription>
        </Alert>
      </div>
    )
  }

  const tierColors = {
    free: 'bg-gray-100 text-gray-800',
    starter: 'bg-blue-100 text-blue-800',
    pro: 'bg-purple-100 text-purple-800',
    expert: 'bg-yellow-100 text-yellow-800',
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profile & Settings</h1>
        <p className="text-muted-foreground mt-1">
          Manage your account, preferences, and API keys
        </p>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      {success && (
        <Alert className="bg-green-50 text-green-900 border-green-200">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      {/* Account & Subscription */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Account Information Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>Account Information</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Email
              </label>
              <p className="text-sm mt-1 font-mono">{profile.email}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                User ID
              </label>
              <p className="text-xs font-mono mt-1 text-muted-foreground truncate">
                {profile.id}
              </p>
            </div>
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Member Since
              </label>
              <p className="text-sm mt-1">
                {new Date(profile.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Subscription Card */}
        <Card>
          <CardHeader>
            <CardTitle>Subscription</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-muted-foreground">
                Current Plan
              </label>
              <div className="mt-2">
                <Badge className={`text-sm capitalize ${tierColors[profile.subscription_tier]}`}>
                  {profile.subscription_tier}
                </Badge>
              </div>
            </div>
            <div className="pt-2 space-y-2">
              <p className="text-xs text-muted-foreground">
                {profile.subscription_tier === 'free'
                  ? 'Limited to basic features. Upgrade for more analysis tools.'
                  : 'Thank you for your subscription!'}
              </p>
            </div>
            <Button variant="outline" className="w-full">
              {profile.subscription_tier === 'free'
                ? 'Upgrade Plan'
                : 'Manage Subscription'}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Full Name Update */}
      <Card>
        <CardHeader>
          <CardTitle>Edit Profile</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <Label htmlFor="full_name">Full Name</Label>
              <Input
                id="full_name"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Enter your full name"
                className="mt-1"
              />
            </div>
            <Button type="submit">Save Changes</Button>
          </form>
        </CardContent>
      </Card>

      {/* Notification Preferences */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            Notification Preferences
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            {[
              {
                key: 'email_alerts' as const,
                label: 'Email Alerts',
                description: 'Receive email notifications for important alerts',
              },
              {
                key: 'daily_reports' as const,
                label: 'Daily Reports',
                description: 'Get daily AI-generated trading reports',
              },
              {
                key: 'trade_signals' as const,
                label: 'Trade Signals',
                description: 'Notify me when new trade signals are generated',
              },
              {
                key: 'risk_warnings' as const,
                label: 'Risk Warnings',
                description: 'Alert me of potential risks in open positions',
              },
            ].map(({ key, label, description }) => (
              <div key={key} className="flex items-start gap-3 pb-3 border-b last:border-0">
                <input
                  type="checkbox"
                  id={key}
                  checked={notifications[key]}
                  onChange={(e) => handleUpdatePreferences(key, e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-gray-300"
                />
                <div className="flex-1">
                  <label htmlFor={key} className="text-sm font-medium cursor-pointer">
                    {label}
                  </label>
                  <p className="text-xs text-muted-foreground mt-1">{description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Trading Hours */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Trading Hours
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-3 pb-4 border-b">
            <input
              type="checkbox"
              id="trading_hours_enabled"
              checked={tradingHours.enabled}
              onChange={(e) =>
                handleUpdatePreferences('enabled', e.target.checked)
              }
              className="mt-1 h-4 w-4 rounded border-gray-300"
            />
            <div className="flex-1">
              <label htmlFor="trading_hours_enabled" className="text-sm font-medium cursor-pointer">
                Restrict Trading to Specific Hours
              </label>
              <p className="text-xs text-muted-foreground mt-1">
                Only accept trades during your preferred trading window
              </p>
            </div>
          </div>

          {tradingHours.enabled && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="start_time">Start Time</Label>
                  <Input
                    id="start_time"
                    type="time"
                    value={tradingHours.start_time}
                    onChange={(e) =>
                      handleUpdatePreferences('start_time', e.target.value)
                    }
                    className="mt-1"
                  />
                </div>
                <div>
                  <Label htmlFor="end_time">End Time</Label>
                  <Input
                    id="end_time"
                    type="time"
                    value={tradingHours.end_time}
                    onChange={(e) =>
                      handleUpdatePreferences('end_time', e.target.value)
                    }
                    className="mt-1"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="timezone">Timezone</Label>
                <select
                  id="timezone"
                  value={tradingHours.timezone}
                  onChange={(e) =>
                    handleUpdatePreferences('timezone', e.target.value)
                  }
                  className="mt-1 w-full h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="UTC">UTC</option>
                  <option value="EST">Eastern (EST)</option>
                  <option value="CST">Central (CST)</option>
                  <option value="MST">Mountain (MST)</option>
                  <option value="PST">Pacific (PST)</option>
                  <option value="CET">Central European (CET)</option>
                  <option value="JST">Japan Standard (JST)</option>
                </select>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* API Keys */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            API Keys
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Use API keys to authenticate programmatic requests to TradeMatrix.ai
          </p>

          <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 space-y-2">
            <div className="flex items-center justify-between">
              <code className="text-xs font-mono">
                {showApiKey && apiKey ? apiKey : '••••••••••••••••••••••••••••••••'}
              </code>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded"
                  title={showApiKey ? 'Hide' : 'Show'}
                >
                  {showApiKey ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
                <button
                  type="button"
                  onClick={copyApiKey}
                  className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded"
                  title="Copy to clipboard"
                >
                  <Copy className="h-4 w-4" />
                </button>
              </div>
            </div>
            {copiedKey && (
              <p className="text-xs text-green-600">Copied to clipboard!</p>
            )}
          </div>

          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-xs">
              Keep your API key secret. Never share it or commit it to version control.
            </AlertDescription>
          </Alert>

          <div className="flex gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={regenerateApiKey}
            >
              Regenerate Key
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Change Password */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            Change Password
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <Label htmlFor="new_password">New Password</Label>
              <div className="relative mt-1">
                <Input
                  id="new_password"
                  type={showPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="confirm_password">Confirm Password</Label>
              <Input
                id="confirm_password"
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                className="mt-1"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="show_password"
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300"
              />
              <label htmlFor="show_password" className="text-sm cursor-pointer">
                Show passwords
              </label>
            </div>
            <Button type="submit" disabled={!newPassword || !confirmPassword}>
              Change Password
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

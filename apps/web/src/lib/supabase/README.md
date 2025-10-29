# Supabase Client Integration

This directory contains the Supabase client setup for TradeMatrix.ai Next.js 16 app.

## Files Overview

- **`client.ts`** - Browser client for Client Components
- **`server.ts`** - Server client for Server Components + Admin client
- **`middleware.ts`** - Auth middleware for session management
- **`types.ts`** - TypeScript database types (auto-generated from schema)
- **`index.ts`** - Central export point for all Supabase utilities

## Setup Instructions

### 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Click "New Project"
3. Fill in project details:
   - Name: `tradematrix-dev` (or your preferred name)
   - Database Password: Generate a strong password (save it!)
   - Region: Choose closest to your users
   - Pricing Plan: Free tier is fine for development

### 2. Get API Keys

1. Go to **Settings** > **API**
2. Copy the following values:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public** key (safe for client-side)
   - **service_role** key (NEVER expose to client!)

### 3. Update Environment Variables

Edit `apps/web/.env.local`:

```bash
# Replace with your actual values
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 4. Run Database Migrations

1. Go to **SQL Editor** in Supabase Dashboard
2. Copy contents of `services/api/supabase/migrations/001_initial_schema.sql`
3. Paste and click "Run"
4. Repeat for `002_rls_policies.sql`

### 5. Configure Auth Providers

#### Email/Password Auth

1. Go to **Authentication** > **Providers**
2. Enable **Email** provider
3. Configure settings:
   - Confirm email: ON (recommended)
   - Email templates: Customize if needed

#### Google OAuth (Optional)

1. Create Google OAuth credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create OAuth 2.0 Client ID
   - Add authorized redirect URI: `https://your-project-id.supabase.co/auth/v1/callback`
2. In Supabase Dashboard:
   - Go to **Authentication** > **Providers**
   - Enable **Google**
   - Add Client ID and Client Secret

#### GitHub OAuth (Optional)

1. Create GitHub OAuth App:
   - Go to GitHub **Settings** > **Developer settings** > **OAuth Apps**
   - New OAuth App
   - Authorization callback URL: `https://your-project-id.supabase.co/auth/v1/callback`
2. In Supabase Dashboard:
   - Go to **Authentication** > **Providers**
   - Enable **GitHub**
   - Add Client ID and Client Secret

## Usage Examples

### Server Components (Recommended)

```typescript
import { createServerClient } from '@/lib/supabase/server'

export default async function TradesPage() {
  const supabase = await createServerClient()

  // Get current user
  const { data: { user } } = await supabase.auth.getUser()

  // Query trades
  const { data: trades, error } = await supabase
    .from('trades')
    .select('*')
    .eq('user_id', user?.id)
    .order('created_at', { ascending: false })

  if (error) {
    console.error('Error fetching trades:', error)
    return <div>Error loading trades</div>
  }

  return (
    <div>
      <h1>Your Trades</h1>
      {trades.map(trade => (
        <div key={trade.id}>{trade.symbol}</div>
      ))}
    </div>
  )
}
```

### Client Components

```typescript
'use client'

import { createBrowserClient } from '@/lib/supabase/client'
import { useState, useEffect } from 'react'

export default function ProfileComponent() {
  const [profile, setProfile] = useState(null)
  const supabase = createBrowserClient()

  useEffect(() => {
    async function fetchProfile() {
      const { data: { user } } = await supabase.auth.getUser()

      if (user) {
        const { data } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', user.id)
          .single()

        setProfile(data)
      }
    }

    fetchProfile()
  }, [])

  return (
    <div>
      <h2>Profile</h2>
      <p>Email: {profile?.email}</p>
      <p>Tier: {profile?.subscription_tier}</p>
    </div>
  )
}
```

### Authentication

```typescript
'use client'

import { createBrowserClient } from '@/lib/supabase/client'
import { useState } from 'react'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const supabase = createBrowserClient()

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()

    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })

    if (error) {
      console.error('Login error:', error.message)
    } else {
      // Redirect to dashboard
      window.location.href = '/dashboard'
    }
  }

  async function handleGoogleLogin() {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`
      }
    })

    if (error) {
      console.error('OAuth error:', error.message)
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit">Login</button>
      <button type="button" onClick={handleGoogleLogin}>
        Login with Google
      </button>
    </form>
  )
}
```

### Admin Operations (Server-side only!)

```typescript
import { createAdminClient } from '@/lib/supabase/server'

export async function updateUserSubscription(userId: string, tier: string) {
  // Only use in server-side code (API routes, Server Actions, etc.)
  const supabase = createAdminClient()

  // Bypasses RLS - use carefully!
  const { data, error } = await supabase
    .from('profiles')
    .update({ subscription_tier: tier })
    .eq('id', userId)
    .select()
    .single()

  return { data, error }
}
```

## Type Safety

All queries are fully typed based on your database schema:

```typescript
import { createServerClient } from '@/lib/supabase/server'
import type { Database } from '@/lib/supabase/types'

const supabase = await createServerClient()

// TypeScript knows the shape of trades table
const { data } = await supabase
  .from('trades') // Autocomplete for table names
  .select('symbol, entry_price, pnl') // Autocomplete for columns
  .eq('status', 'open') // Type-safe status values

// data is typed as:
// { symbol: string; entry_price: number; pnl: number | null }[]
```

## Regenerating Types

When you change your database schema:

```bash
# Install Supabase CLI globally
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref your-project-id

# Generate fresh types
supabase gen types typescript --local > src/lib/supabase/types.ts
```

## Authentication Flow

The middleware automatically:
1. Refreshes expired tokens
2. Redirects unauthenticated users from `/dashboard` to `/login`
3. Redirects authenticated users from `/login` to `/dashboard`
4. Maintains session across requests

Protected routes are configured in `apps/web/middleware.ts`.

## Next Steps

1. Create auth pages: `/login`, `/signup`, `/auth/callback`
2. Build dashboard layout with user profile
3. Create trade management UI
4. Implement real-time subscriptions
5. Set up Storage buckets for charts/PDFs
6. Configure RLS policies for data security

## Troubleshooting

### "Invalid API key" error
- Check that env vars are set correctly
- Restart dev server after changing `.env.local`
- Ensure you're using the correct project URL and keys

### "Row Level Security" errors
- Make sure you've run the RLS policies migration
- Check that user is authenticated before querying
- Use `createAdminClient()` if you need to bypass RLS (server-side only)

### Types not matching database
- Regenerate types using Supabase CLI
- Ensure migrations are applied in correct order

## Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Next.js 16 + Supabase Guide](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Supabase Auth](https://supabase.com/docs/guides/auth)

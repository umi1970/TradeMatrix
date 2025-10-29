# Google OAuth Authentication Setup Guide

This guide will walk you through setting up Google OAuth authentication for TradeMatrix.ai using Supabase.

## Prerequisites

- A Supabase project (create one at [supabase.com](https://supabase.com))
- A Google Cloud project (for OAuth credentials)

## 1. Set Up Supabase Project

### Create Supabase Project

✅ **COMPLETED** - Project already created: "tradematrix Projekt"

~~1. Go to [supabase.com](https://supabase.com) and sign in~~
~~2. Click "New Project"~~
~~3. Fill in the project details:~~
   ~~- Name: `tradematrix` (or your preferred name)~~
   ~~- Database Password: Generate a strong password (save it!)~~
   ~~- Region: Choose the closest to your users~~
~~4. Click "Create new project" and wait for setup to complete~~

### Get Supabase Credentials

1. In your Supabase project dashboard, go to **Settings** > **API**
2. Copy the following:
   - **Project URL** (looks like: `https://xxxxx.supabase.co`)
   - **anon public** key
   - **service_role** key (keep this secret!)

### Configure Environment Variables

✅ **COMPLETED** - `.env.local` already configured

~~1. Create a `.env.local` file in `apps/web/`:~~

~~```bash~~
~~# Copy from .env.example~~
~~cp .env.example .env.local~~
~~```~~

~~2. Update the file with your Supabase credentials:~~

~~```env~~
~~NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co~~
~~NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here~~
~~SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here~~
~~```~~

## 2. Run Database Migrations

✅ **COMPLETED** - Migrations already executed

~~1. In your Supabase dashboard, go to **SQL Editor**~~
~~2. Open the migration files in order:~~
   ~~- `services/api/supabase/migrations/001_initial_schema.sql`~~
   ~~- `services/api/supabase/migrations/002_rls_policies.sql`~~
~~3. Copy each file's content and run it in the SQL Editor~~
~~4. Verify tables were created in **Database** > **Tables**~~

## 3. Set Up Google OAuth

### Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google+ API**:
   - Go to **APIs & Services** > **Library**
   - Search for "Google+ API"
   - Click "Enable"

### Create OAuth Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Configure the OAuth consent screen if prompted:
   - User Type: External
   - App name: TradeMatrix.ai
   - User support email: your-email@example.com
   - Developer contact: your-email@example.com
   - Save and continue through the steps
4. Create OAuth Client ID:
   - Application type: **Web application**
   - Name: TradeMatrix.ai
   - Authorized JavaScript origins:
     - `http://localhost:3000` (for development)
     - Your production URL (when deployed)
   - Authorized redirect URIs:
     - `https://htnlhazqzpwfyhnngfsn.supabase.co/auth/v1/callback`
5. Click **Create** and save your:
   - Client ID
   - Client Secret

### Configure Google OAuth in Supabase

1. In Supabase dashboard, go to **Authentication** > **Providers**
2. Find **Google** and click to expand
3. Enable Google provider
4. Enter your Google OAuth credentials:
   - **Client ID**: Paste from Google Cloud Console
   - **Client Secret**: Paste from Google Cloud Console
5. Click **Save**

## 4. Test Authentication

### Start the Development Server

```bash
cd apps/web
npm run dev
```

### Test Google OAuth Flow

1. Open [http://localhost:3000/login](http://localhost:3000/login)
2. Click "Continue with Google"
3. Sign in with your Google account
4. You should be redirected to `/dashboard`
5. Verify your user info is displayed

### Test Email/Password Flow

1. Go to [http://localhost:3000/signup](http://localhost:3000/signup)
2. Enter an email and password
3. Check your email for confirmation (if email confirmation is enabled)
4. Sign in at [http://localhost:3000/login](http://localhost:3000/login)
5. Verify access to `/dashboard`

## 5. Optional: Configure Additional Providers

### GitHub OAuth (Optional)

1. Go to GitHub Settings > Developer settings > OAuth Apps
2. Create a new OAuth App:
   - Application name: TradeMatrix.ai
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `https://your-project-id.supabase.co/auth/v1/callback`
3. Copy Client ID and Client Secret
4. In Supabase dashboard, go to **Authentication** > **Providers**
5. Enable GitHub and add your credentials

## 6. Production Deployment

### Update OAuth Redirect URIs

When deploying to production (e.g., Vercel):

1. Add your production URL to Google Cloud Console:
   - Authorized JavaScript origins: `https://yourdomain.com`
   - Authorized redirect URIs: Keep the Supabase callback URL
2. Update environment variables in your hosting platform
3. No changes needed in Supabase (redirect URL stays the same)

### Environment Variables for Production

Set these in your hosting platform (e.g., Vercel):

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
```

## Troubleshooting

### "redirect_uri_mismatch" Error

- Verify the redirect URI in Google Cloud Console exactly matches:
  `https://your-project-id.supabase.co/auth/v1/callback`
- Check for trailing slashes or typos

### "Invalid login credentials" Error

- Verify your Supabase credentials in `.env.local`
- Make sure you're using the correct anon key (not service_role key for client)

### Middleware Not Protecting Routes

- Verify `middleware.ts` is in the root of `apps/web/` (not in `src/`)
- Check the matcher config in middleware
- Restart the dev server

### Email Confirmation Not Sending

- In Supabase dashboard, go to **Authentication** > **Settings**
- Check "Enable email confirmations" setting
- Configure email templates if needed

## File Structure

```
apps/web/
├── src/
│   ├── app/
│   │   ├── login/
│   │   │   └── page.tsx          # Login page
│   │   ├── signup/
│   │   │   └── page.tsx          # Signup page
│   │   ├── auth/
│   │   │   └── callback/
│   │   │       └── route.ts      # OAuth callback handler
│   │   └── dashboard/
│   │       └── page.tsx          # Protected dashboard
│   ├── components/
│   │   └── auth/
│   │       ├── GoogleSignInButton.tsx
│   │       ├── SignOutButton.tsx
│   │       └── AuthForm.tsx
│   └── lib/
│       ├── supabase/
│       │   ├── client.ts         # Browser client
│       │   ├── server.ts         # Server client
│       │   ├── middleware.ts     # Middleware client
│       │   └── types.ts          # Database types
│       └── auth/
│           ├── utils.ts          # Auth utilities
│           └── types.ts          # Auth types
├── middleware.ts                 # Route protection
└── .env.local                    # Environment variables
```

## Next Steps

1. Customize the login/signup pages with your branding
2. Add password reset functionality
3. Implement user profile management
4. Set up subscription tiers with Stripe
5. Build your trading features

## Resources

- [Supabase Auth Documentation](https://supabase.com/docs/guides/auth)
- [Next.js 15 Documentation](https://nextjs.org/docs)
- [Google OAuth Documentation](https://developers.google.com/identity/protocols/oauth2)

# Quick Testing Guide

**Status:** ✅ Email/Password tested and working | ⏳ Google OAuth ready (needs config)
**Last Updated:** 2025-10-26

## How to Test Authentication

### Prerequisites Checklist

**Completed:**
1. ✅ Supabase project created ("tradematrix Projekt")
2. ✅ Database migrations run in Supabase SQL Editor
3. ✅ Environment variables added to `.env.local`

**For Google OAuth (Optional):**
4. ⏳ Google OAuth credentials from [Google Cloud Console](https://console.cloud.google.com/)
5. ⏳ Google OAuth configured in Supabase dashboard

**Recommended:** Start with Email/Password testing (works now!), add Google OAuth later.

If you need Google OAuth setup, see `AUTH_SETUP.md` for detailed instructions.

---

## Step-by-Step Testing

### 1. Start the Development Server

```bash
cd apps/web
npm run dev
```

Server should start at [http://localhost:3000](http://localhost:3000) (or 3001 if 3000 is busy)

### 2. Test Email/Password Authentication (Recommended First!)

**✅ TESTED AND WORKING**

1. **Create Account (Signup)**
   - Navigate to: [http://localhost:3000/signup](http://localhost:3000/signup) (or 3001)
   - Enter email and password (min 6 chars)
   - Click "Create account"
   - **Note:** Email confirmation link may expire quickly - manually confirm user in Supabase if needed

2. **Login**
   - Navigate to: [http://localhost:3000/login](http://localhost:3000/login)
   - Enter your email and password
   - Click "Sign in"
   - Should redirect to `/dashboard`

3. **Verify Dashboard Access**
   - Dashboard should display:
     - Your email address
     - User ID
     - "Sign Out" button

4. **Test Sign Out**
   - Click "Sign Out"
   - Should redirect to `/login`
   - Try accessing `/dashboard` - should redirect back to login

### 3. Test Google OAuth Login (Optional - Needs Configuration)

⏳ **Not yet configured** - See `AUTH_SETUP.md` Section 3 for Google OAuth setup

Once configured:
1. Click "Continue with Google" on login page
2. Sign in with Google account
3. Should redirect to `/dashboard`

### 4. Test Protected Routes

1. **Try Accessing Dashboard While Logged Out**
   - Sign out if currently signed in
   - Try to navigate to: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
   - Should automatically redirect to `/login`
   - URL should show: `/login?redirectTo=/dashboard`

2. **Try Accessing Login While Logged In**
   - Sign in if not already signed in
   - Try to navigate to: [http://localhost:3000/login](http://localhost:3000/login)
   - Should automatically redirect to `/dashboard`

---

## Expected Behavior

### ✅ Success Cases

| Action | Expected Result |
|--------|----------------|
| Click Google sign-in | Redirects to Google OAuth |
| Complete Google OAuth | Redirects to `/dashboard` |
| Sign up with email | Creates account and redirects to `/dashboard` |
| Sign in with email | Redirects to `/dashboard` |
| Access `/dashboard` (logged in) | Shows dashboard with user info |
| Click "Sign Out" | Redirects to `/login` |
| Access `/login` (logged in) | Redirects to `/dashboard` |
| Access `/dashboard` (logged out) | Redirects to `/login` |

### ❌ Error Cases to Test

| Action | Expected Result |
|--------|----------------|
| Sign in with wrong password | Error message displayed |
| Sign up with existing email | Error message displayed |
| Sign up with weak password | Validation error or Supabase error |
| Invalid email format | HTML5 validation error |

---

## Debugging Tips

### Check Browser Console

Open DevTools (F12) and check Console tab for:
- JavaScript errors
- Network requests to Supabase
- Auth state changes

### Check Network Tab

In DevTools Network tab, look for:
- POST requests to Supabase Auth endpoints
- Response status codes (200 = success, 400 = error)
- Response bodies for error messages

### Check Supabase Dashboard

1. **Auth Users**
   - Go to: Authentication > Users
   - Verify new users appear after signup
   - Check user metadata and provider info

2. **Auth Logs**
   - Go to: Authentication > Logs
   - Check for authentication events
   - Look for errors or warnings

3. **Database**
   - Go to: Database > Tables
   - Check if `profiles` table exists
   - Verify profile records are created (if trigger is set up)

### Common Issues & Solutions

#### "redirect_uri_mismatch"

**Problem:** Google OAuth redirect URL doesn't match

**Solution:**
1. Check Google Cloud Console > Credentials
2. Verify redirect URI is: `https://your-project-id.supabase.co/auth/v1/callback`
3. Make sure there are no trailing slashes
4. Save changes and wait a few minutes

#### "Invalid login credentials"

**Problem:** Wrong email or password

**Solution:**
1. Verify email is correct
2. Check password (Supabase requires min 6 characters by default)
3. Try resetting password if forgot

#### Session not persisting

**Problem:** Getting logged out on refresh

**Solution:**
1. Check `.env.local` has correct Supabase credentials
2. Verify middleware is working (check `middleware.ts` at root)
3. Clear browser cookies and try again
4. Check Supabase project settings for session timeout

#### Middleware not redirecting

**Problem:** Can access protected routes when logged out

**Solution:**
1. Verify `middleware.ts` is at root of `apps/web/` (not in `src/`)
2. Check middleware matcher config
3. Restart dev server: `npm run dev`
4. Clear Next.js cache: `rm -rf .next`

#### TypeScript errors

**Problem:** Red squiggly lines in VSCode

**Solution:**
1. Run type check: `npm run type-check`
2. Restart TypeScript server in VSCode
3. Check `tsconfig.json` has correct paths

---

## Verifying Everything Works

### Checklist

After testing, verify:

- [ ] Can sign in with Google OAuth
- [ ] Can sign up with email/password
- [ ] Can sign in with email/password
- [ ] Can sign out successfully
- [ ] Dashboard shows correct user info
- [ ] Protected routes redirect when logged out
- [ ] Auth pages redirect when logged in
- [ ] No TypeScript errors (`npm run type-check`)
- [ ] No console errors in browser
- [ ] Users appear in Supabase Auth dashboard

---

## Next: Customize & Extend

Once authentication works, you can:

1. **Customize UI**
   - Update login/signup page styling
   - Add your logo and branding
   - Modify color scheme

2. **Add Features**
   - Password reset functionality
   - Profile management page
   - Avatar upload
   - Email change

3. **Add More Providers**
   - GitHub OAuth
   - Microsoft OAuth
   - Apple Sign In

4. **Integrate with App**
   - Add subscription tier checks
   - Build trading features
   - Connect to Stripe
   - Add AI agent access control

---

## Getting Help

If you encounter issues:

1. Check `AUTH_SETUP.md` for setup instructions
2. Review Supabase docs: [supabase.com/docs](https://supabase.com/docs)
3. Check Next.js docs: [nextjs.org/docs](https://nextjs.org/docs)
4. Search for error messages in Supabase Discord or GitHub issues

---

**Happy Testing! 🚀**

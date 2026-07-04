# Deployment Guide for SkoolPlannr Web

## What's Been Done

✅ Flutter web app built successfully for production
✅ Build output located at: `build/web/`
✅ Vercel configuration file created: `vercel.json`
✅ API base URL configured: `https://699cb5430037a8a18f1c.sgp.appwrite.run/`
✅ Vercel project already linked (Project ID: prj_YuiVR3vFqcgQjU6JQuQ1qiKA5xt4)

## Quick Deploy Options

### Option 1: Using Vercel CLI (Recommended)

```bash
# Navigate to the flutter directory
cd /Users/soham/Library/CloudStorage/OneDrive-Personal/Code/School-Planner/frontend/flutter

# Deploy to production
npx vercel deploy build/web --prod
```

### Option 2: Using Vercel Web Interface

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Find your project or click "Add New" > "Project"
3. Upload the `build/web` folder or connect your Git repository
4. Vercel will automatically detect the configuration from `vercel.json`

### Option 3: Using Vercel CLI (After Global Install)

```bash
# Install Vercel CLI globally (one-time setup)
npm install -g vercel

# Navigate to flutter directory
cd /Users/soham/Library/CloudStorage/OneDrive-Personal/Code/School-Planner/frontend/flutter

# Deploy
vercel deploy build/web --prod
```

## Rebuilding for Web

If you need to rebuild the app:

```bash
cd /Users/soham/Library/CloudStorage/OneDrive-Personal/Code/School-Planner/frontend/flutter
flutter build web --release --dart-define=API_BASE_URL=https://699cb5430037a8a18f1c.sgp.appwrite.run/
```

## vercel.json Configuration

The `vercel.json` file has been created with:
- SPA routing (all routes redirect to index.html)
- Cache headers for static assets
- Optimized for Flutter web apps

## Environment Variables

The API base URL is compiled into the app during build:
- `API_BASE_URL=https://699cb5430037a8a18f1c.sgp.appwrite.run/`

If you need to change this, rebuild the app with a different value for the `--dart-define` flag.

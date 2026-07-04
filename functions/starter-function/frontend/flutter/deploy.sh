#!/bin/bash

# Deploy Flutter web app to Vercel
# This script builds the Flutter web app and deploys it to Vercel

echo "Building Flutter web app..."
cd /Users/soham/Library/CloudStorage/OneDrive-Personal/Code/School-Planner/frontend/flutter

# Build the web app
flutter build web --release --dart-define=API_BASE_URL=https://699cb5430037a8a18f1c.sgp.appwrite.run/

echo "Build complete!"
echo ""
echo "To deploy to Vercel, run the following command:"
echo "cd /Users/soham/Library/CloudStorage/OneDrive-Personal/Code/School-Planner/frontend/flutter"
echo "npx vercel deploy build/web --prod"
echo ""
echo "Alternatively, you can:"
echo "1. Install Vercel CLI: npm install -g vercel"
echo "2. Login to Vercel: vercel login"
echo "3. Deploy: vercel deploy build/web --prod"
echo ""
echo "Or use the Vercel web interface:"
echo "1. Go to https://vercel.com"
echo "2. Import your project or drag & drop the build/web folder"

# 🚀 Deployment Guide - MembershipPro Platform

This guide covers how to deploy the MembershipPro membership platform both locally for development and online for production use.

## 📋 Prerequisites

Before deploying, ensure you have:
- Node.js 18+ installed
- npm or yarn package manager
- Git (for version control)
- A database (PostgreSQL recommended for production)

## 🏠 Local Development Deployment

### Step 1: Clone or Download the Project

**Option A: Using the v0 Download**
1. Click the "Download Code" button in the v0 interface
2. Extract the downloaded ZIP file
3. Navigate to the project directory

**Option B: Manual Setup**
1. Create a new directory: `mkdir membership-platform`
2. Copy all the provided files into the directory
3. Ensure the file structure matches the project layout

### Step 2: Install Dependencies

\`\`\`bash
cd membership-platform
npm install
\`\`\`

**Key Dependencies Installed:**
- Next.js 14 (React framework)
- Tailwind CSS (styling)
- shadcn/ui (UI components)
- Lucide React (icons)
- TypeScript (type safety)

### Step 3: Set Up the Database

**Option A: Using PostgreSQL (Recommended)**
\`\`\`bash
# Install PostgreSQL locally
# Create a new database
createdb membership_platform

# Run the SQL scripts
psql -d membership_platform -f scripts/01-create-tables.sql
psql -d membership_platform -f scripts/02-seed-data.sql
\`\`\`

**Option B: Using SQLite (Development)**
\`\`\`bash
# Install sqlite3
npm install sqlite3

# Create database and run scripts
sqlite3 membership.db < scripts/01-create-tables.sql
sqlite3 membership.db < scripts/02-seed-data.sql
\`\`\`

### Step 4: Environment Configuration

Create a `.env.local` file in the root directory:

\`\`\`env
# Database Configuration
DATABASE_URL="postgresql://username:password@localhost:5432/membership_platform"
# or for SQLite:
# DATABASE_URL="file:./membership.db"

# App Configuration
NEXTAUTH_SECRET="your-secret-key-here"
NEXTAUTH_URL="http://localhost:3000"

# DigiLocker API (for production integration)
DIGILOCKER_CLIENT_ID="your-digilocker-client-id"
DIGILOCKER_CLIENT_SECRET="your-digilocker-client-secret"
DIGILOCKER_REDIRECT_URI="http://localhost:3000/api/digilocker/callback"
\`\`\`

### Step 5: Start Development Server

\`\`\`bash
npm run dev
\`\`\`

The application will be available at: `http://localhost:3000`

### Step 6: Test the Application

**Demo Accounts:**
- **Admin**: admin@example.com / password123
- **User**: user@example.com / password123

**Test Flow:**
1. Visit the homepage
2. Sign up for a new account
3. Complete the DigiLocker verification simulation
4. Explore the user dashboard
5. Login as admin to test event management

## 🌐 Online Production Deployment

### Option 1: Deploy to Vercel (Recommended)

Vercel is the easiest option since it's built by the Next.js team.

#### Step 1: Prepare for Deployment

\`\`\`bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login
\`\`\`

#### Step 2: Database Setup

**Using Vercel Postgres:**
\`\`\`bash
# Add Vercel Postgres to your project
vercel postgres create membership-db

# Get connection string
vercel env pull .env.local
\`\`\`

**Using External Database (Supabase/PlanetScale):**
1. Create a database on your preferred provider
2. Run the SQL scripts to set up tables
3. Add the connection string to environment variables

#### Step 3: Configure Environment Variables

\`\`\`bash
# Set production environment variables
vercel env add DATABASE_URL
vercel env add NEXTAUTH_SECRET
vercel env add NEXTAUTH_URL
\`\`\`

#### Step 4: Deploy

\`\`\`bash
# Deploy to Vercel
vercel --prod
\`\`\`

**Automatic Deployment:**
1. Push your code to GitHub
2. Connect your GitHub repo to Vercel
3. Vercel will automatically deploy on every push

### Option 2: Deploy to Netlify

#### Step 1: Build Configuration

Create `netlify.toml`:

\`\`\`toml
[build]
  command = "npm run build"
  publish = ".next"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
\`\`\`

#### Step 2: Deploy

\`\`\`bash
# Install Netlify CLI
npm install -g netlify-cli

# Login and deploy
netlify login
netlify deploy --prod --dir=.next
\`\`\`

### Option 3: Deploy to Railway

#### Step 1: Install Railway CLI

\`\`\`bash
npm install -g @railway/cli
railway login
\`\`\`

#### Step 2: Initialize and Deploy

\`\`\`bash
railway init
railway add postgresql
railway deploy
\`\`\`

### Option 4: Deploy to DigitalOcean App Platform

#### Step 1: Create App Spec

Create `.do/app.yaml`:

\`\`\`yaml
name: membership-platform
services:
- name: web
  source_dir: /
  github:
    repo: your-username/membership-platform
    branch: main
  run_command: npm start
  environment_slug: node-js
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: DATABASE_URL
    scope: RUN_TIME
    type: SECRET
databases:
- engine: PG
  name: membership-db
  num_nodes: 1
  size: basic-xs
  version: "14"
\`\`\`

#### Step 2: Deploy

\`\`\`bash
doctl apps create --spec .do/app.yaml
\`\`\`

## 🗄️ Database Migration for Production

### Step 1: Set Up Production Database

**PostgreSQL on Cloud:**
\`\`\`sql
-- Connect to your production database
-- Run the table creation script
\i scripts/01-create-tables.sql

-- Optionally run seed data (remove for production)
-- \i scripts/02-seed-data.sql
\`\`\`

### Step 2: Database Connection

Update your production environment variables:

\`\`\`env
DATABASE_URL="postgresql://user:password@host:port/database?sslmode=require"
\`\`\`

## 🔒 Security Configuration for Production

### Step 1: Environment Variables

\`\`\`env
# Strong secret for JWT tokens
NEXTAUTH_SECRET="your-very-long-random-secret-key"

# Production URL
NEXTAUTH_URL="https://your-domain.com"

# Database with SSL
DATABASE_URL="postgresql://user:pass@host:port/db?sslmode=require"

# DigiLocker Production Credentials
DIGILOCKER_CLIENT_ID="production-client-id"
DIGILOCKER_CLIENT_SECRET="production-client-secret"
DIGILOCKER_REDIRECT_URI="https://your-domain.com/api/digilocker/callback"
\`\`\`

### Step 2: Security Headers

Add to `next.config.mjs`:

\`\`\`javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ]
  },
}

export default nextConfig
\`\`\`

## 📊 Monitoring and Analytics

### Step 1: Add Vercel Analytics

\`\`\`bash
npm install @vercel/analytics
\`\`\`

Add to `app/layout.tsx`:

\`\`\`tsx
import { Analytics } from '@vercel/analytics/react'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  )
}
\`\`\`

### Step 2: Error Monitoring

\`\`\`bash
npm install @sentry/nextjs
\`\`\`

## 🔧 Troubleshooting

### Common Issues

**1. Database Connection Errors**
\`\`\`bash
# Check connection string format
# Ensure database is accessible
# Verify SSL requirements
\`\`\`

**2. Build Failures**
\`\`\`bash
# Clear Next.js cache
rm -rf .next
npm run build
\`\`\`

**3. Environment Variable Issues**
\`\`\`bash
# Verify all required env vars are set
# Check for typos in variable names
# Ensure proper escaping of special characters
\`\`\`

### Performance Optimization

**1. Enable Compression**
\`\`\`javascript
// next.config.mjs
const nextConfig = {
  compress: true,
  poweredByHeader: false,
}
\`\`\`

**2. Optimize Images**
\`\`\`javascript
// next.config.mjs
const nextConfig = {
  images: {
    domains: ['your-domain.com'],
    formats: ['image/webp', 'image/avif'],
  },
}
\`\`\`

## 📈 Scaling Considerations

### Database Scaling
- Use connection pooling (PgBouncer)
- Implement read replicas for heavy read workloads
- Consider database sharding for large user bases

### Application Scaling
- Use CDN for static assets
- Implement Redis for session storage
- Consider serverless functions for API routes

### Monitoring
- Set up uptime monitoring
- Implement application performance monitoring (APM)
- Configure log aggregation

## 🚀 Going Live Checklist

- [ ] Database is set up and migrated
- [ ] All environment variables are configured
- [ ] SSL certificate is installed
- [ ] Domain is configured
- [ ] Error monitoring is set up
- [ ] Analytics are configured
- [ ] Backup strategy is implemented
- [ ] Security headers are configured
- [ ] Performance is optimized
- [ ] Testing is completed

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review the platform-specific documentation
3. Check the GitHub issues for common problems
4. Contact support through the respective platform

---

**Happy Deploying! 🎉**

Your MembershipPro platform is now ready to serve users with secure identity verification and event management capabilities.

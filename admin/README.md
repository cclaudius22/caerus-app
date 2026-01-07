# Caerus Admin Panel

Admin dashboard for managing users and platform data.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` file with your Firebase config:
```bash
cp .env.example .env.local
# Edit .env.local with your Firebase credentials
```

3. Run development server:
```bash
npm run dev
```

Admin panel runs on http://localhost:3001

## Deploy to Vercel

1. Push to GitHub
2. Import project in Vercel
3. Add environment variables in Vercel dashboard
4. Deploy

## Admin Access

Admin access is granted to users with `@caerus.app` email addresses. The email is checked during Firebase authentication.

## Features

- **Dashboard**: Overview stats (users, pending approvals)
- **Founders**: List all founders with search
- **Investors**: List all investors with search
- **Talent**: List all talent with status filter, approve/reject actions

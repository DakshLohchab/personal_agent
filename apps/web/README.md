# Life Sandbox web

This is the Phase 6 Next.js App Router frontend. It is presentation and API
orchestration only: simulation mathematics and agent orchestration remain in
the backend.

## Local development

```bash
cd apps/web
npm install
cp .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` to the backend URL. No provider, database,
storage, or research credentials belong in this application.

## Checks

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

For Vercel, configure `NEXT_PUBLIC_API_BASE_URL` as the only required
environment variable. Phase 7 memory UX and later deployment hardening remain
intentionally deferred.

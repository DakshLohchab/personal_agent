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

By default, browser requests use the same-origin `/api` route and Next.js
forwards them to FastAPI at `http://127.0.0.1:8000`. Set `INTERNAL_API_URL`
when the backend is hosted elsewhere. `NEXT_PUBLIC_API_BASE_URL` is optional
for deployments where the browser should call the API directly; in that setup,
configure the backend CORS allowlist for the frontend origin. No provider,
database, storage, or research credentials belong in this application.

## Checks

```bash
npm run typecheck
npm run lint
npm test
npm run build
```

For Vercel, configure `INTERNAL_API_URL` to the deployed FastAPI origin so
browser requests can remain same-origin through the Next.js rewrite. Use
`NEXT_PUBLIC_API_BASE_URL` only when direct browser-to-API access is intended.

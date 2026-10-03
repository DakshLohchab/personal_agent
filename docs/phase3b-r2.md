# Phase 3B: private R2 file storage

## Bucket setup

Create a private Cloudflare R2 bucket and an API token restricted to that bucket.
Set `R2_ENDPOINT_URL` to the S3-compatible endpoint
(`https://<account-id>.r2.cloudflarestorage.com`). Do not enable public bucket
access.

## Environment variables

* `R2_ACCOUNT_ID`
* `R2_BUCKET`
* `R2_ACCESS_KEY_ID`
* `R2_SECRET_ACCESS_KEY`
* `R2_ENDPOINT_URL`
* `R2_PRESIGN_TTL_SECONDS` (default 300)
* `R2_MAX_UPLOAD_BYTES` (default 52428800)

Credentials are server-only. They are never returned by the API or written to
logs.

## Object keys and flow

The server sanitizes the client filename and generates a UUID-backed key:

`users/{user_id}/files/{file_id}/{safe_filename}`

The upload URL endpoint creates a `pending` metadata row and returns a
short-lived presigned PUT URL signed for the expected MIME type. The client
uploads directly to R2; FastAPI never proxies file bytes. Completion performs
an R2 HEAD request and verifies size and (when returned) content type before
marking the row `uploaded`.

Download requests verify ownership and return a short-lived presigned GET URL.
Deletion removes the object first and then marks the metadata row `deleted`.

## Security rules

Only signed URLs are exposed. They are bearer tokens and should be treated as
secrets. Never log signed URLs, object-store credentials, or make the bucket
public. Ownership is enforced by the authenticated user-scoped repository and
the database RLS policies.

## Local test strategy

Use `services.storage.fake.FakeObjectStore` in API tests. Tests can call
`put_object` to simulate a completed direct upload and verify the HEAD,
ownership, size, MIME, download, and deletion flows without Cloudflare. R2
adapter tests inject a mocked boto3 client; CI does not require R2 credentials.

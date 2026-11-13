# CLUTCH-X deployment and operations

## Selected hosting targets

- **Frontend:** Cloudflare Pages, built from `frontend/`.
- **API and analytics store:** Railway, built from the root `Dockerfile`.
- **Analytics database:** DuckDB generated during the Docker image build. No
  external database service or runtime source-data volume is required.

The browser calls the Railway API directly; configure CORS with the exact
Cloudflare Pages origin(s).

## Required configuration

| Service | Variable | Value |
|---|---|---|
| Cloudflare Pages | `VITE_API_BASE_URL` | `https://<railway-service-domain>/api/v1` |
| Railway | `CLUTCH_X_DB` | `/data/clutch_x.duckdb` (already the image default) |
| Railway | `CLUTCH_X_CORS_ORIGINS` | Comma-separated Pages production and approved preview origins |
| Railway | `PORT` | Leave to Railway; the container reads its assigned port and falls back to `8000` locally |

Do not add trailing slashes to the API base path. The frontend appends route
paths to this value. Avoid wildcard CORS origins; include only origins that
serve the dashboard.

## First deployment

1. Keep all six required CSVs under `Data Pack/` in the Docker build context.
   The build validates them and regenerates the complete processed dataset,
   audit artifacts, and DuckDB store.
2. Push the workflow and project to GitHub and wait for CI. Configure Railway
   to build the repository root with its included `Dockerfile`; set the
   Railway variables above and use the Railway-assigned port.
3. Configure the Railway health check to call
   `GET /api/v1/overview`. Confirm it returns HTTP 200 after the image build.
4. Create a Cloudflare Pages project from the same repository with root
   directory `frontend`, build command `npm ci && npm run build`, and output
   directory `dist`. Set `VITE_API_BASE_URL` for each environment and add each
   served origin to Railway's `CLUTCH_X_CORS_ORIGINS`.
5. Open the Pages URL and verify the overview, both leaderboard disciplines,
   filters, and API responses. Promote a release only after reviewing the
   analytics gate and the generated report.

## Rebuild and release

Changes to `Data Pack/`, ETL code, or API code require a new Railway image
build; the Dockerfile repeats validation and ETL and places the resulting
database in the runtime image. Frontend-only changes require a Cloudflare
Pages rebuild. A dataset update therefore changes the API data only when the
new image is deployed. Keep the GitHub Actions checks enabled and review the
ranking audit output before promotion.

For local operation:

```sh
docker build -t clutch-x-api:local .
docker run --rm -p 8000:8000 clutch-x-api:local
curl --fail http://127.0.0.1:8000/api/v1/overview
```

Set `PORT` when running the image on a non-default local port. Set
`CLUTCH_X_CORS_ORIGINS` to the exact local frontend origin if the dashboard
uses a non-default host or port.

## Data handling and operational limitations

- The builder stage needs the CSVs, but the final runtime image contains only
  the generated DuckDB database. The source data is not copied into the final
  stage. The build context and any remote builder cache still receive the
  source files, so confirm their sharing and retention are permitted by the
  data license and repository access policy.
- The database is generated into the image and is not mutable state. To change
  the dataset, rebuild and redeploy; no persistent database volume is needed.
- The image exposes read-only analytics endpoints without authentication.
  Keep the source repository and deployment controls access-restricted as
  required, and do not add private or user-identifying data to the source pack.
- The current data misses the PRD split-half stability requirement:
  batting rho is 0.1985 and bowling rho is 0.3317 against a 0.65 target.
  Docker deliberately keeps the exploratory API available while CI reports
  this acceptance failure. Do not describe the rankings as validated stable
  rankings or bypass the gate to promote them as such.
- This guide documents deployment configuration; it does not provision
  Cloudflare or Railway accounts, connect credentials, or deploy a live
  service.

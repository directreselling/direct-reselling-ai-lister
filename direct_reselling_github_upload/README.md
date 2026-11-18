# Direct Reselling AI Lister — first working foundation

This is an **early prototype**, not a finished AI lister or a live eBay publisher.

## What works in the code
- Account login using Django's built-in authentication.
- Multi-photo batch upload, with each photo initially assigned a separate SKU.
- Manual regrouping of photos into garment/item groups.
- Editable draft fields, price and purchase cost.
- 80-character title generator from user-entered fields.
- Approve draft (does NOT publish).
- SQLite local development and PostgreSQL Docker configuration.

## Not implemented yet
AI image recognition, automatic photo grouping, AI-generated item specifics, verified
sold-comparable pricing, eBay OAuth/API publishing, bulk publish, cloud deployment,
storage hardening, production monitoring, robust upload retries and cost reporting.
Do not treat approved drafts as published.

## Local start (Python 3.12+)
1. Create a virtual environment: `python -m venv .venv`
2. Activate it and run `pip install -r requirements.txt`
3. Run `python manage.py migrate`
4. Run `python manage.py createsuperuser`
5. Run `python manage.py runserver`
6. Visit `http://127.0.0.1:8000` and sign in.

## Docker (local development only)
Create `.env` from `.env.example`, add a strong `DJANGO_SECRET_KEY` and
`POSTGRES_PASSWORD`, then run `docker compose up --build`.
Run `docker compose exec web python manage.py createsuperuser`.
Visit `http://127.0.0.1:8000`.

**Security:** Do not expose this prototype to the public internet. Add HTTPS,
proper image delivery/access controls, virus scanning, upload limits at the proxy,
CSRF/host configuration, backups, secret management and production checks first.
Media serving currently works only in DEBUG mode. The upload endpoint needs
friendlier error handling and stricter resource protection before deployment.

## Suggested next development milestone
Replace manual photo grouping with an AI-assisted suggestion queue, retain
manual override, add image-based draft generation, and implement eBay OAuth
sandbox integration with explicit user confirmation before any live publish.

## Safety improvements in this revision
- Validates all uploaded images before creating a batch; malformed files return HTTP 400.
- Prevents manual grouping beyond 15 photos per item.
- Removes automatic migrations from the web container startup command. Before starting a fresh Docker installation, run `docker compose run --rm web python manage.py migrate` after starting the database. For an existing installation, first take and verify database/media backups and rehearse restoration. Do not deploy this revision without doing so.
- Adds regression tests for malformed upload and the 15-photo grouping limit.

**Verification status:** Python syntax was checked, but Django dependencies are not installed in the build environment, so Django tests, migrations, Docker startup, and mobile browser acceptance tests remain unverified. The prototype is not production ready.

## AI draft milestone (new)
Set `OPENAI_API_KEY` as a private server environment variable and optionally set `OPENAI_MODEL` (default `gpt-4.1-mini`). Do not commit the key. On an item edit page, select up to 10 images and choose **Generate AI draft**. The server sends resized copies to OpenAI's Responses API; original images remain unchanged. Results populate the editable draft and editable item aspects, with evidence notes for review. AI generation never publishes to eBay. User-entered brand, item type, department, size and colour take priority. The system does not validate suggestions against eBay's live category-specific requirements yet. Review all details, particularly condition, before approval.

A Django initial migration is now included. If an older installation already has database tables created without migration records, do not apply this initial migration blindly: back up and reconcile the migration history first. Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`, and `python manage.py test` before deploying. API calls incur usage charges.

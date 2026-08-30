# Padel availability agenda

A backend-less way to display MongoDB padel court availabilities to users. There is
no server answering live requests — a script periodically exports MongoDB into a
static JSON file, and the frontend just fetches that file.

```
padel-agenda/
├── export/                  # runs on a schedule, not continuously
│   ├── export.js            # queries MongoDB, writes frontend/availabilities.json
│   ├── package.json
│   └── .env.example
├── frontend/                 # this whole folder is what you deploy
│   ├── index.html            # the agenda UI (fetches availabilities.json)
│   └── availabilities.json   # sample data — replace by running the export
└── .github/workflows/export.yml   # optional: schedules the export for free
```

## 1. Try it immediately

`frontend/availabilities.json` already contains sample data, so you can open
`frontend/index.html` directly in a browser (or serve the folder with any static
file server) and see the agenda working before touching MongoDB at all.

## 2. Wire up your real data

1. `cd export && cp .env.example .env` and fill in your `MONGODB_URI`, `DB_NAME`,
   and `COLLECTION_NAME`.
2. Open `export/export.js` and edit the `mapDocument` function so its field names
   match your actual documents (I guessed `city`, `region`, `club`, `court`,
   `startTime`, `durationMinutes` based on your description — adjust as needed).
3. `npm install` then `npm run export`. This overwrites
   `frontend/availabilities.json` with your real data.

## 3. Deploy the frontend

The `frontend/` folder is a fully static site — one HTML file plus one JSON file.
Any static host works: drag-and-drop the folder into Netlify, connect the repo to
Vercel, or enable GitHub Pages on it. No server configuration needed.

## 4. Keep the data fresh

You need the export to re-run periodically so the JSON doesn't go stale. Two easy
options:

- **GitHub Actions (free, included)** — `.github/workflows/export.yml` runs the
  export every 10 minutes and commits the updated JSON. Add your connection
  string as a repository secret named `MONGODB_URI` (Settings → Secrets and
  variables → Actions). Each commit will trigger your static host's auto-deploy,
  so the site stays current with no server to maintain.
- **Any other cron** — a scheduled task on a small VM, a scheduled cloud
  function, or your existing infra, running `node export/export.js` on whatever
  cadence matches how often availability actually changes.

## When you'd outgrow this

If availability ever needs to reflect a booking within seconds (rather than
minutes), swap the export script for a single read-only API endpoint (a small
serverless function using the MongoDB driver) and change `DATA_URL` in
`index.html` to point at it instead of the static file. The frontend code barely
changes — it's still just a `fetch()` call.

 # PadelBot Web

PadelBot Web is the static web front for displaying padel court availability in
La Reunion. The browser does not call MongoDB and there is no live application
server: a Python export job reads the source data, writes JSON files into
`docs/`, and the static page reads those files.

## Architecture

The repository has two runtime parts:

- `src/` contains the Python exporter. `src/main.py` runs the three exports in
	sequence through `src.export.exporter.Exporter`.
- `docs/` is the deployable static site. `docs/index.html` contains the French
	availability and booking UI, and `docs/mentions-legales.html` contains the
	legal notice.

The exporter connects to the configured MongoDB database through the async
MongoDB client in `src/configs/mongo_client.py`. It produces these files:

- `docs/availabilities.json` contains future availability slots. Results are
	deduplicated by club, court, date, and time, keeping the latest scrape. Slots
	whose end is less than 30 minutes away are removed.
- `docs/scrape_runs.json` contains the latest scrape status for each club and
	availability date. The page uses this to show freshness and to avoid showing
	availability for a failed scrape.
- `docs/meteo_runs.json` contains the latest weather model run for each club.
	The page matches the forecast to slot times and displays weather information
	where available.

Each JSON document also includes a UTC `generatedAt` timestamp. The frontend
fetches the three files with caching disabled, then provides:

- day tabs for the available dates;
- city, club, time-period, and duration filters;
- availability cards showing the time, club, court, duration, and weather;
- a booking view with the configured club web, iOS, and Android links;
- scrape freshness/status information and the application version from
	`docs/VERSION`.

## Local development

The project requires Python 3.13 or newer and uses `uv` for dependency
management.

Create `.devcontainer/devcontainer.env` with the settings consumed by
`src/configs/settings.py`:

```text
AVAILABILITIES_OUTPUT_PATH=docs/availabilities.json
SCRAPE_RUNS_OUTPUT_PATH=docs/scrape_runs.json
METEO_RUNS_OUTPUT_PATH=docs/meteo_runs.json
MDB_USER=...
MDB_PASSWORD=...
DB_NAME=...
COLLECTION_NAME=...
TIMEZONE=...
```

Install dependencies and run the exporter:

```sh
uv sync
make export
```

The exporter needs network access to the configured MongoDB Atlas cluster. It
overwrites the three JSON files in `docs/`.

To inspect the static frontend locally, serve `docs/` over HTTP so that its
`fetch()` calls work:

```sh
python -m http.server 8080 --directory docs
```

Then open `http://localhost:8080` in a browser.

## Deployment

`.github/workflows/export.yml` refreshes the JSON data and deploys the complete
`docs/` directory to GitHub Pages when changes are pushed to `main` or when the
workflow is started manually. The workflow temporarily adds the GitHub Actions
runner IP to the MongoDB Atlas access list, runs `uv run python -m src.main`,
removes the IP, and uploads `docs/` as the Pages artifact.

The workflow expects these repository secrets and variables:

- `ATLAS_PUBLIC_KEY`, `ATLAS_PRIVATE_KEY`, and `ATLAS_PROJECT_ID` for temporary
	Atlas network access;
- `MDB_USER_PROD`, `MDB_PASSWORD_PROD`, `DB_NAME_PROD`, and `COLLECTION_NAME`
	for the export;
- `TIMEZONE` as an Actions variable.

The generated JSON is part of the Pages artifact rather than being served by a
Python process. MongoDB credentials therefore remain in the exporter workflow
and are never sent to the browser.

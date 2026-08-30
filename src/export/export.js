// export.js
//
// Connects to MongoDB, reads padel court availability documents, and writes
// them as a static JSON file that the frontend fetches directly.
//
// Run manually:   node export.js
// Run on a schedule: see ../.github/workflows/export.yml for a free
// GitHub Actions cron example, or schedule this same script via any
// cron-capable host (a small VM, a scheduled serverless function, etc).

const { MongoClient } = require('mongodb');
const fs = require('fs');
const path = require('path');

const MONGODB_URI = process.env.MONGODB_URI;
const DB_NAME = process.env.DB_NAME || 'padel';
const COLLECTION_NAME = process.env.COLLECTION_NAME || 'availabilities';
const OUTPUT_PATH = process.env.OUTPUT_PATH || path.join(__dirname, '../frontend/availabilities.json');

// -----------------------------------------------------------------------
// ADAPT THIS: map one of your raw MongoDB documents to the shape the
// frontend expects. The field names below (city, region, club, court,
// startTime, durationMinutes) are placeholders based on the description
// you gave me — change the right-hand side of each line to match your
// actual document's field names.
// -----------------------------------------------------------------------
function mapDocument(doc) {
  return {
    id: String(doc._id),
    city: doc.city,
    region: doc.region,
    club: doc.club,
    court: doc.court,
    // Must end up as an ISO datetime string, e.g. "2026-08-30T09:00:00+04:00"
    start: new Date(doc.startTime).toISOString(),
    durationMinutes: doc.durationMinutes,
  };
}

async function run() {
  if (!MONGODB_URI) {
    console.error('Missing MONGODB_URI environment variable. Copy .env.example to .env and fill it in.');
    process.exit(1);
  }

  const client = new MongoClient(MONGODB_URI);

  try {
    await client.connect();
    const collection = client.db(DB_NAME).collection(COLLECTION_NAME);

    // Only export slots that haven't started yet, soonest first.
    // Adjust the field name / query to match your schema if needed.
    const cursor = collection
      .find({ startTime: { $gte: new Date() } })
      .sort({ startTime: 1 });

    const rawDocs = await cursor.toArray();
    const availabilities = rawDocs.map(mapDocument);

    const output = {
      generatedAt: new Date().toISOString(),
      availabilities,
    };

    fs.mkdirSync(path.dirname(OUTPUT_PATH), { recursive: true });
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(output, null, 2));

    console.log(`Wrote ${availabilities.length} availabilities to ${OUTPUT_PATH}`);
  } finally {
    await client.close();
  }
}

run().catch(err => {
  console.error('Export failed:', err);
  process.exit(1);
});

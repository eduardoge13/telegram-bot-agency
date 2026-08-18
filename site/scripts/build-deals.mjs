#!/usr/bin/env node
// Reads real fare data collected by the flightradar scraper (Google Flights via Amadeus)
// and writes a price BAND per destination for the homepage: the cheapest fare we have
// actually seen, and the median of the same window as the top of the band.
//
// We publish a band instead of a single exact price on purpose: the floor is a single
// observation by construction (one lucky scrape), so quoting it alone is a promise we
// cannot honour. The band leads with the floor and stays honest about a normal fare.
//
// Run on the VPS, where /opt/flightradar/data/flights.db lives:
//   node scripts/build-deals.mjs > src/data/deals.json
//
// Requires the `sqlite3` CLI to be present (already installed on the VPS for flightradar).

import { execFileSync } from 'node:child_process';

const DB_PATH = process.env.FLIGHTS_DB_PATH || '/opt/flightradar/data/flights.db';
// One window, applied per row. Filtering by the newest row *per destination* is not
// enough: a single fresh scrape would drag a pile of months-old rows onto the page.
const WINDOW_DAYS = Number(process.env.DEALS_WINDOW_DAYS || 21);
// A destination needs enough observations for the median to mean anything. Reading
// price_history there are thousands per destination, so this only guards near-empty ones.
const MIN_SAMPLE = Number(process.env.DEALS_MIN_SAMPLE || 200);
// price_history stores the total for this many travellers; must match PAX_ADULTS in
// the collector's .env or every price on the site is off by a factor.
const PAX_ADULTS = Number(process.env.PAX_ADULTS || 3);
const CURRENCY = process.env.DEALS_CURRENCY || 'MXN';

// Sources that must never reach the site.
//
// `amadeus` is excluded because AMADEUS_BASE_URL still points at
// test.api.amadeus.com — the sandbox serves cached, fictional fares. On the same
// route and dates (CUN->MAD, 2026-09-03/10) the sandbox said $11,208 while the real
// scrape said $39,523. Freshness alone cannot catch this: if the sandbox starts
// answering again its rows become "today" and the fake floors return. Provenance is
// the discriminating filter, not recency.
//
// Remove 'amadeus' from this list ONLY once the collector runs against
// api.amadeus.com in production.
const EXCLUDED_SOURCES = (process.env.DEALS_EXCLUDED_SOURCES ?? 'amadeus')
	.split(',')
	.map((s) => s.trim())
	.filter(Boolean);

// IATA -> display info. Extend as new routes appear in the scraper.
const DESTINATIONS = {
	ACA: { city: { es: 'Acapulco', en: 'Acapulco' }, country: { es: 'México', en: 'Mexico' }, region: 'domestic', image: 'acapulco.jpg' },
	CUN: { city: { es: 'Cancún', en: 'Cancún' }, country: { es: 'México', en: 'Mexico' }, region: 'domestic', image: 'cancun.jpg' },
	MAD: { city: { es: 'Madrid', en: 'Madrid' }, country: { es: 'España', en: 'Spain' }, region: 'europe', image: 'madrid.jpg' },
	BCN: { city: { es: 'Barcelona', en: 'Barcelona' }, country: { es: 'España', en: 'Spain' }, region: 'europe', image: 'barcelona.jpg' },
	PAR: { city: { es: 'París', en: 'Paris' }, country: { es: 'Francia', en: 'France' }, region: 'europe', image: 'paris.jpg' },
	ROM: { city: { es: 'Roma', en: 'Rome' }, country: { es: 'Italia', en: 'Italy' }, region: 'europe', image: 'rome.jpg' },
	BRU: { city: { es: 'Bruselas', en: 'Brussels' }, country: { es: 'Bélgica', en: 'Belgium' }, region: 'europe', image: 'brussels.jpg' },
	AMS: { city: { es: 'Ámsterdam', en: 'Amsterdam' }, country: { es: 'Países Bajos', en: 'Netherlands' }, region: 'europe', image: 'amsterdam.jpg' },
	FRA: { city: { es: 'Fráncfort', en: 'Frankfurt' }, country: { es: 'Alemania', en: 'Germany' }, region: 'europe', image: 'frankfurt.jpg' },
	BER: { city: { es: 'Berlín', en: 'Berlin' }, country: { es: 'Alemania', en: 'Germany' }, region: 'europe', image: 'berlin.jpg' },
	MUC: { city: { es: 'Múnich', en: 'Munich' }, country: { es: 'Alemania', en: 'Germany' }, region: 'europe', image: 'munich.jpg' },
};

function queryBandsByDestination() {
	// price_history, not offers: `offers` is a deduplicated summary with a couple of
	// dozen rows per destination, while price_history holds every observation the
	// scraper makes — thousands per destination in the same window. Prices there are
	// totals for PAX_ADULTS travellers, so divide to get a per-person figure.
	//
	// NTILE(20) gives twentieths: the top of bucket 1 is p05 and the top of bucket 10
	// is the median. p05 rather than MIN for the floor — across thousands of rows a
	// single mis-scraped leg would otherwise become the headline price.
	const sourceFilter = EXCLUDED_SOURCES.length
		? `AND h.source NOT IN (${EXCLUDED_SOURCES.map((s) => `'${s.replace(/'/g, "''")}'`).join(', ')})`
		: '';
	const sql = `
		WITH ranked AS (
			SELECT w.destination AS destination,
			       h.price_total / ${PAX_ADULTS} AS price_person,
			       h.observed_at AS observed_at,
			       NTILE(20) OVER (
			           PARTITION BY w.destination ORDER BY h.price_total
			       ) AS twentieth
			FROM price_history h
			JOIN watchlist w ON w.id = h.watch_id
			WHERE h.observed_at >= date('now', '-${WINDOW_DAYS} day')
			  AND h.price_total IS NOT NULL
			  AND h.price_total > 0
			  ${sourceFilter}
		)
		SELECT destination,
		       COUNT(*) AS n,
		       MAX(CASE WHEN twentieth <= 1 THEN price_person END) AS floor_pp,
		       MAX(CASE WHEN twentieth <= 10 THEN price_person END) AS median_pp,
		       MAX(observed_at) AS last_seen
		FROM ranked
		GROUP BY destination
		ORDER BY floor_pp ASC;
	`;
	const raw = execFileSync('sqlite3', ['-json', DB_PATH, sql], { encoding: 'utf8' });
	return raw.trim() ? JSON.parse(raw) : [];
}

// Round the floor down and the ceiling up to a clean marketing figure, so the band reads
// as an estimate rather than a quote. Never round the floor up: that would advertise a
// price below anything we actually saw.
function roundStep(value) {
	return value >= 20000 ? 1000 : value >= 5000 ? 500 : 100;
}
const roundFloor = (v) => Math.floor(v / roundStep(v)) * roundStep(v);
const roundCeil = (v) => Math.ceil(v / roundStep(v)) * roundStep(v);

function buildDeals() {
	const rows = queryBandsByDestination();
	const deals = [];
	const skipped = [];

	for (const row of rows) {
		const info = DESTINATIONS[row.destination];
		if (!info) continue; // skip unmapped/unknown codes rather than guessing

		// Destinations with no rows at all inside the window never come back from the
		// query, so they are reported as absent rather than silently missing.
		if (!Number.isFinite(row.n) || row.n < MIN_SAMPLE) {
			skipped.push({ code: row.destination, reason: 'sample', sampleSize: row.n });
			continue;
		}

		const priceFrom = roundFloor(row.floor_pp);
		const priceTo = roundCeil(row.median_pp);
		if (!(priceFrom > 0) || !(priceTo > priceFrom)) {
			skipped.push({ code: row.destination, reason: 'band', floor: row.floor_pp, median: row.median_pp });
			continue;
		}

		deals.push({
			code: row.destination,
			city: info.city,
			country: info.country,
			region: info.region,
			image: info.image,
			priceFrom,
			priceTo,
			// price_history carries no currency column: the collector normalises every
			// source to MXN before storing (see flightradar/normalize.py).
			currency: CURRENCY,
			sampleSize: row.n,
			lastSeen: row.last_seen,
		});
	}

	// Destinations that produced no rows in the window at all: absent from the query
	// result, so record them explicitly instead of letting them vanish unexplained.
	const seen = new Set(rows.map((row) => row.destination));
	for (const code of Object.keys(DESTINATIONS)) {
		if (!seen.has(code)) skipped.push({ code, reason: 'no-data-in-window' });
	}

	return {
		generatedAt: new Date().toISOString(),
		windowDays: WINDOW_DAYS,
		minSample: MIN_SAMPLE,
		excludedSources: EXCLUDED_SOURCES,
		skipped,
		deals,
	};
}

const output = buildDeals();
process.stdout.write(JSON.stringify(output, null, '\t') + '\n');

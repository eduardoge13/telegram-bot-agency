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
const LOOKBACK_DAYS = Number(process.env.DEALS_LOOKBACK_DAYS || 45);
// A destination needs enough observations for the median to mean anything.
const MIN_SAMPLE = Number(process.env.DEALS_MIN_SAMPLE || 20);
// The page claims fares are monitored daily. A route the scraper stopped collecting
// must not appear under that claim, however good its old numbers look.
const MAX_STALE_DAYS = Number(process.env.DEALS_MAX_STALE_DAYS || 21);

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
	// ntile(4) splits each destination's fares into quartiles; the largest value still
	// inside the lower half is the median. The raw max is useless here — it is business
	// class and would put a six-figure number on the page.
	const sql = `
		WITH ranked AS (
			SELECT destination, price_person, currency, collected_at,
			       NTILE(4) OVER (PARTITION BY destination ORDER BY price_person) AS quartile
			FROM offers
			WHERE collected_at >= date('now', '-${LOOKBACK_DAYS} day')
			  AND price_person IS NOT NULL
		)
		SELECT destination,
		       COUNT(*) AS n,
		       MIN(price_person) AS min_pp,
		       MAX(CASE WHEN quartile <= 2 THEN price_person END) AS median_pp,
		       currency,
		       MAX(collected_at) AS last_seen
		FROM ranked
		GROUP BY destination
		ORDER BY min_pp ASC;
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
	const staleCutoff = Date.now() - MAX_STALE_DAYS * 86400000;
	const deals = [];
	const skipped = [];

	for (const row of rows) {
		const info = DESTINATIONS[row.destination];
		if (!info) continue; // skip unmapped/unknown codes rather than guessing

		if (!Number.isFinite(row.n) || row.n < MIN_SAMPLE) {
			skipped.push({ code: row.destination, reason: 'sample', sampleSize: row.n });
			continue;
		}
		if (new Date(row.last_seen).getTime() < staleCutoff) {
			skipped.push({ code: row.destination, reason: 'stale', lastSeen: row.last_seen });
			continue;
		}

		const priceFrom = roundFloor(row.min_pp);
		const priceTo = roundCeil(row.median_pp);
		if (!(priceFrom > 0) || !(priceTo > priceFrom)) {
			skipped.push({ code: row.destination, reason: 'band', min: row.min_pp, median: row.median_pp });
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
			currency: row.currency,
			sampleSize: row.n,
			lastSeen: row.last_seen,
		});
	}

	return {
		generatedAt: new Date().toISOString(),
		lookbackDays: LOOKBACK_DAYS,
		minSample: MIN_SAMPLE,
		maxStaleDays: MAX_STALE_DAYS,
		skipped,
		deals,
	};
}

const output = buildDeals();
process.stdout.write(JSON.stringify(output, null, '\t') + '\n');

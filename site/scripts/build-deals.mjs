#!/usr/bin/env node
// Reads real fare data collected by the flightradar scraper (Google Flights via Amadeus)
// and writes a snapshot of best-known prices per destination for the homepage.
//
// Run on the VPS, where /opt/flightradar/data/flights.db lives:
//   node scripts/build-deals.mjs > src/data/deals.json
//
// Requires the `sqlite3` CLI to be present (already installed on the VPS for flightradar).

import { execFileSync } from 'node:child_process';

const DB_PATH = process.env.FLIGHTS_DB_PATH || '/opt/flightradar/data/flights.db';
const LOOKBACK_DAYS = 45;

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

function queryMinPricesByDestination() {
	const sql = `
		SELECT destination, MIN(price_person) AS min_pp, currency, MAX(collected_at) AS last_seen, COUNT(*) AS n
		FROM offers
		WHERE collected_at >= date('now', '-${LOOKBACK_DAYS} day')
		  AND price_person IS NOT NULL
		GROUP BY destination
		ORDER BY min_pp ASC;
	`;
	const raw = execFileSync('sqlite3', ['-json', DB_PATH, sql], { encoding: 'utf8' });
	return raw.trim() ? JSON.parse(raw) : [];
}

function buildDeals() {
	const rows = queryMinPricesByDestination();
	const deals = [];

	for (const row of rows) {
		const info = DESTINATIONS[row.destination];
		if (!info) continue; // skip unmapped/unknown codes rather than guessing
		if (!Number.isFinite(row.n) || row.n < 3) continue; // avoid single-sample noise

		deals.push({
			code: row.destination,
			city: info.city,
			country: info.country,
			region: info.region,
			image: info.image,
			priceFrom: row.min_pp,
			currency: row.currency,
			sampleSize: row.n,
			lastSeen: row.last_seen,
		});
	}

	return {
		generatedAt: new Date().toISOString(),
		lookbackDays: LOOKBACK_DAYS,
		deals,
	};
}

const output = buildDeals();
process.stdout.write(JSON.stringify(output, null, '\t') + '\n');

import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const astroCli = path.resolve(scriptDir, '../node_modules/astro/bin/astro.mjs');
const args = process.argv.slice(2);

const child = spawn(process.execPath, [astroCli, ...args], {
	stdio: 'inherit',
	env: {
		...process.env,
		ASTRO_TELEMETRY_DISABLED: '1',
	},
});

child.on('exit', (code, signal) => {
	if (signal) {
		process.kill(process.pid, signal);
		return;
	}

	process.exit(code ?? 0);
});

child.on('error', (error) => {
	console.error(error);
	process.exit(1);
});

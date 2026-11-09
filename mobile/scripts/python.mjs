// Use the platform's standard Python executable for npm build commands.
import { spawnSync } from 'node:child_process';
const result = spawnSync(process.platform === 'win32' ? 'python' : 'python3', process.argv.slice(2), { stdio: 'inherit' });
if (result.error) console.error(result.error.message);
process.exit(result.status ?? 1);

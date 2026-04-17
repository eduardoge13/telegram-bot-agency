# Backups (telegram-bot-agency)

This project runs on a VPS under `systemd` and keeps a local SQLite cache at:

- `/opt/telegram-bot-agency/data/clients.db`

The VPS automation installs a `systemd` timer and service that:

- Creates a consistent SQLite backup using `sqlite3 .backup`
- Compresses it into a `.tar.gz` including a small manifest
- Verifies the backup is restorable (extract + `PRAGMA quick_check`)
- Prunes old backups (retention policy)

## Location

- Backups directory: `/opt/telegram-bot-agency/backups`
- Backup filenames: `clientsdb_YYYYMMDDThhmmssZ.tar.gz`

Backups contain client data. Keep permissions restricted to `root`.

## Schedule

"Quincenal" is implemented as **the 1st and 15th of each month** via `systemd` timer
on the VPS (server timezone, usually UTC).

Check schedule:

- `systemctl list-timers --all | grep telegram-bot-backup`

## Retention policy

Retention is enforced during each run:

- Keep the most recent N backups (default: 26; about 1 year for twice/month)
- Delete older ones

The script can be adjusted to change `KEEP` if needed.

## Manual run (VPS)

- `systemctl start telegram-bot-backup.service`
- `journalctl -u telegram-bot-backup.service -n 200 --no-pager`

## Restore (VPS)

1. Stop the bot:
   - `systemctl stop telegram-bot-agency`
2. Extract a backup to a temp dir:
   - `mkdir -p /root/restore_tmp && tar -xzf /opt/telegram-bot-agency/backups/<file>.tar.gz -C /root/restore_tmp`
3. Replace the DB:
   - `cp -f /root/restore_tmp/clients.db /opt/telegram-bot-agency/data/clients.db`
   - `chown root:root /opt/telegram-bot-agency/data/clients.db`
4. Start the bot:
   - `systemctl start telegram-bot-agency`

## Verify a backup (VPS)

Extract and run integrity check:

- `tmp=$(mktemp -d) && tar -xzf /opt/telegram-bot-agency/backups/<file>.tar.gz -C "$tmp" && sqlite3 "$tmp/clients.db" "PRAGMA quick_check;"`


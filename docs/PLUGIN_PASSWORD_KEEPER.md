# Plugin: password_keeper

Local **encrypted** account vault for SWP. Imports browser password **CSV exports** (Chrome / Edge / Firefox) and migrates outdated plaintext key-value JSON files.

## Security notes

- Secrets are encrypted with a **master password** (PBKDF2 + Fernet).
- Vault file default: `data/password_vault.json` (mode `0600` when possible).
- `password.list` always masks secrets; `password.get` requires `reveal=true`.
- Prefer browser **CSV export** over reading live browser DB files (OS keychain locked, fragile, risky).
- Never commit vault files or master passwords.

## Install

```bash
pip install -e ".[password]"
```

## Tasks

| Task | Metadata |
|------|----------|
| `password.list` | `master_password`, `vault_path?`, `query?` |
| `password.get` | `id`, `reveal?`, `master_password` |
| `password.upsert` | `origin`/`url`, `username`, `password`, `dry_run?` |
| `password.delete` | `id`, `dry_run?` |
| `password.import_csv` | `csv_path` or `csv_text`, `browser?` chrome\|edge\|firefox, `merge?`, `dry_run?` |
| `password.import_file` | `path` (plaintext JSON kv), `delete_source?`, `dry_run?` |
| `password.purge_outdated` | `max_age_days?`, `strip_extra_keys?`, `remove_empty?`, `dry_run?` |

## Browser import

1. Chrome / Edge: Settings → Passwords → Export
2. Firefox: about:logins → … → Export logins

```python
await rt.executor.execute("password.import_csv", {
    "master_password": "...",
    "vault_path": "data/password_vault.json",
    "csv_path": "passwords.csv",
    "browser": "chrome",
})
```

## Outdated keys / files

- Unknown account fields dropped; allowed `extra` keys: notes, otp_uri, tags, browser, http_realm, form_action.
- Legacy vault keys (`passwords`, `kv`, `secrets`, …) migrated into `accounts` on load.
- `password.import_file` folds `{url: {user, password}}` JSON into the vault.
- `password.purge_outdated` removes empty / optionally age-stale accounts.

"""Encrypted vault file store + browser CSV import + legacy cleanup."""
from __future__ import annotations

import base64
import contextlib
import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from packages.password_keeper.password_keeper.crypto import decrypt, encrypt, fingerprint, new_salt
from packages.password_keeper.password_keeper.models import (
    ALLOWED_EXTRA_KEYS,
    LEGACY_VAULT_KEYS,
    VAULT_VERSION,
    AccountEntry,
    VaultDocument,
    account_match_key,
    normalize_origin,
    utc_now_iso,
)


class VaultError(RuntimeError):
    pass


class PasswordVault:
    def __init__(self, path: Path, master_password: str) -> None:
        self.path = path
        self.master_password = master_password
        self.doc: VaultDocument | None = None

    def load_or_create(self) -> VaultDocument:
        if self.path.is_file():
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self.doc = self._migrate(raw)
            self._assert_master()
            return self.doc
        salt = new_salt()
        self.doc = VaultDocument(
            version=VAULT_VERSION,
            salt_b64=base64.b64encode(salt).decode("ascii"),
            master_fp=fingerprint(self.master_password, salt),
            accounts=[],
        )
        return self.doc

    def _salt(self) -> bytes:
        assert self.doc is not None
        return base64.b64decode(self.doc.salt_b64.encode("ascii"))

    def _assert_master(self) -> None:
        assert self.doc is not None
        if fingerprint(self.master_password, self._salt()) != self.doc.master_fp:
            raise VaultError("master password does not match vault")

    def _migrate(self, raw: dict[str, Any]) -> VaultDocument:
        discarded: list[str] = []
        salt_b64 = raw.get("salt_b64")
        if salt_b64:
            salt = base64.b64decode(str(salt_b64).encode("ascii"))
            master_fp = str(raw.get("master_fp") or fingerprint(self.master_password, salt))
        else:
            salt = new_salt()
            salt_b64 = base64.b64encode(salt).decode("ascii")
            master_fp = fingerprint(self.master_password, salt)
            discarded.append("missing_salt_rekeyed")

        accounts_raw: list[Any] = []
        if isinstance(raw.get("accounts"), list):
            accounts_raw.extend(raw["accounts"])
        for key in LEGACY_VAULT_KEYS:
            if key not in raw:
                continue
            discarded.append(key)
            val = raw.get(key)
            if isinstance(val, list):
                accounts_raw.extend(val)
            elif isinstance(val, dict):
                for origin, item in val.items():
                    if isinstance(item, dict):
                        accounts_raw.append(
                            {
                                "origin": origin,
                                "username": item.get("username") or item.get("user") or "",
                                "password": item.get("password") or item.get("secret") or "",
                                "source": "legacy_kv",
                            }
                        )
                    else:
                        accounts_raw.append(
                            {"origin": origin, "username": "", "password": str(item), "source": "legacy_kv"}
                        )

        known = {"version", "salt_b64", "master_fp", "accounts", "legacy_discarded_keys"}
        for k in raw:
            if k not in known and k not in LEGACY_VAULT_KEYS:
                discarded.append(str(k))

        accounts: list[AccountEntry] = []
        for item in accounts_raw:
            if not isinstance(item, dict):
                continue
            entry = self._coerce_entry(item, salt=salt)
            if entry is not None:
                accounts.append(entry)

        return VaultDocument(
            version=VAULT_VERSION,
            salt_b64=str(salt_b64),
            master_fp=master_fp,
            accounts=accounts,
            legacy_discarded_keys=sorted(set(discarded + list(raw.get("legacy_discarded_keys") or []))),
        )

    def _coerce_entry(self, item: dict[str, Any], *, salt: bytes) -> AccountEntry | None:
        origin = str(item.get("origin") or item.get("url") or item.get("name") or "")
        username = str(item.get("username") or item.get("user") or "")
        secret_enc = str(item.get("secret_enc") or "")
        plain = item.get("password") or item.get("secret")
        if plain and not secret_enc:
            secret_enc = encrypt(self.master_password, salt, str(plain))
        if not secret_enc:
            return None
        extra = dict(item.get("extra") or {})
        for k, v in item.items():
            if k in {
                "id", "origin", "url", "name", "username", "user", "secret_enc", "password", "secret",
                "label", "source", "created_at", "updated_at", "last_used_at", "extra",
            }:
                continue
            if k in ALLOWED_EXTRA_KEYS:
                extra[k] = v
        return AccountEntry(
            id=str(item["id"]) if item.get("id") else AccountEntry().id,
            origin=normalize_origin(origin),
            username=username,
            secret_enc=secret_enc,
            label=str(item.get("label") or ""),
            source=str(item.get("source") or "legacy"),
            created_at=str(item.get("created_at") or utc_now_iso()),
            updated_at=str(item.get("updated_at") or utc_now_iso()),
            last_used_at=item.get("last_used_at"),
            extra={k: v for k, v in extra.items() if k in ALLOWED_EXTRA_KEYS},
        )

    def save(self, *, dry_run: bool = False) -> None:
        assert self.doc is not None
        self.doc.version = VAULT_VERSION
        text = json.dumps(self.doc.model_dump(), indent=2, ensure_ascii=False) + "\n"
        if dry_run:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text, encoding="utf-8")
        with contextlib.suppress(OSError):
            self.path.chmod(0o600)

    def list_accounts(self, *, query: str = "") -> list[dict[str, Any]]:
        assert self.doc is not None
        q = query.strip().lower()
        out: list[dict[str, Any]] = []
        for a in self.doc.accounts:
            if q and q not in a.origin.lower() and q not in a.username.lower() and q not in (a.label or "").lower():
                continue
            out.append(a.public_dict())
        return out

    def get(self, account_id: str, *, reveal: bool = False) -> dict[str, Any]:
        assert self.doc is not None
        for a in self.doc.accounts:
            if a.id == account_id:
                secret = decrypt(self.master_password, self._salt(), a.secret_enc) if reveal else None
                a.last_used_at = utc_now_iso()
                return a.public_dict(reveal_secret=secret)
        raise VaultError(f"account not found: {account_id}")

    def upsert(
        self,
        *,
        origin: str,
        username: str,
        password: str,
        label: str = "",
        source: str = "manual",
        extra: dict[str, Any] | None = None,
    ) -> AccountEntry:
        assert self.doc is not None
        origin_n = normalize_origin(origin)
        key = account_match_key(origin_n, username)
        extra_clean = {k: v for k, v in (extra or {}).items() if k in ALLOWED_EXTRA_KEYS}
        for a in self.doc.accounts:
            if account_match_key(a.origin, a.username) == key:
                a.secret_enc = encrypt(self.master_password, self._salt(), password)
                a.label = label or a.label
                a.source = source
                a.updated_at = utc_now_iso()
                a.extra.update(extra_clean)
                a.extra = {k: v for k, v in a.extra.items() if k in ALLOWED_EXTRA_KEYS}
                return a
        entry = AccountEntry(
            origin=origin_n,
            username=username,
            secret_enc=encrypt(self.master_password, self._salt(), password),
            label=label,
            source=source,
            extra=extra_clean,
        )
        self.doc.accounts.append(entry)
        return entry

    def delete(self, account_id: str) -> bool:
        assert self.doc is not None
        before = len(self.doc.accounts)
        self.doc.accounts = [a for a in self.doc.accounts if a.id != account_id]
        return len(self.doc.accounts) < before

    def import_browser_csv(self, csv_text: str, *, source: str = "browser_csv", merge: bool = True) -> dict[str, int]:
        assert self.doc is not None
        reader = csv.DictReader(io.StringIO(csv_text))
        if not reader.fieldnames:
            raise VaultError("empty csv")
        fields = {f.lower().strip(): f for f in reader.fieldnames if f}
        url_k = fields.get("url") or fields.get("origin") or fields.get("name")
        user_k = fields.get("username") or fields.get("user")
        pass_k = fields.get("password") or fields.get("passwd")
        if not pass_k:
            raise VaultError("csv missing password column")
        added = updated = skipped = 0
        for row in reader:
            password = (row.get(pass_k) or "").strip()
            if not password:
                skipped += 1
                continue
            origin = (row.get(url_k) or "") if url_k else ""
            username = (row.get(user_k) or "") if user_k else ""
            extra: dict[str, Any] = {}
            for cand, key in (("httprealm", "http_realm"), ("formactionorigin", "form_action")):
                if cand in fields:
                    val = row.get(fields[cand])
                    if val:
                        extra[key] = val
            key = account_match_key(str(origin), str(username))
            exists = any(account_match_key(a.origin, a.username) == key for a in self.doc.accounts)
            if exists and not merge:
                skipped += 1
                continue
            before_ids = {a.id for a in self.doc.accounts}
            entry = self.upsert(origin=str(origin), username=str(username), password=password, source=source, extra=extra)
            if entry.id in before_ids:
                updated += 1
            else:
                added += 1
        return {"added": added, "updated": updated, "skipped": skipped}

    def import_plaintext_kv_file(self, path: Path) -> dict[str, int]:
        assert self.doc is not None
        data = json.loads(path.read_text(encoding="utf-8"))
        added = updated = 0
        if not isinstance(data, dict):
            raise VaultError("plaintext file must be a JSON object")
        if "accounts" in data or "salt_b64" in data:
            migrated = self._migrate(data)
            before = {account_match_key(a.origin, a.username) for a in self.doc.accounts}
            for a in migrated.accounts:
                key = account_match_key(a.origin, a.username)
                plain = decrypt(self.master_password, base64.b64decode(migrated.salt_b64), a.secret_enc)
                self.upsert(
                    origin=a.origin,
                    username=a.username,
                    password=plain,
                    label=a.label,
                    source=a.source or "file",
                    extra=a.extra,
                )
                if key in before:
                    updated += 1
                else:
                    added += 1
            self.doc.legacy_discarded_keys = sorted(
                set(self.doc.legacy_discarded_keys + migrated.legacy_discarded_keys)
            )
            return {"added": added, "updated": updated}
        for origin, val in data.items():
            if origin in {"version", "salt_b64", "master_fp"}:
                continue
            if isinstance(val, dict):
                user = str(val.get("username") or val.get("user") or "")
                pw = str(val.get("password") or val.get("secret") or "")
            else:
                user, pw = "", str(val)
            if not pw:
                continue
            before_ids = {a.id for a in self.doc.accounts}
            entry = self.upsert(origin=str(origin), username=user, password=pw, source="file")
            if entry.id in before_ids:
                updated += 1
            else:
                added += 1
        return {"added": added, "updated": updated}

    def purge_outdated(
        self,
        *,
        max_age_days: int | None = None,
        strip_extra_keys: bool = True,
        remove_empty: bool = True,
    ) -> dict[str, int]:
        assert self.doc is not None
        removed_accounts = 0
        stripped_keys = 0
        kept: list[AccountEntry] = []
        now = utc_now_iso()
        for a in self.doc.accounts:
            if strip_extra_keys:
                before = set(a.extra.keys())
                a.extra = {k: v for k, v in a.extra.items() if k in ALLOWED_EXTRA_KEYS}
                stripped_keys += len(before - set(a.extra.keys()))
            if remove_empty and not a.origin and not a.username:
                removed_accounts += 1
                continue
            if max_age_days is not None and max_age_days > 0:
                ref = a.last_used_at or a.updated_at or a.created_at
                try:
                    ref_d = datetime.fromisoformat(ref.replace("Z", "+00:00"))
                    now_d = datetime.fromisoformat(now.replace("Z", "+00:00"))
                    if (now_d - ref_d).days > max_age_days:
                        removed_accounts += 1
                        continue
                except ValueError:
                    pass
            kept.append(a)
        self.doc.accounts = kept
        return {
            "removed_accounts": removed_accounts,
            "stripped_extra_keys": stripped_keys,
            "legacy_keys_recorded": len(self.doc.legacy_discarded_keys),
            "remaining": len(self.doc.accounts),
        }

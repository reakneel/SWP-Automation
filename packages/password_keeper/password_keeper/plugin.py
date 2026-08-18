from __future__ import annotations

from pathlib import Path
from typing import Any

from core.plugin.base import Plugin, PluginMetadata
from core.task.base import Task, TaskContext, TaskResult
from packages.password_keeper.password_keeper.vault import PasswordVault, VaultError


def _master(meta: dict[str, Any]) -> str:
    return str(meta.get("master_password") or meta.get("master") or "")


def _vault_path(meta: dict[str, Any]) -> Path:
    return Path(str(meta.get("vault_path") or "data/password_vault.json"))


def _open(meta: dict[str, Any]) -> PasswordVault:
    master = _master(meta)
    if not master:
        raise VaultError("metadata.master_password is required")
    vault = PasswordVault(_vault_path(meta), master)
    vault.load_or_create()
    return vault


class _ListTask(Task):
    name = "password.list"
    description = "List vault accounts (passwords masked)."

    async def run(self, context: TaskContext) -> TaskResult:
        try:
            vault = _open(context.metadata)
            items = vault.list_accounts(query=str(context.metadata.get("query") or ""))
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("listed", count=len(items), accounts=items)


class _GetTask(Task):
    name = "password.get"
    description = "Get one account by id; set reveal=true to show password."

    async def run(self, context: TaskContext) -> TaskResult:
        account_id = str(context.metadata.get("id") or "")
        if not account_id:
            return TaskResult.failure("metadata.id is required")
        reveal = bool(context.metadata.get("reveal", False))
        try:
            vault = _open(context.metadata)
            item = vault.get(account_id, reveal=reveal)
            dry = bool(context.metadata.get("dry_run", False))
            if not dry and reveal:
                vault.save(dry_run=False)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("fetched", account=item)


class _UpsertTask(Task):
    name = "password.upsert"
    description = "Create or update an account (origin + username key)."

    async def run(self, context: TaskContext) -> TaskResult:
        origin = str(context.metadata.get("origin") or context.metadata.get("url") or "")
        username = str(context.metadata.get("username") or "")
        password = str(context.metadata.get("password") or "")
        if not password:
            return TaskResult.failure("metadata.password is required")
        dry = bool(context.metadata.get("dry_run", False))
        try:
            vault = _open(context.metadata)
            entry = vault.upsert(
                origin=origin,
                username=username,
                password=password,
                label=str(context.metadata.get("label") or ""),
                source=str(context.metadata.get("source") or "manual"),
                extra=dict(context.metadata.get("extra") or {}),
            )
            vault.save(dry_run=dry)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok(
            "would_upsert" if dry else "upserted",
            account=entry.public_dict(),
            dry_run=dry,
        )


class _DeleteTask(Task):
    name = "password.delete"
    description = "Delete an account by id."

    async def run(self, context: TaskContext) -> TaskResult:
        account_id = str(context.metadata.get("id") or "")
        if not account_id:
            return TaskResult.failure("metadata.id is required")
        dry = bool(context.metadata.get("dry_run", False))
        try:
            vault = _open(context.metadata)
            ok = vault.delete(account_id)
            if ok:
                vault.save(dry_run=dry)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        if not ok:
            return TaskResult.failure("account not found", id=account_id)
        return TaskResult.ok("would_delete" if dry else "deleted", id=account_id, dry_run=dry)


class _ImportCsvTask(Task):
    name = "password.import_csv"
    description = "Import Chrome/Edge/Firefox password CSV export into the vault."

    async def run(self, context: TaskContext) -> TaskResult:
        csv_text = str(context.metadata.get("csv_text") or "")
        csv_path = str(context.metadata.get("csv_path") or "")
        if not csv_text and csv_path:
            csv_text = Path(csv_path).read_text(encoding="utf-8")
        if not csv_text:
            return TaskResult.failure("metadata.csv_text or csv_path is required")
        browser = str(context.metadata.get("browser") or "browser").lower()
        source = {
            "chrome": "chrome_csv",
            "edge": "edge_csv",
            "firefox": "firefox_csv",
        }.get(browser, "browser_csv")
        dry = bool(context.metadata.get("dry_run", False))
        merge = bool(context.metadata.get("merge", True))
        try:
            vault = _open(context.metadata)
            stats = vault.import_browser_csv(csv_text, source=source, merge=merge)
            vault.save(dry_run=dry)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("would_import" if dry else "imported", dry_run=dry, source=source, **stats)


class _ImportFileTask(Task):
    name = "password.import_file"
    description = "Import outdated plaintext JSON key-value password files into the vault."

    async def run(self, context: TaskContext) -> TaskResult:
        path = str(context.metadata.get("path") or "")
        if not path:
            return TaskResult.failure("metadata.path is required")
        dry = bool(context.metadata.get("dry_run", False))
        delete_source = bool(context.metadata.get("delete_source", False))
        try:
            vault = _open(context.metadata)
            stats = vault.import_plaintext_kv_file(Path(path))
            vault.save(dry_run=dry)
            if delete_source and not dry:
                Path(path).unlink(missing_ok=True)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok(
            "would_import_file" if dry else "imported_file",
            dry_run=dry,
            delete_source=delete_source and not dry,
            **stats,
        )


class _PurgeTask(Task):
    name = "password.purge_outdated"
    description = "Remove empty/stale accounts and strip unknown extra keys."

    async def run(self, context: TaskContext) -> TaskResult:
        dry = bool(context.metadata.get("dry_run", False))
        max_age = context.metadata.get("max_age_days")
        max_age_days = int(max_age) if max_age is not None else None
        try:
            vault = _open(context.metadata)
            stats = vault.purge_outdated(
                max_age_days=max_age_days,
                strip_extra_keys=bool(context.metadata.get("strip_extra_keys", True)),
                remove_empty=bool(context.metadata.get("remove_empty", True)),
            )
            vault.save(dry_run=dry)
        except Exception as exc:
            return TaskResult.failure(str(exc))
        return TaskResult.ok("would_purge" if dry else "purged", dry_run=dry, **stats)


class PasswordKeeperPlugin(Plugin):
    metadata = PluginMetadata(
        name="password_keeper",
        version="0.1.0",
        description="Encrypted local password vault with browser CSV and legacy file import.",
        tags=["password", "vault", "security"],
    )

    def tasks(self) -> list[Task]:
        return [
            _ListTask(),
            _GetTask(),
            _UpsertTask(),
            _DeleteTask(),
            _ImportCsvTask(),
            _ImportFileTask(),
            _PurgeTask(),
        ]

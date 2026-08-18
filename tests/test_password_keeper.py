from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.runtime import AutomationRuntime
from packages.password_keeper.password_keeper.plugin import PasswordKeeperPlugin
from packages.password_keeper.password_keeper.vault import PasswordVault


@pytest.mark.asyncio
async def test_upsert_list_get_purge(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault.json"
    master = "unit-test-master-key"
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(PasswordKeeperPlugin())

    rec = await runtime.executor.execute(
        "password.upsert",
        {
            "master_password": master,
            "vault_path": str(vault_path),
            "origin": "https://example.com",
            "username": "alice",
            "password": "p@ss",
            "extra": {"notes": "ok", "stale_field": "drop-me"},
        },
    )
    assert rec.status.value == "success"
    account_id = rec.data["account"]["id"]
    assert rec.data["account"]["password"] == "********"

    listed = await runtime.executor.execute(
        "password.list",
        {"master_password": master, "vault_path": str(vault_path)},
    )
    assert listed.data["count"] == 1

    got = await runtime.executor.execute(
        "password.get",
        {
            "master_password": master,
            "vault_path": str(vault_path),
            "id": account_id,
            "reveal": True,
        },
    )
    assert got.data["account"]["password"] == "p@ss"

    vault = PasswordVault(vault_path, master)
    vault.load_or_create()
    assert "stale_field" not in vault.doc.accounts[0].extra


@pytest.mark.asyncio
async def test_import_csv_and_legacy_file(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault.json"
    master = "unit-test-master-key"
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(PasswordKeeperPlugin())

    csv_path = tmp_path / "export.csv"
    csv_path.write_text(
        "name,url,username,password\n"
        "Example,https://ex.com,bob,secret1\n",
        encoding="utf-8",
    )
    rec = await runtime.executor.execute(
        "password.import_csv",
        {
            "master_password": master,
            "vault_path": str(vault_path),
            "csv_path": str(csv_path),
            "browser": "chrome",
        },
    )
    assert rec.status.value == "success"
    assert rec.data["added"] == 1

    legacy = tmp_path / "old_passwords.json"
    legacy.write_text(
        json.dumps({"https://legacy.test": {"username": "carol", "password": "oldpw", "foo": 1}}),
        encoding="utf-8",
    )
    rec2 = await runtime.executor.execute(
        "password.import_file",
        {
            "master_password": master,
            "vault_path": str(vault_path),
            "path": str(legacy),
        },
    )
    assert rec2.status.value == "success"
    assert rec2.data["added"] == 1

    listed = await runtime.executor.execute(
        "password.list",
        {"master_password": master, "vault_path": str(vault_path)},
    )
    assert listed.data["count"] == 2


@pytest.mark.asyncio
async def test_wrong_master_rejected(tmp_path: Path) -> None:
    vault_path = tmp_path / "vault.json"
    runtime = AutomationRuntime.create()
    await runtime.plugins.load(PasswordKeeperPlugin())
    await runtime.executor.execute(
        "password.upsert",
        {
            "master_password": "right",
            "vault_path": str(vault_path),
            "origin": "https://a.com",
            "username": "u",
            "password": "x",
        },
    )
    bad = await runtime.executor.execute(
        "password.list",
        {"master_password": "wrong", "vault_path": str(vault_path)},
    )
    assert bad.status.value == "failed"

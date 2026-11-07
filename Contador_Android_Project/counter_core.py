# -*- coding: utf-8 -*-
"""Lógica y almacenamiento del Contador de usuarios (compartida y sin interfaz)."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any


def new_id() -> str:
    return uuid.uuid4().hex


def default_data() -> dict[str, Any]:
    group_id = new_id()
    return {
        "version": 1,
        "reset_interval_hours": 6.0,
        "next_reset_at": time.time() + 6 * 3600,
        "selected_group_id": group_id,
        "groups": [{"id": group_id, "name": "Grupo 1", "users": []}],
    }


def normalize_data(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        raise ValueError("El archivo no contiene una estructura válida.")

    if not data["groups"]:
        fresh = default_data()
        data["groups"] = fresh["groups"]
        data["selected_group_id"] = fresh["selected_group_id"]

    data.setdefault("version", 1)
    data.setdefault("reset_interval_hours", 6.0)
    try:
        interval = float(data["reset_interval_hours"])
    except (TypeError, ValueError):
        interval = 6.0
    if interval <= 0:
        interval = 6.0
    data["reset_interval_hours"] = interval

    try:
        data.setdefault("next_reset_at", time.time() + interval * 3600)
        data["next_reset_at"] = float(data["next_reset_at"])
    except (TypeError, ValueError):
        data["next_reset_at"] = time.time() + interval * 3600

    for group in data["groups"]:
        if not isinstance(group, dict):
            raise ValueError("Hay un grupo con formato no válido.")
        group.setdefault("id", new_id())
        group.setdefault("name", "Grupo")
        group.setdefault("users", [])
        if not isinstance(group["users"], list):
            group["users"] = []
        clean_users = []
        for user in group["users"]:
            if not isinstance(user, dict):
                continue
            user.setdefault("id", new_id())
            user.setdefault("name", "Usuario")
            user["active"] = bool(user.get("active", False))
            clean_users.append(user)
        group["users"] = clean_users

    valid_ids = {g["id"] for g in data["groups"]}
    if data.get("selected_group_id") not in valid_ids:
        data["selected_group_id"] = data["groups"][0]["id"]
    return data


def load_data(path: str | Path) -> tuple[dict[str, Any], str | None]:
    path = Path(path)
    if not path.exists():
        return default_data(), None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return normalize_data(json.load(handle)), None
    except Exception as exc:
        return default_data(), str(exc)


def save_data(path: str | Path, data: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
    temp_path.replace(path)


def count_users(data: dict[str, Any]) -> tuple[int, int]:
    total = active = 0
    for group in data["groups"]:
        for user in group["users"]:
            total += 1
            active += bool(user.get("active", False))
    return active, total


def reset_if_due(data: dict[str, Any], now: float | None = None) -> bool:
    """Apaga todos los estados si venció el plazo y mantiene la cadencia original."""
    now = time.time() if now is None else float(now)
    next_reset = float(data.get("next_reset_at", now + 3600))
    if now < next_reset:
        return False
    interval_seconds = max(0.5 * 3600, float(data.get("reset_interval_hours", 6.0)) * 3600)
    for group in data["groups"]:
        for user in group["users"]:
            user["active"] = False
    missed_intervals = int((now - next_reset) // interval_seconds) + 1
    data["next_reset_at"] = next_reset + missed_intervals * interval_seconds
    return True

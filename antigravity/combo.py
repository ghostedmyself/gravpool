from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any

NAME_REGEX = re.compile(r"^[a-zA-Z0-9\._\-]{1,64}$")

@dataclass
class Combo:
    name: str
    kind: str = 'fallback'
    models: list[str] = field(default_factory=list)
    created_at: str = ''
    updated_at: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "models": self.models,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Combo:
        return cls(
            name=data.get("name", ""),
            kind=data.get("kind", "fallback"),
            models=data.get("models", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

def combo_dir() -> str:
    """Return the combo config directory, creating it if necessary."""
    d = Path.home() / ".antigravity-pool"
    d.mkdir(parents=True, exist_ok=True)
    os.chmod(str(d), 0o700)
    return str(d)

def combos_path() -> str:
    """Return the path to the combos.json file."""
    return str(Path(combo_dir()) / "combos.json")

def load_combos() -> list[Combo]:
    """Load all combos from the storage file."""
    path = combos_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        return [Combo.from_dict(c) for c in data if isinstance(c, dict)]
    except Exception:
        return []

def save_combos(combos: list[Combo]) -> None:
    """Atomically save the list of combos to storage."""
    path = combos_path()
    data = [c.to_dict() for c in combos]
    dir_name = os.path.dirname(path)
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, prefix="combos_", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, path)

def get_combo(name: str) -> Optional[Combo]:
    """Retrieve a combo by name."""
    for c in load_combos():
        if c.name == name:
            return c
    return None

def add_combo(name: str, models: list[str], kind: str = "fallback") -> Combo:
    """Create or update a combo."""
    if not NAME_REGEX.match(name):
        raise ValueError(f"Invalid combo name: {name}")
    if not models:
        raise ValueError("Combo models list cannot be empty")
    if kind not in ("fallback", "fusion"):
        raise ValueError(f"Invalid combo kind: {kind}")
    
    # Dedupe while preserving order
    seen = set()
    deduped_models = []
    for m in models:
        if m not in seen:
            seen.add(m)
            deduped_models.append(m)
            
    combos = load_combos()
    now = datetime.now(timezone.utc).isoformat()
    
    existing = None
    for i, c in enumerate(combos):
        if c.name == name:
            existing = c
            combos.pop(i)
            break
            
    new_combo = Combo(
        name=name,
        kind=kind,
        models=deduped_models,
        created_at=existing.created_at if existing and existing.created_at else now,
        updated_at=now
    )
    combos.append(new_combo)
    save_combos(combos)
    return new_combo

def remove_combo(name: str) -> bool:
    """Remove a combo by name. Returns True if removed."""
    combos = load_combos()
    new_combos = [c for c in combos if c.name != name]
    if len(new_combos) == len(combos):
        return False
    save_combos(new_combos)
    return True

def resolve_combo(name: str, pool_snap: dict, *, strategy: Optional[str] = None, threshold: float = 0.05) -> dict:
    """
    Resolve a combo to actual models based on availability.
    """
    combo = get_combo(name)
    if not combo:
        used_strategy = strategy or "fallback"
        return {
            "combo": name,
            "strategy": used_strategy,
            "picked": None if used_strategy == "fallback" else [],
            "fallback": [],
            "drained": [],
            "reason": f"Combo '{name}' not found"
        }
        
    used_strategy = strategy or combo.kind
    drained = []
    available_models = []
    
    accounts = pool_snap.get("accounts", {})
    
    for model in combo.models:
        model_available = False
        for acct_data in accounts.values():
            m_data = acct_data.get("models", {}).get(model, {})
            remaining = m_data.get("remaining", 0.0)
            if remaining >= threshold:
                model_available = True
                break
        
        if model_available:
            available_models.append(model)
        else:
            drained.append(model)
            
    if used_strategy == "fallback":
        picked = available_models[0] if available_models else None
        fallback_list = available_models[1:] if available_models else []
        return {
            "combo": name,
            "strategy": "fallback",
            "picked": picked,
            "fallback": fallback_list,
            "drained": drained,
            "reason": "OK" if picked else "All models drained"
        }
    else:
        return {
            "combo": name,
            "strategy": "fusion",
            "picked": available_models,
            "fallback": [],
            "drained": drained,
            "reason": "OK" if available_models else "All models drained"
        }

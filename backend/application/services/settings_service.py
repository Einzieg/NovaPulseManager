from __future__ import annotations

from typing import Any

from backend.models.Config import Config


class SettingsService:
    @staticmethod
    def _blob_to_bool(value: Any, default: bool = True) -> bool:
        if isinstance(value, (bytes, memoryview)):
            try:
                return bool(int.from_bytes(bytes(value), "big"))
            except Exception:
                return default
        if isinstance(value, bool):
            return value
        return default

    def get_config(self) -> dict[str, Any]:
        cfg, _ = Config.get_or_create(id=1)
        return {
            "dark_mode": self._blob_to_bool(cfg.dark_mode, True),
            "cap_tool": cfg.cap_tool or "MuMu",
            "touch_tool": cfg.touch_tool or "MaaTouch",
            "email": cfg.email,
            "password": cfg.password,
            "receiver": cfg.receiver,
        }

    def update_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        cfg, _ = Config.get_or_create(id=1)
        allowed = {"dark_mode", "cap_tool", "touch_tool", "email", "password", "receiver"}
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key == "dark_mode":
                cfg.dark_mode = int(bool(value)).to_bytes(1, "big")
            else:
                setattr(cfg, key, value)
        cfg.save()
        return self.get_config()

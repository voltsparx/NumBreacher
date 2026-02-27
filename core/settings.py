import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class FrameworkSettings:
    profile: str = "beginner"
    owner_lookup_enabled: bool = True
    engine_name: str = "threading"
    max_workers: int = 8
    auto_summary_after_bulk: bool = True
    dedupe_bulk_numbers: bool = True
    bulk_output_mode: str = "full"
    runbook_stop_on_error: bool = False
    show_beginner_tips: bool = True

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, payload):
        allowed = set(cls.__dataclass_fields__.keys())
        filtered = {key: value for key, value in payload.items() if key in allowed}
        return cls(**filtered)

    def apply_profile(self, name):
        normalized = str(name or "").strip().lower()
        if normalized not in PROFILE_PRESETS:
            raise ValueError(
                f"Unknown profile '{name}'. Available: {', '.join(sorted(PROFILE_PRESETS))}"
            )

        preset = PROFILE_PRESETS[normalized]
        for key, value in preset.items():
            setattr(self, key, value)
        self.profile = normalized

    def save(self, file_path):
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=4)

    @classmethod
    def load(cls, file_path):
        path = Path(file_path)
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Settings file must contain a JSON object.")
        return cls.from_dict(payload)


PROFILE_PRESETS = {
    "beginner": {
        "owner_lookup_enabled": True,
        "engine_name": "threading",
        "max_workers": 6,
        "auto_summary_after_bulk": True,
        "dedupe_bulk_numbers": True,
        "bulk_output_mode": "full",
        "runbook_stop_on_error": False,
        "show_beginner_tips": True,
    },
    "professional": {
        "owner_lookup_enabled": True,
        "engine_name": "async",
        "max_workers": 16,
        "auto_summary_after_bulk": True,
        "dedupe_bulk_numbers": True,
        "bulk_output_mode": "compact",
        "runbook_stop_on_error": True,
        "show_beginner_tips": False,
    },
    "speed": {
        "owner_lookup_enabled": False,
        "engine_name": "async",
        "max_workers": 24,
        "auto_summary_after_bulk": False,
        "dedupe_bulk_numbers": True,
        "bulk_output_mode": "silent",
        "runbook_stop_on_error": True,
        "show_beginner_tips": False,
    },
    "deep": {
        "owner_lookup_enabled": True,
        "engine_name": "threading",
        "max_workers": 10,
        "auto_summary_after_bulk": True,
        "dedupe_bulk_numbers": False,
        "bulk_output_mode": "full",
        "runbook_stop_on_error": True,
        "show_beginner_tips": False,
    },
}

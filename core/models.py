from dataclasses import asdict, dataclass


@dataclass
class ScanResult:
    number: str
    geo: dict[str, str]
    carrier: str
    line_type: str
    formats: dict[str, str]
    voip: bool
    risk: str
    owner: dict[str, object]
    reputation: dict[str, str]
    osint: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

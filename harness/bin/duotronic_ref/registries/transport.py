"""Transport profile registry (Witness Contract Transport §6)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransportProfile:
    profile_id: str
    version: str
    declares_numeric_zero: bool
    requires_replay_key: bool
    notes: str = ""


class TransportRegistry:
    def __init__(self, profiles: list[TransportProfile]) -> None:
        self._profiles = {(p.profile_id, p.version): p for p in profiles}

    def resolve(self, profile_id: str, version: str = "v1") -> TransportProfile:
        try:
            return self._profiles[(profile_id, version)]
        except KeyError as exc:
            raise KeyError(f"unknown transport profile {profile_id}@{version}") from exc

    def all(self) -> list[TransportProfile]:
        return list(self._profiles.values())


TRANSPORT_REGISTRY = TransportRegistry(
    [
        TransportProfile(
            profile_id="dbp-minsafe",
            version="v1",
            declares_numeric_zero=False,
            requires_replay_key=True,
            notes="Minimum-safe Duotronic Bus Profile.",
        ),
        TransportProfile(
            profile_id="dbp-strict",
            version="v1",
            declares_numeric_zero=True,
            requires_replay_key=True,
            notes="Strict Duotronic Bus Profile (declares numeric zero).",
        ),
        TransportProfile(
            profile_id="dbp-cluster-full-duplex-v1",
            version="v1",
            declares_numeric_zero=False,
            requires_replay_key=True,
            notes="v1.5 cluster full-duplex inter-node profile.",
        ),
    ]
)

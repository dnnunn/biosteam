from __future__ import annotations

from typing import Optional


class AIProvider:
    def summarize_source(self, url: str) -> str:
        raise NotImplementedError

    def extract_recipe(self, text: str) -> dict:
        raise NotImplementedError

    def explain_delta(self, old: dict, new: dict) -> str:
        raise NotImplementedError


class NullAIProvider(AIProvider):
    def summarize_source(self, url: str) -> str:  # pragma: no cover
        return ""

    def extract_recipe(self, text: str) -> dict:  # pragma: no cover
        return {}

    def explain_delta(self, old: dict, new: dict) -> str:  # pragma: no cover
        return ""


def get_provider(name: Optional[str] = None) -> AIProvider:
    # Placeholder shim; returns a no-op provider to keep runtime deterministic.
    _ = name  # future: dispatch to configured backend
    return NullAIProvider()


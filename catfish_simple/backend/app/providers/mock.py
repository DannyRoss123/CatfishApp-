import random
from typing import List

from .base import ReverseImageMatch, ReverseImageProvider


class MockReverseImageProvider(ReverseImageProvider):
    """Returns deterministic pseudo-matches for local testing."""

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)

    def search(self, image_bytes: bytes) -> List[ReverseImageMatch]:
        # 25% chance to return a mock reuse match
        if self.random.random() < 0.25:
            similarity = round(self.random.uniform(0.6, 0.95), 2)
            return [
                ReverseImageMatch(
                    similarity=similarity,
                    source_url="https://example.com/profile/123",
                    description="Found on dating profile aggregator",
                )
            ]
        return []

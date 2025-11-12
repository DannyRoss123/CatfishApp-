from dataclasses import dataclass
from typing import List


@dataclass
class ReverseImageMatch:
    similarity: float  # 0-1
    source_url: str
    description: str | None = None


class ReverseImageProvider:
    def search(self, image_bytes: bytes) -> List[ReverseImageMatch]:
        raise NotImplementedError

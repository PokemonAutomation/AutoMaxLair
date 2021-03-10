from typing import Dict


class Ball():
    """Represents a ball. Contains one id and names in multiple languages."""

    def __init__(
        self,
        name_id: str,
        names: Dict[str, str]
    ) -> None:
        self.name_id = name_id
        self.names = names

    def __str__(self) -> str:
        return self.name_id

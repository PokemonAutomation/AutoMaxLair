from typing import Dict


class Ball():
    """Represent a ball. Contains one id and one translation for each language"""

    def __init__(
        self,
        name_id: str,
        names: Dict[str, str]
    ) -> None:
        self.name_id = name_id
        self.names = names

class MotherNotFoundError(Exception):
    """Raised when a write references a mother that does not exist (or was soft-deleted)."""

    def __init__(self, mother_id: str) -> None:
        super().__init__(f"Mother {mother_id} not found.")
        self.mother_id = mother_id

class NevaraError(Exception):
    """Base exception for the Nevara SDK."""


class NevaraAPIError(NevaraError):
    """Raised when the Nevara API returns an unsuccessful response."""

    def __init__(self, status_code: int, message: str, response_body: str = "") -> None:
        super().__init__(f"Nevara API error {status_code}: {message}")
        self.status_code = status_code
        self.message = message
        self.response_body = response_body

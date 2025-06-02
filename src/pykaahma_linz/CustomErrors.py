"""
CustomErrors.py
Custom exceptions for the Koordinates module.
"""

class KServerError(Exception):
    """Custom exception for errors encountered when connecting to a Koordinates server."""
    pass
class KServerBadRequestError(KServerError):
    """Raised when a 400 Bad Request is returned from the Koordinates server."""
    pass

class KUnknownItemTypeError(Exception):
    """Raised when an unknown item type is encountered."""
    pass
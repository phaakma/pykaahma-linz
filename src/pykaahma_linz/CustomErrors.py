"""
CustomErrors.py
Custom exceptions for the Koordinates module.
"""

class KServerError(Exception):
    """
    Exception raised for errors encountered when connecting to a Koordinates server.

    Used to signal general server-side or connection errors.

    Attributes:
        message (str): Description of the error.
    """

class KServerBadRequestError(KServerError):
    """
    Exception raised when a 400 Bad Request is returned from the Koordinates server.

    Used to signal invalid requests or parameters.

    Attributes:
        message (str): Description of the error.
    """

class KUnknownItemTypeError(Exception):
    """
    Exception raised when an unknown item type is encountered.

    Used to signal that an item kind is not supported by the client.

    Attributes:
        message (str): Description of the error.
    """
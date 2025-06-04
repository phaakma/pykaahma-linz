"""
KItem.py
A base class to represent an item.
"""


class KItem:
    """
    Base class for representing an item in the Koordinates system.

    This class provides a structure for items that can be extended by specific item types.
    It stores basic metadata and provides dynamic attribute access.

    Attributes:
        _kserver (KServer): The KServer instance this item belongs to.
        _raw_json (dict): The raw JSON dictionary representing the item.
        id (str): The unique identifier of the item.
        url (str): The URL of the item.
        type (str): The type of the item (e.g., 'layer', 'table').
        kind (str): The kind of the item (e.g., 'vector', 'table').
        title (str): The title of the item.
        description (str): The description of the item.
        _jobs (list): List of JobResult objects associated with this item.
    """

    def __init__(self, kserver: "KServer", item_dict: dict) -> None:
        """
        Initializes the KItem instance from a dictionary returned from the API.

        Parameters:
            kserver (KServer): The KServer instance that this item belongs to.
            item_dict (dict): A dictionary containing the item's details, typically from an API response.

        Returns:
            None
        """
        self._kserver = kserver
        self._raw_json = item_dict
        self.id = item_dict.get("id")
        self.url = item_dict.get("url")
        self.type = item_dict.get("type")
        self.kind = item_dict.get("kind")
        self.title = item_dict.get("title")
        self.description = item_dict.get("description")
        self._jobs = []

    def __getattr__(self, item) -> object:
        """
        Provides dynamic attribute access for the item.

        Parameters:
            item (str): The name of the attribute to access.

        Returns:
            The value of the requested attribute, or None if it does not exist.
        """
        attr = self._raw_json.get(item, None)
        if attr is None:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{item}'")
        return attr

    def __repr__(self) -> str:
        return f"KItem(id={self.id}, title={self.title}, type={self.type})"

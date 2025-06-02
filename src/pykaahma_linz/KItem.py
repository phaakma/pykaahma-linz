"""
KItem.py
A base class to represent an item.
"""

class KItem:
    """
    A base class to represent an item in the Koordinates system.
    
    This class provides a structure for items that can be extended by specific item types.
    """

    def __init__(self, kserver: "KServer", item_dict: dict):
        """
        Initializes the KItem instance from a dict returned from the api.

        Args:
            item_dict (dict): A dictionary containing the item's details, typically from an API response.
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

    def __getattr__(self, item):
        """
        Provides dynamic attribute access for the item.

        Args:
            item (str): The name of the attribute to access.

        Returns:
            The value of the requested attribute, or None if it does not exist.
        """
        attr = self._raw_json.get(item, None)
        if attr is None:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{item}'")
        return attr


    def __repr__(self):
        return f"KItem(id={self.id}, title={self.title}, type={self.type})"


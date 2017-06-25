"""
ActionCable message
"""

import json


class Message:
    """
    A subscription message.
    """
    def __init__(self, action, data):
        self.action = action
        self.data = data

    def message(self):
        """
        The message properly
        formatted.
        """
        message = self.data
        message['action'] = self.action
        return message

    def raw_message(self):
        """
        The message formatted
        and dumped.
        """
        return json.dumps(self.message())

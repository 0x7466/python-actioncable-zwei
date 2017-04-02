import json


class Message:
  """
  A subscription message.
  """
  def __init__(self, action, data):
    self.action = action
    self.data = data

  def message(self):
    message = self.data
    message['action'] = self.action
    return message

  def raw_message(self):
    return json.dumps(self.message())

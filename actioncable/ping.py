import time


class Ping:
  """
  A ping
  """
  def __init__(self):
    self.local_timestamp = time.mktime(time.gmtime())

  @property
  def healthy(self):
    difference_current_time = time.mktime(time.gmtime()) - self.local_timestamp
    return difference_current_time < 6

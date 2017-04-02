import threading
import uuid
import logging
import time

from .ping import Ping


class ConnectionMonitor:
  """
  Monitors the connection and reestablishes
  the connection if lost.
  """
  def __init__(self, connection):
    self.connection = connection

    self.stale_threshold = 6
    self.last_ping = Ping()
    self.started = False

  def start(self):
    if self.started:
      return

    self.started = True
    self.thread = threading.Thread(name="APIConnectionMonitorThread_{}".format(uuid.uuid1()), target=self._run_forever)
    self.thread.daemon = True
    self.thread.start()

    logging.debug('ACTIONCABLE MONITOR : Started.')

  def stop(self):
    self.started = False

    logging.debug('ACTIONCABLE MONITOR : Stopped.')

  def _run_forever(self):
    while self.started:
      if self.connection.state == 'disconnected':
        time.sleep(1)
        continue

      if not self.last_ping.healthy:
        logging.warning('ACTIONCABLE MONITOR : Connection Ping unhealthy! Reconnect...')
        self.connection.connect()
        self.last_ping = Ping()
      
      time.sleep(1)

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
    self.last_ping = None
    self.thread = None
    self.started = False
    self.failure_rounds = 0
    self.connection_failed = False

    self.logger = logging.getLogger('ActionCable Monitor')

  def start(self):
    self.logger.debug('Start monitor...')

    if self.started:
      self.logger.warning('Monitor already started. Return.')
      return

    self.started = True
    self.last_ping = Ping()
    
    self.thread = threading.Thread(name="APIConnectionMonitorThread_{}".format(uuid.uuid1()), target=self._run_forever)
    self.thread.daemon = True
    self.thread.start()

  def stop(self):
    self.logger.debug('Stop monitor...')

    if self.started:
      self.started = False
    else:
      self.logger.warning('Monitor not started.')

  def restart(self):
    """
    Restarts the monitor.
    """
    self.logger.debug('Restart monitor...')

    self.stop()
    self.start()

  def _run_forever(self):
    self.logger.debug('Start monitor loop.')

    failure_rounds_since_last_fix_attempt = 0

    try:
      while self.started:
        fix = False

        if not self.connection_failed:
          if not self.last_ping.healthy:
            self.logger.warning('Connection ping unhealthy! Try to reconnect...')
            fix = True
        else:
          if failure_rounds_since_last_fix_attempt >= 10:
            self.logger.warning('Connection still unhealthy! Try to reconnect...')
            failure_rounds_since_last_fix_attempt = 0
            fix = True
          
          failure_rounds_since_last_fix_attempt += 1

        if fix:
          self.connection_failed = True
          self.connection.reconnect()

        if self.connection_failed:
          if self.connection.connected:
            self.logger.info('Connection fixed.')
            self.last_ping = Ping()
            self.connection_failed = False
          else:
            self.failure_rounds += 1
            self.logger.warning('Connection dead for {} round/s.'.format(self.failure_rounds))
        
        if not self.connection_failed:
          failure_rounds_since_last_fix_attempt = 0
          self.failure_rounds = 0
        
        time.sleep(1)
    except:
      self.logger.error('Error in monitor loop. Restart monitor...')
      self.restart()













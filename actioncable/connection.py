import websocket
import threading
import uuid
import json
import logging

from .monitor import ConnectionMonitor
from .ping import Ping


class Connection:
  """
  The connection to a websocket server
  """
  def __init__(self, url, origin=None, log_ping=False):
    """
    :param url: The url of the cable server.
    :param origin: (Optional) The origin.
    :param log_ping: (Default: False) If true every
                      ping gets logged.
    """
    self.url = url
    self.origin = origin
    self.log_ping = log_ping

    self.logger = logging.getLogger('ActionCable Connection')

    self.subscriptions = {}

    self.monitor = ConnectionMonitor(self)

    self.ws = websocket.WebSocketApp(self.url, on_message=self._on_message, on_close=self._on_close)
    self.ws.on_open = self._on_open

    self.ws_thread = None

    if origin is not None:
      self.origin = origin


  def __del__(self):
    if self.monitor is not None:
      self.monitor.stop()

  def connect(self, origin=None):
    """
    Connects to the server.

    :param origin: (Optional) The origin.
    """
    self.logger.debug('Establish connection...')

    if self.connected:
      self.logger.warn('Connection already established. Return...')
      return

    if origin is not None:
      self.origin = origin

    # Small workaround for bug in websocket library.
    # This property gets set at init of the instance
    # but never reset after disconnect. So if you try
    # to reconnect the connection gets closed immediately.
    self.ws.keep_running = True

    self.ws_thread = threading.Thread(name="APIConnectionThread_{}".format(uuid.uuid1()), target=self._run_forever)
    self.ws_thread.daemon = True
    self.ws_thread.start()
    
    if not self.monitor.started:
      self.monitor.start()

  def disconnect(self, stop_monitor=True):
    """
    Closes the connection.
    """
    self.logger.debug('Close connection...')

    self.ws.close()
    
    if stop_monitor and self.monitor.started:
      self.monitor.stop()

  def reconnect(self):
    """
    Reconnect to server.
    """
    self.logger.debug('Reconnect...')

    for subscription in self.subscriptions.values():
      if subscription.state == 'subscribed':
        subscription.state = 'connection_pending'

    self.disconnect(stop_monitor=False)

    while self.socket_present:
      # Block until the socket is removed
      pass

    self.connect()

  def _run_forever(self):
    self.logger.debug('Run connection loop.')
    self.ws.run_forever(origin=self.origin)

  def send(self, data):
    """
    Sends data to the server.
    """
    self.logger.debug('Send data: {}'.format(data))

    if not self.connected:
      self.logger.warn('Connection not established. Return...')
      return

    self.ws.send(json.dumps(data))

  def _on_open(self, ws):
    """
    Called when the connection is open.
    """
    self.logger.debug('Connection established.')


  def _on_message(self, ws, message):
    """
    Called aways when a message arrives.
    """
    data = json.loads(message)
    message_type = None
    identifier = None
    subscription = None

    if 'type' in data:
      message_type = data['type']

    if 'identifier' in data:
      identifier = json.loads(data['identifier'])

    if identifier is not None:
      subscription = self.find_subscription(identifier)

    if subscription is not None:
      subscription.received(data)
    elif message_type == 'welcome':
      self.logger.debug('Welcome message received.')

      for subscription in self.subscriptions.values():
        if subscription.state == 'connection_pending':
          subscription.create()

    elif message_type == 'ping':
      ping = Ping()
      self.monitor.last_ping = ping

      if self.log_ping:
        self.logger.debug('Ping received.')
    else:
      self.logger.warning('Message not supported.')

  def _on_close(self, ws):
    """
    Called when the connection was closed.
    """
    self.logger.debug('Connection closed.')

    for subscription in self.subscriptions.values():
      if subscription.state == 'subscribed':
        subscription.state = 'connection_pending'

  @property
  def socket_present(self):
    return self.ws.sock is not None

  @property
  def connected(self):
    return self.ws.sock is not None and self.ws.sock.connected

  def find_subscription(self, identifier):
    for subscription in self.subscriptions.values():
      if subscription.identifier == identifier:
        return subscription

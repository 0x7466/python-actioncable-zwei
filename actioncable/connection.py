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

    self.state = 'disconnected'
    self.subscriptions = {}

    self.ws = None
    self.ws_thread = None

    self.monitor = ConnectionMonitor(self)
    self.monitor.start()

  def __del__(self):
    if self.monitor is not None:
      self.monitor.stop()

  def connect(self, origin=None):
    """
    Connects to the server.

    :param origin: (Optional) The origin.
    """
    self.state = 'connect'

    if origin is not None:
      self.origin = origin

    self.ws = websocket.WebSocketApp(self.url, on_message=self._on_message, on_close=self._on_close)
    self.ws.on_open = self._on_open

    self.ws_thread = threading.Thread(name="APIConnectionThread_{}".format(uuid.uuid1()), target=self._run_forever)
    self.ws_thread.daemon = True
    self.ws_thread.start()


    logging.debug('ACTIONCABLE CONNECTION : Connect...')

  def disconnect(self):
    """
    Closes the connection.
    """
    self.state = 'disconnect'

    self.ws.close()

    logging.debug('ACTIONCABLE CONNECTION : Close connection...')

  def reconnect(self):
    """
    Reconnect to server.
    """
    for subscription in self.subscriptions.values():
      if subscription.state == 'subscribed':
        subscription.state = 'connection_pending'

    self.connect()

  def _run_forever(self):
    self.ws.run_forever(origin=self.origin)

  def send(self, data):
    """
    Sends data to the server.
    """
    self.ws.send(json.dumps(data))

  def _on_open(self, ws):
    """
    Called when the connection is open.
    """
    self.state = 'connected'

    logging.debug('ACTIONCABLE CONNECTION : Connected.')

  def _on_message(self, ws, message):
    """
    Called aways when a message arrives.
    """
    self.state = 'connected'

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
      logging.debug('ACTIONCABLE : Welcome message received.')

      for subscription in self.subscriptions.values():
        if subscription.state == 'connection_pending':
          subscription.create()

    elif message_type == 'ping':
      ping = Ping()
      self.monitor.last_ping = ping

      if self.log_ping:
        logging.debug('ACTIONCABLE : Ping received.')
    else:
      logging.warning('ACTIONCABLE : Message not supported.')

  def _on_close(self, ws):
    """
    Called when the connection was closed.
    """
    if self.state == 'disconnect':
      self.state = 'disconnected'
    else:
      self.state = 'uncontrolled_disconnected'


    if self.state == 'uncontrolled_disconnected':
      logging.warning('ACTIONCABLE CONNECTION : Uncontrolled Disconnected.')
    else:
      logging.debug('ACTIONCABLE CONNECTION : Disconnected.')

    for subscription in self.subscriptions.values():
      if subscription.state == 'subscribed':
        subscription.state = 'connection_pending'


  def find_subscription(self, identifier):
    for subscription in self.subscriptions.values():
      if subscription.identifier == identifier:
        return subscription

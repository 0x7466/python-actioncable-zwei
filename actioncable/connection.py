"""
ActionCable connection.
"""

import threading
import uuid
import json
import logging
import time
import websocket


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

        self.websocket = None
        self.ws_thread = None

        self.auto_reconnect = False

        if origin is not None:
            self.origin = origin

    def connect(self, origin=None):
        """
        Connects to the server.

        :param origin: (Optional) The origin.
        """
        self.logger.debug('Establish connection...')

        if self.connected:
            self.logger.warning('Connection already established. Return...')
            return

        if origin is not None:
            self.origin = origin

        self.auto_reconnect = True

        self.ws_thread = threading.Thread(
            name="APIConnectionThread_{}".format(uuid.uuid1()),
            target=self._run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def disconnect(self):
        """
        Closes the connection.
        """
        self.logger.debug('Close connection...')

        self.auto_reconnect = False
        
        if self.websocket is not None:
            self.websocket.close()

    def _run_forever(self):
        while self.auto_reconnect:
            try:
                self.logger.debug('Run connection loop.')
                
                self.websocket = websocket.WebSocketApp(
                    self.url,
                    on_message=self._on_message,
                    on_close=self._on_close)
                self.websocket.on_open = self._on_open
                
                self.websocket.run_forever(ping_interval=5, ping_timeout=3, origin=self.origin)
                time.sleep(2)
            except Exception as exc:
                self.logger.error('Connection loop raised exception. Exception: %s', exc)

    def send(self, data):
        """
        Sends data to the server.
        """
        self.logger.debug('Send data: {}'.format(data))

        if not self.connected:
            self.logger.warning('Connection not established. Return...')
            return

        self.websocket.send(json.dumps(data))

    def _on_open(self, socket):
        """
        Called when the connection is open.
        """
        self.logger.debug('Connection established.')


    def _on_message(self, socket, message):
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
            if self.log_ping:
                self.logger.debug('Ping received.')
        else:
            self.logger.warning('Message not supported. (Message: {})'.format(message))

    def _on_close(self, socket):
        """
        Called when the connection was closed.
        """
        self.logger.debug('Connection closed.')

        for subscription in self.subscriptions.values():
            if subscription.state == 'subscribed':
                subscription.state = 'connection_pending'

    @property
    def socket_present(self):
        """
        If socket is present.
        """
        return self.websocket is not None and self.websocket.sock is not None

    @property
    def connected(self):
        """
        If connected to server.
        """
        return self.websocket is not None and \
               self.websocket.sock is not None and \
               self.websocket.sock.connected

    def find_subscription(self, identifier):
        """
        Finds a subscription
        by it's identifier.
        """
        for subscription in self.subscriptions.values():
            if subscription.identifier == identifier:
                return subscription

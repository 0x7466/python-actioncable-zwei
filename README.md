# ActionCableZwei - A Python 3 client for Rails' Action Cable

This library handles the connections and subscriptions and monitors the connection. It removes the underlaying websocket layer.

## Get started

```
$ sudo pip3 install ActionCableZwei
```

## Example usage

### Setup the connection
Setup the connection to your Action Cable server.

```python
from actioncable.connection import Connection

connection = Connection(url='wss://url_to_your_cable_server/cable', origin='https://url_to_your_cable_server')
connection.connect()
```

### Subscribe to a channel

```python
from actioncable.subscription import Subscription

subscription = Subscription(connection, identifier={'channel': 'AppChannel'})

def on_receive(message):
  print('New message arrived!')
  print('Action: {} | Data: {}'.format(message.action, message.data))

subscription.on_receive(callback=on_receive)
subscription.create()
```

### Send data

```python
from actioncable.message import Message

message = Message(action='update_something', data={'something': 'important'})

subscription.send(message)
```

### Unsubscribe

```python
subscription.remove()
```

### Close connection

```python
connection.disconnect()
```

## Development

Pull it up!

## You need help?

Ask a question on [StackOverflow](https://stackoverflow.com/) with the tag 'actioncable-zwei'.

## Things to do

 * **To test the package.**

Also here we would be thankful for pull requests.

## Contribution

Create pull requests on Github and help us to improve this gem. There are some guidelines to follow:

 * Follow the conventions
 * Test all your implementations
 * Document methods which aren't self-explaining

Copyright (c) 2017 Tobias Feistmantl, MIT license

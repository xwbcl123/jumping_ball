import pyglet

from pyglet.experimental import net


server = net.Server(address='0.0.0.0', port=1234)


def pong(connection, message):
    print(f"Received '{message}' from '{connection}'")
    connection.send(b'pong')


@server.event
def on_connection(connection):
    print(f"New client connected: {connection}")
    connection.set_handler('on_receive', pong)


@server.event
def on_disconnection(connection):
    print(f"Client disconnected: {connection}")


pyglet.app.run()

from pyglet.experimental import net


client = net.Client(address='localhost', port=1234)


@client.event
def on_receive(message):
    print(f"Received: {message}")


@client.event
def on_disconnect(message):
    print(f"Received: {message}")


client.send(b'ping')


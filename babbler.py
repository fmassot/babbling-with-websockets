# -*- coding: utf-8 -*-

import os
import redis
import gevent
import logging
from logging.handlers import RotatingFileHandler
from twitter import OAuth
from twitter_stream import StreamFactory
from flask import Flask, render_template
from flask_sockets import Sockets
from ConfigParser import ConfigParser

config = ConfigParser()
config.read('config.cfg')

# Flask
app = Flask(__name__)
app.debug = 'DEBUG' in os.environ
handler = RotatingFileHandler('babbler.log')
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
sockets = Sockets(app)

# Redis
redis = redis.StrictRedis(host='localhost', port=6379, db=0)

def init_twitter_stream(config, redis):
    """Create a greenlet for twitter stream"""
    auth = OAuth(
        consumer_key=config.get('twitter', 'consumer_key'),
        consumer_secret=config.get('twitter', 'consumer_secret'),
        token=config.get('twitter', 'access_token'),
        token_secret=config.get('twitter', 'access_token_secret'),
    )

    stream = StreamFactory(auth, redis, config.get('redis', 'main_chan'), {'track':'python'})

    return stream

class ClientBackend(object):
    """Interface for registering and updating WebSocket clients with a redis subscriber
    """

    def __init__(self, redis_chan):
        self.clients = list()
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(redis_chan)

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                app.logger.info(u'Sending message: %s'%message)
                yield data

    def register(self, client):
        """Register a WebSocket connection for Redis updates."""
        self.clients.append(client)

    def send(self, client, data):
        """Send given data to the registered client.
Automatically discards invalid connections."""
        try:
            client.send(data)
        except Exception:
            app.logger.info(u"Removing client %s"%client)
            self.clients.remove(client)

    def run(self):
        """Listens for new messages in Redis, and sends them to clients."""
        for data in self.__iter_data():
            for client in self.clients:
                gevent.spawn(self.send, client, data)

    def start(self):
        """Maintains Redis subscription in the background."""
        gevent.spawn(self.run)

# Subscriber for clients
MAIN_CHAN = config.get('redis', 'main_chan')
backend = ClientBackend(MAIN_CHAN)
backend.start()

stream = init_twitter_stream(config, redis)
stream.start()


@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/twitterstream/track/<tracked_str>')
def track(tracked_str):
    stream.filters = {'track':tracked_str}
    stream.restart()
    return "Tracked", 200

@app.route('/twitterstream/start/')
def _start_stream():
    stream.restart()
    return "Restart", 200

@app.route('/twitterstream/stop/')
def stop_stream():
    stream.kill()
    return "Killed", 200

@sockets.route('/submit')
def inbox(ws):
    """Receives incoming chat messages, inserts them into Redis."""
    while ws.socket is not None:
        # Sleep to prevent *contstant* context-switches.
        gevent.sleep(0.1)
        message = ws.receive()

        if message:
            app.logger.info(u'Inserting message: %s'%message)
            redis.publish(MAIN_CHAN, message)

@sockets.route('/receive')
def outbox(ws):
    """Sends outgoing chat messages, via `ChatBackend`."""
    backend.register(ws)

    while ws.socket is not None:
        # Context switch while `ChatBackend.start` is running in the background.
        gevent.sleep()


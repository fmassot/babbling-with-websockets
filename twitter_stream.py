# -*- coding: utf-8 -*-

import json
from gevent import Greenlet
from twitter import TwitterStream

class StreamFactory(object):
    def __init__(self, auth, redis, chan, filters):
        self.auth = auth
        self.redis = redis
        self.chan = chan
        self.filters = filters
        self.g = None

    def start(self):
        if self.g is not None:
            raise "A greenlet is already there"
        self.g = Greenlet(self._start)
        self.g.start()
        return self.g

    def kill(self):
        if self.g is not None:
            self.g.kill()
            self.g = None

    def restart(self):
        self.kill()
        self.start()

    def _start(self):
        for tweet in TwitterStream(auth=self.auth).statuses.filter(**self.filters):
            # XXX: have to dump tweet, redis seems to do not know how to dump it itself.
            self.redis.publish(self.chan, json.dumps(tweet))




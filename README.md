Babbling with websockets
========================

Repo to show a dummy example to get a twitter stream on the server side and send
the stream to a web page with websockets. You can also send message.

I used flask and flask-sockets and get mainly inspired from [heroku example](https://github.com/heroku-examples/python-websockets-chat).


WARNING: I don't really know what I'm doing but it works...

Usage
=====

Set up the config in conf.cfg, there is an example in sample.cfg, just copy
paste it to conf.cfg and fill your twitter's settings.

Start the server:
`gunicorn -k flask_sockets.worker babbler:app`

Open http://localhost:8000 and that's it!


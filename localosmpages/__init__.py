from flask import Flask
from flask_oauthlib.client import OAuth
import os

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='show me the way, lazarus',
))
app.config.from_envvar('LOCALOSMPAGES_SETTINGS', silent=True)

oauth = OAuth()
osm = oauth.remote_app('osm',
    base_url='http://master.apis.dev.openstreetmap.org/api/0.6/',
    request_token_url='http://master.apis.dev.openstreetmap.org/oauth/request_token',
    access_token_url='http://master.apis.dev.openstreetmap.org/oauth/access_token',
    authorize_url='http://master.apis.dev.openstreetmap.org/oauth/authorize',
    consumer_key='QiOymJuVbbnWaJKwOWFL7gsdbubEN728sgspq6Og',
    consumer_secret='h3F5HLv5ZYZLKk4tUPNI5fjYKVJFQhjL0lTujkz3'
)

import localosmpages.views
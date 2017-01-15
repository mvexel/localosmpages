import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash
from xml.etree import ElementTree
from functools import wraps
import json
from datetime import datetime

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'localosmpages.db'),
    SECRET_KEY='show me the way, lazarus',
))
app.config.from_envvar('LOCALOSMPAGES_SETTINGS', silent=True)

from flask_oauthlib.client import OAuth

oauth = OAuth()
osm = oauth.remote_app('osm',
    base_url='http://master.apis.dev.openstreetmap.org/api/0.6/',
    request_token_url='http://master.apis.dev.openstreetmap.org/oauth/request_token',
    access_token_url='http://master.apis.dev.openstreetmap.org/oauth/access_token',
    authorize_url='http://master.apis.dev.openstreetmap.org/oauth/authorize',
    consumer_key='QiOymJuVbbnWaJKwOWFL7gsdbubEN728sgspq6Og',
    consumer_secret='h3F5HLv5ZYZLKk4tUPNI5fjYKVJFQhjL0lTujkz3'
)


# database stuff

def connect_db():
    '''Connects to the specific database.'''
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    '''Opens a new database connection if there is none yet for the
    current application context.
    '''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    '''Closes the database again at the end of the request.'''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    '''Initializes the database.'''
    init_db()
    print('Initialized the database.')

# decorators

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'osm_user' in session:
            return redirect(url_for('home', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# routes

@app.route('/')
def home():
    db = get_db()
    return render_template('home.html')

@app.route('/login')
def login():
    return osm.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
def oauth_authorized():
    next_url = request.args.get('next') or url_for('index')
    resp = osm.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    session['osm_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )

    user_data = osm.get('user/details').data
    user = OSMUser.from_xml(user_data)
    print("USER:", user)
    session['osm_user'] = user

    flash('You were signed in as {username}'.format(
        username=session['osm_user'].display_name))
    return redirect(next_url)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/logout')
def logout():
    session.pop('osm_user', None)
    flash('You were logged out')
    return redirect(url_for('home'))

@osm.tokengetter
def get_osm_token(token=None):
    return session.get('osm_token')


class OSMUser(dict):

    def __init__(self, **kwargs):
        dict.__init__(self, **kwargs)
        self.osmid = kwargs.get('osmid', None)
        self.display_name = kwargs.get('display_name', None)
        self.changeset_count = int(kwargs.get('changeset_count', None))
        self.avatar_url = kwargs.get('avatar_url', None)
        self.account_created = kwargs.get('account_created', None)
        self.contributor_terms_agreed = kwargs.get('contributor_terms_agreed', None)
        self.pd = kwargs.get('pd', None)
        self.traces_count = kwargs.get('traces_count', None)
        self.blocks_received = kwargs.get('blocks_received', None)
        self.blocks_active = kwargs.get('blocks_active', None)
        self.languages = kwargs.get('languages', [])
        self.messages_received = kwargs.get('messages_received', None)
        self.messages_unread = kwargs.get('messages_unread', None)
        self.messages_sent = kwargs.get('messages_sent', None)
        self.join_date = kwargs.get('join_date', None)
        self.last_active = kwargs.get('last_active', None)
        self.non_local = kwargs.get('non_local', None)
        self.is_new = kwargs.get('is_new', None)

        # sync dates
        join_date = osm.get('user/preferences/osmlocalpages_join_date').data
        app.logger.debug(join_date)
        if join_date == b'':
            app.logger.debug('new user')
            self.is_new = True
            self.join_date = str(datetime.now())
            osm.put('user/preferences/osmlocalpages_join_date', data=self.join_date, content_type='text/plain')
        else:
            self.join_date = join_date
            self.is_new = False
        app.logger.debug(self.is_new)
        self.last_active = str(datetime.now())
        osm.put('user/preferences/osmlocalpages_last_active', data=self.last_active, content_type='text/plain')


    @classmethod
    def from_xml(cls, elem):
        try:
            user = elem.find('user')
            return cls(
                osmid=int(user.attrib['id']),
                display_name=user.attrib['display_name'],
                changeset_count=user.find('changesets').attrib['count'],
                avatar_url=user.find('img').attrib['href'].split('?')[0].replace('http','https'),
                account_created=user.attrib['account_created'],
                contributor_terms_agreed=bool(user.find('contributor-terms').attrib['agreed'] == 'true'),
                pd=bool(user.find('contributor-terms').attrib['pd'] == 'true'),
                traces_count=int(user.find('traces').attrib['count']),
                blocks_received=int(user.find('blocks').find('received').attrib['count']),
                blocks_active=int(user.find('blocks').find('received').attrib['active']),
                languages=[elem.text for elem in user.find('languages')],
                messages_received=int(user.find('messages').find('received').attrib['count']),
                messages_unread=int(user.find('messages').find('received').attrib['unread']),
                messages_sent=int(user.find('messages').find('sent').attrib['count']))
        except Exception as e:
            raise e

    def __str__(self):
        return "OSMUSer {osmid} ({display_name})".format(
            osmid=self.osmid,
            display_name=self.display_name)


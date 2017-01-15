from localosmpages import app, osm, database, user
from functools import wraps
from flask import redirect, url_for, session, request, render_template, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'user' in session:
            return redirect(url_for('home', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    db = database.get_db()
    return render_template('home.html')

@app.route('/login')
def login():
    return osm.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
def oauth_authorized():
    next_url = request.args.get('next') or url_for('home')
    resp = osm.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    # store OAuth tokens in session
    session['osm_token'] = (
        resp['oauth_token'],
        resp['oauth_token_secret']
    )

    # Retrieve user details, store in session as well
    user.sync()
    session['user'] = user.config

    flash('You were signed in as {username}'.format(
        username=user.config['display_name']))
    return redirect(next_url)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You were logged out')
    return redirect(url_for('home'))

@osm.tokengetter
def get_osm_token(token=None):
    return session.get('osm_token')


from localosmpages import app, osm, user
from functools import wraps
from flask import redirect, url_for, session, request, render_template, flash

# Decorators

def login_required(f):
    '''Decorator for routes only accessible by logged in users'''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'user' in session:
            flash(u'You need to be logged in for this.')
            return redirect(url_for('home', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    '''Homepage'''
    return render_template('home.html')

@app.route('/login')
def login():
    '''Redirect to OSM Oauth for login'''
    return osm.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
def oauth_authorized():
    '''Callback route for OSM OAuth'''
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

@app.route('/profile')
@login_required
def profile():
    '''TODO a profile page'''
    return render_template('profile.html')

@app.route('/logout')
def logout():
    '''Log the user out (delete user from session)'''
    session.pop('user', None)
    flash('You were logged out')
    return redirect(url_for('home'))

@osm.tokengetter
def get_osm_token(token=None):
    '''The tokengetter for OAuthlib'''
    return session.get('osm_token')

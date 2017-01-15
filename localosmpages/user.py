from localosmpages import app, osm
import json
from datetime import datetime
from dateutil import parser

config = {
    'osmid': None,
    'display_name': None,
    'changeset_count': None,
    'avatar_url': None,
    'account_created': None,
    'contributor_terms_agreed': None,
    'pd': None,
    'traces_count': None,
    'blocks_received': None,
    'blocks_active': None,
    'languages': None,
    'messages_received': None,
    'messages_unread': None,
    'is_new': None,
    'joined_date': None,
    'last_active': None
}

def sync():
    '''Sync the user with what osm.org knows'''
    user_data = osm.get('user/details').data
    elem = user_data.find('user')
    config['osmid']=int(elem.attrib['id'])
    config['display_name']=elem.attrib['display_name']
    config['changeset_count']=elem.find('changesets').attrib['count']
    config['avatar_url']=elem.find('img').attrib['href'].split('?')[0].replace('http','https')
    config['account_created']=elem.attrib['account_created']
    config['contributor_terms_agreed']=bool(elem.find('contributor-terms').attrib['agreed'] == 'true')
    config['pd']=bool(elem.find('contributor-terms').attrib['pd'] == 'true')
    config['traces_count']=int(elem.find('traces').attrib['count'])
    config['blocks_received']=int(elem.find('blocks').find('received').attrib['count'])
    config['blocks_active']=int(elem.find('blocks').find('received').attrib['active'])
    config['languages']=[elem.text for elem in elem.find('languages')]
    config['messages_received']=int(elem.find('messages').find('received').attrib['count'])
    config['messages_unread']=int(elem.find('messages').find('received').attrib['unread'])
    config['messages_sent']=int(elem.find('messages').find('sent').attrib['count'])
    config['is_new']=False

    # sync join and active dates with OSM
    join_date = osm.get('user/preferences/osmlocalpages_join_date').data.decode('utf-8')
    if join_date == b'':
        # If it does not exist, we have a new user.
        app.logger.debug('new user')
        join_date = str(datetime.now())
        osm.put(
            'user/preferences/osmlocalpages_join_date',
            data=join_date,
            content_type='text/plain')
        config['is_new'] = True
    config['join_date'] = join_date

    last_active = str(datetime.now())
    osm.put(
        'user/preferences/osmlocalpages_last_active',
        data=last_active,
        content_type='text/plain')
    config['last_active'] = last_active

    app.logger.debug(config['join_date'])
    app.logger.debug(config['last_active'])

import imp
import os
import yaml
import subprocess


def compose_connection_string(user, password, host, dbName):
    # results in ParseResult(scheme='mysql', netloc='root:vagrant@localhost',
    # path='/wiki', params='', query='', fragment='')
    return 'mysql://' + user + ':' + password + '@' + host + '/' + dbName


def parse_db_connection_string(urlConnectionString):
    """
    From a url like: mysql://wikimetrics:wikimetrics@localhost/wikimetrics
    exracts user, password, host, dbName
    """
    from urlparse import urlparse
    parsed = urlparse(urlConnectionString)
    # results in
    # ParseResult(scheme='mysql', netloc='root:vagrant@localhost',
    # path='/wiki', params='', query='', fragment='')
    netloc = parsed.netloc
    user = netloc.split(':')[0]
    password, host = netloc.split(':')[1].split('@')
    dbName = parsed.path.split('/')[1]
    return user, password, host, dbName


def setup_testing_config(db_config):
    override_file = 'wikimetrics/config/test_config.yaml'
    config_override = create_dict_from_text_config_file(override_file)
    test_config = update_config_from_override(db_config, config_override)

    test_config['PROJECT_HOST_NAMES'] = get_project_host_names_local()
    return test_config


def get_project_host_names_local():
    """"
    In tests and local projectnames are hardcoded
    """
    return ['wiki', 'dewiki', 'enwiki']


def update_config_from_override(default_config_dict, override_config_dict):
    """
    Update a given dictionary values with settings on other dictionary.
    Used to override the configuration
    """
    for k in iter(default_config_dict):
        if k in override_config_dict:
            default_config_dict[k] = override_config_dict[k]
    return default_config_dict


# TODO: does not work in labs environment
def create_object_from_config_file(path):
    dir, fname = os.path.split(path)
    return imp.load_source(os.path.splitext(fname)[0], path)


def create_dict_from_text_config_file(path):
    yaml_string = open(path).read()
    return yaml.load(yaml_string)


class FromDictionary(object):
    def __init__(self, **entries):
        self.__dict__.update(entries)


def create_object_from_text_config_file(path):
    yaml_string = open(path).read()
    yaml_dict = yaml.load(yaml_string)
    return FromDictionary(**yaml_dict)


def config_web(args):
    from flask import Flask, request, json
    from flask.ext.login import LoginManager
    from flask.ext.oauth import (
        OAuth, OAuthRemoteApp, OAuthException, get_etree
    )
    from werkzeug import url_decode, parse_options_header
    import flask.ext.oauth as nasty_patch_to_oauth

    global app
    app = Flask('wikimetrics')
    # note absolute_path does not change on the life of the application
    app.absolute_path_to_app_root = get_absolute_path()
    # TODO do we need this config to be created like an object instead of a dictionary?
    web_config = create_object_from_text_config_file(args.web_config)
    # if args.override_config:
    # override_config = create_object_from_text_config_file(args.override_config)
    # TODO override one obj with other, can we use dict?

    app.config.from_object(web_config)

    version, latest = get_wikimetrics_version()
    app.config['WIKIMETRICS_LATEST'] = latest
    app.config['WIKIMETRICS_VERSION'] = version
    
    global login_manager
    login_manager = LoginManager()
    login_manager.init_app(app)

    # TODO, this does not need to be a
    # global, could be stored in flask application context
    global google
    oauth = OAuth()
    google = oauth.remote_app(
        'google',
        base_url=app.config['GOOGLE_BASE_URL'],
        authorize_url=app.config['GOOGLE_AUTH_URI'],
        request_token_url=None,
        request_token_params={
            'scope': app.config['GOOGLE_AUTH_SCOPE'],
            'response_type': 'code',
        },
        access_token_url=app.config['GOOGLE_TOKEN_URI'],
        access_token_method='POST',
        access_token_params={
            'grant_type':
            'authorization_code'
        },
        consumer_key=app.config['GOOGLE_CLIENT_ID'],
        consumer_secret=app.config['GOOGLE_CLIENT_SECRET'],
    )

    def better_parse_response(resp, content, strict=False):
        ct, options = parse_options_header(resp['content-type'])
        if ct in ('application/json', 'text/javascript'):
            try:
                return json.loads(content)
            # handle json decode errors from parse_response
            # this is useful in the identify call because the response is
            # 'application/json' but the content is encoded
            except:
                return content
        elif ct in ('application/xml', 'text/xml'):
            # technically, text/xml is ascii based but because many
            # implementations get that wrong and utf-8 is a superset
            # of utf-8 anyways, so there is not much harm in assuming
            # utf-8 here
            charset = options.get('charset', 'utf-8')
            return get_etree().fromstring(content.decode(charset))
        elif ct != 'application/x-www-form-urlencoded':
            if strict:
                return content
        charset = options.get('charset', 'utf-8')
        return url_decode(content, charset=charset).to_dict()

    # TODO: Even worse, definitely patch upstream or consider switching to rauth
    nasty_patch_to_oauth.parse_response = better_parse_response

    # TODO: patch upstream
    # NOTE: a million thanks to Merlijn_van_Deen, author of
    # https://wikitech.wikimedia.org/wiki/Setting_up_Flask_cgi_app_as_a_tool/OAuth
    class MediaWikiOAuthRemoteApp(OAuthRemoteApp):
        def handle_oauth1_response(self):
            """
            Handles an oauth1 authorization response.  The return value of
            this method is forwarded as the first argument to the handling
            view function.
            """
            client = self.make_client()
            resp, content = client.request(
                '{0}&oauth_verifier={1}'.format(
                    self.expand_url(self.access_token_url),
                    request.args['oauth_verifier'],
                ),
                self.access_token_method
            )
            data = nasty_patch_to_oauth.parse_response(resp, content)
            if not self.status_okay(resp):
                raise OAuthException(
                    'Invalid response from ' + self.name,
                    type='invalid_response',
                    data=data
                )
            return data

    global meta_mw
    meta_mw_base_url = app.config['META_MW_BASE_URL']
    meta_mw = MediaWikiOAuthRemoteApp(
        oauth,
        'meta_mw',
        base_url=meta_mw_base_url,
        request_token_url=meta_mw_base_url + app.config['META_MW_BASE_INDEX'],
        request_token_params={
            'title': 'Special:MWOAuth/initiate',
            'oauth_callback': 'oob'
        },
        access_token_url=meta_mw_base_url + app.config['META_MW_TOKEN_URI'],
        authorize_url=meta_mw_base_url + app.config['META_MW_AUTH_URI'],
        consumer_key=app.config['META_MW_CONSUMER_KEY'],
        consumer_secret=app.config['META_MW_CLIENT_SECRET'],
    )
    oauth.remote_apps['meta_mw'] = meta_mw


# TODO: look into making a single config object that has empty sections if
# some roles are not used (or maybe dependency injection)
def config_db(args):
    """
    Initializes the config object with what's passed in, further splits the config
    to get a user,password, host and dbName
    """
    from .database import Database

    db_config = create_dict_from_text_config_file(args.db_config)
    config_override = {}
    if args.override_config:
        config_override = create_dict_from_text_config_file(args.override_config)
        db_config = update_config_from_override(db_config, config_override)

    global db

    user, password, host, db_name = parse_db_connection_string(
        db_config['WIKIMETRICS_ENGINE_URL'])
    db_config['WIKIMETRICS'] = {
        'USER': user,
        'PASSWORD': password,
        'HOST': host,
        'DBNAME': db_name,
    }

    if db_config.get('DEBUG'):
        db_config['PROJECT_HOST_NAMES'] = get_project_host_names_local()

    db = Database(db_config)


def config_queue(args):
    from celery import Celery
    from celery.schedules import crontab
    from datetime import timedelta
    
    # create and configure celery app
    global queue
    queue = Celery('wikimetrics', include=['wikimetrics'])
    queue_config = create_dict_from_text_config_file(args.queue_config)
    if args.override_config:
        config_override = create_dict_from_text_config_file(args.override_config)
        queue_config = update_config_from_override(queue_config, config_override)
    queue.config_from_object(queue_config)
    
    schedules = queue.conf['CELERYBEAT_SCHEDULE']
    for key in schedules:
        schedule_type = schedules[key]['schedule']
        if schedule_type == 'daily':
            schedules[key]['schedule'] = crontab(minute=0, hour=0)
        elif schedule_type == 'test':
            schedules[key]['schedule'] = crontab(seconds=1)
        else:
            schedules[key]['schedule'] = timedelta(seconds=30)


def get_absolute_path():
    """
    Returns the path to the wikimetrics checkout root
    """
    return os.path.dirname(os.path.abspath(__file__)) + os.path.sep


def get_wikimetrics_version():
    """
    Returns
        a tuple of the form (pretty version string, latest commit sha)
    """
    path = get_absolute_path()
    orig_wd = os.getcwd()  # remember our original working directory
    try:
        os.chdir(path)
        cmd = [
            'git',
            'log',
            '--date',
            'relative',
            "--pretty=format:'%an %ar %h'",
            '-n',
            '1',
        ]
        p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        version, err = p.communicate()
        if err is not None:
            version = 'Unknown version'
        cmd = ['git', 'log', '--date', 'relative', "--pretty=format:%h", '-n', '1']
        p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE)
        latest, err = p.communicate()
        if err is not None:
            latest = 'unknown'
    except:
        pass
    finally:
        os.chdir(orig_wd)
    return version, latest

import os
from pathlib import Path
from datetime import datetime
from datetime import timedelta

import jwt
import tornado.web
import tornado.websocket
from utilities import db_utils
from utilities import cron_utils

class SocketBase(tornado.websocket.WebSocketHandler):
    def initialize(self, socket_manager):
        self.db_manager = db_utils.DatabaseManager(read_configuration())
        self.socket_manager = socket_manager

    def on_close(self):
        self.socket_manager.leave(self)

class BaseHandler(tornado.web.RequestHandler):
    SUPPORTED_METHODS = tornado.web.RequestHandler.SUPPORTED_METHODS + ('BREW',)

    def initialize(self, socket_manager=None):
        self.set_header('X-Frame-Options', 'DENY')
        self.set_header('X-XSS-Protection', '1; mode=block')
        self.set_header('X-Content-Type-Options', 'nosniff')
        self.set_header('Referrer-Policy', 'same-origin')
        self.set_header('Content-Security-Policy', 'default-src \'self\' \'unsafe-inline\'; img-src \'self\' data:;')

        if socket_manager is not None:
            self.socket_manager = socket_manager

    @tornado.web.removeslash
    def prepare(self):
        """
        Setup a database session, initialise application configuration,
        handle user sessions validation and verify user access rights.
        """
        self.system_configuration = read_configuration()
        self.settings['cookie_secret'] = self.system_configuration['cookie_secret']
        self.db_manager = db_utils.DatabaseManager(self.system_configuration)
        self.cron_manager = cron_utils.CRONManager()
        self.jwt_secret = self.system_configuration['jwt_secret']
        self.config = {
            'event_name': 'Event' # placeholder
        }
        redirect_exclusions = [
            '/',
            '/login',
            '/register'
        ]
        remote = bool('/remote' in self.request.uri)

        if self.current_user is None and self.request.uri not in redirect_exclusions and not remote:
            self.redirect('/')
            return
        elif self.current_user is not None:
            cur_user = self.current_user
            cur_user['exp'] = datetime.utcnow() + timedelta(hours=1)
            self.config['user'] = cur_user
            self.set_secure_cookie('user', self.encode_jwt(cur_user))

        if '/admin' in self.request.uri:
            if not self.current_user or cur_user['role'] != 'admin':
                self.redirect('/')

        if self.db_manager.get_error_state() is True:
            self.write('Database authentication failed.')
            self.finish()

    def get_current_user(self):
        cookie = self.get_secure_cookie('user')
        decoded_jwt = None

        if cookie is not None:
            try:
                decoded_jwt = jwt.decode(cookie, self.jwt_secret, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                self.redirect('/logout')
                return
            except jwt.DecodeError:
                self.redirect('/logout')
                return
        else:
            self.clear_all_cookies()

        return decoded_jwt

    def encode_jwt(self, payload):
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    @staticmethod
    def build_jwt_payload(user):
        return {
            '_id': str(user['_id']),
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'username': user['username'],
            'role': user['role'],
            'email': user['email'],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=1)
        }

    def write_error(self, status_code, **kwargs):
        """
        Handle non 404 errors.
        """
        message = 'An unexpected error has occurred. Please try your request again.'
        config = {
            'page_name': 'error',
            'event_name': 'Error'
        }

        self.render('error.html',
                    heading='Something went wrong :(',
                    config=config,
                    message=message)

    def check_xsrf_cookie(self):
        if self.request.method != 'BREW' and '/remote/' not in self.request.uri:
            tornado.web.RequestHandler.check_xsrf_cookie(self)

    def brew(self):
        self.set_status(418, "Easter Egg")
        self.write('Error 418: I am a teapot.')

class PageNotFoundHandler(BaseHandler):
    def prepare(self):
        super().prepare()
        self.config['page_name'] = 'error'

    def get(self):
        """
        Handle 404 errors.
        """
        self.set_status(404)
        message = 'The page you are looking for cannot be found.'
        self.render('error.html',
                    heading='404 Not Found',
                    config=self.config,
                    message=message)

def read_configuration():
    parent = str(Path(__file__).resolve().parents[1])
    path = os.path.join(parent, 'config.conf')
    config = {}

    with open(path, 'r') as conf_file:
        for line in conf_file:
            pair = line.split('=')
            config[pair[0]] = pair[1].strip()

    return config

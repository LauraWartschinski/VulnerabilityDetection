# -*- coding: utf-8 -*-

'''Make Pyramid play ball with AngularJS to achieve CSRF protection.

    To start using this module, include it in your application configuration::

        # Integrate with Angular for CSRF protection:
        config.include('bag.web.pyramid.angular_csrf')

    For any GET requests, this causes the response to have a
    cookie containing the CSRF token, just as Angular 1.3.x wants it.

    In subsequent AJAX requests (with verbs different than GET),
    Angular will send the token back in a header 'X-XSRF-Token'.
    Now you have 2 choices for view configuration.

    First choice: the view_config argument
    ======================================

    **WARNING: The 1st choice isn't working. If you find out why, a pull
    request would be extremely welcome.**

    The first choice is easiest:
    You can protect the corresponding Pyramid views simply by
    adding the ``check_csrf=True`` parameter to view_config().

    But to achieve this, we have to monkeypatch Pyramid.
    By default Pyramid uses a header named 'X-CSRF-Token'.
    We change it to 'X-XSRF-Token', which is preferred by Angular.
    Just so you know, the monkeypatch works well against Pyramid 1.5.1.
    To do this, run::

        from bag.web.pyramid.angular_csrf import monkeypatch_pyramid_csrf_check
        monkeypatch_pyramid_csrf_check()

    ...and now you can use the ``check_csrf=True`` argument.

    The disadvantages of this approach are, of course, monkeypatching,
    and the fact that when the CSRF token is missing, Pyramid returns 404,
    which in my opinion isn't accurate ― 404 tells me the URL is incorrect,
    when in fact there's only a missing header. Enters the second choice:

    Second choice: the csrf() decorator
    ===================================

    Decorate your view with @csrf and it will raise HTTPForbidden when
    the token is missing, which seems better. Usage::

        from bag.web.pyramid.angular_csrf import csrf

        @view_config(context=User, permission='edit_user',
                     accept='application/json', request_method='PUT',
                     renderer='json')
        @csrf
        def view_that_changes_a_user(context, request):
            ...

    Although I haven't tested this, I hear one can also decorate a class:

        @view_defaults(decorator=csrf)
        class SomeView(object):
            ...

    https://docs.angularjs.org/api/ng/service/$http
'''

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from functools import wraps
from pyramid.events import NewResponse
from pyramid.httpexceptions import HTTPForbidden
from . import _

COOKIE_NAME = 'XSRF-TOKEN'
HEADER_NAME = 'X-XSRF-Token'  # different from Pyramid's default 'X-CSRF-Token'


def on_GET_request_setup_csrf_cookie(ev):
    '''If this is the first GET request, we set the CSRF token in a
        JavaScript readable session cookie called XSRF-TOKEN.
        Angular will pick it up for subsequent AJAX requests.
        '''
    if ev.request.method == 'GET':  # and not 'static' in ev.request.path:
        token = ev.request.session.get_csrf_token()
        if ev.request.cookies.get('XSRF-TOKEN') != token:
            ev.response.set_cookie(COOKIE_NAME, token)


# Option 1 is not working  :(
def monkeypatch_pyramid_csrf_check():
    from pyramid import session

    def check_csrf_token(request, token='csrf_token', header=HEADER_NAME,
                         raises=True):
        supplied_token = request.params.get(token, request.headers.get(header))
        if supplied_token != request.session.get_csrf_token():
            if raises:
                raise session.BadCSRFToken('check_csrf_token(): Invalid token')
            return False
        return True

    session.check_csrf_token = check_csrf_token


# Option 2: decorator
def csrf(fn):
    @wraps(fn)
    def wrapper(context, request):
        token = request.headers.get(HEADER_NAME)
        session_token = request.session.get_csrf_token()
        # print(token, session_token)
        if token == session_token:
            return fn(context, request)
        else:
            raise HTTPForbidden(_(
                'Invalid CSRF token. Please try reloading the page.'))
    return wrapper


def includeme(config):
    config.add_subscriber(on_GET_request_setup_csrf_cookie, NewResponse)

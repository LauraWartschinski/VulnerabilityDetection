#!/usr/bin/python
# -*- coding: utf-8 -*-
import os,sys,re,urllib2,json,datetime,hashlib,random
import flask
import markdown
import requests

app = flask.Flask(__name__)
API_ROOT="http://localhost:8080/"
app.config['SECRET_KEY'] = requests.get(API_ROOT + "api/config?key=flask_secret_key").json()["value"]

@app.route('/favicon.ico')
def favicon():
    return "Not found", 404

@app.route('/robots.txt')
def robots():
    return "Not found", 404

@app.route('/', defaults={'path': ''}, methods=['GET','POST'])
@app.route('/<path:path>', methods=['GET','POST'])
def catch_all(path):
    data = {}
    auth_status = {}

    request_headers = {}
    if "Cookie" in flask.request.headers: request_headers["Cookie"] = flask.request.headers["Cookie"]
    if "Content-Type" in flask.request.headers: request_headers["Content-Type"] = flask.request.headers["Content-Type"]
    if "Content-Length" in flask.request.headers:
        content_length = flask.request.headers["Content-Length"]
        if content_length is not None and content_length.isdigit():
            request_headers["Content-Length"] = content_length

    response_headers = {}

    try:
        res = requests.get(API_ROOT + "api/auth/status", headers=request_headers)
        if not res.ok: return "Internel Server Error(api/auth/status failed)", 500
        if "Set-Cookie" in res.headers: response_headers["Set-Cookie"] = res.headers["Set-Cookie"]
        auth_status.update(res.json())

        res = None
        if flask.request.method == "GET":
            res = requests.get(API_ROOT + "site/" + path, headers=request_headers)
        else: # POST
            xsrf_token = flask.session.get("XSRF-TOKEN")
            xsrf_token_hdr = flask.request.headers.get("X-XSRF-TOKEN")
            if xsrf_token is None or xsrf_token_hdr is None or xsrf_token != xsrf_token_hdr:
                return "403 Forbidden(Token mismatch)", 403
            res = requests.post(API_ROOT + "site/" + path, headers=request_headers, data=flask.request.get_data())
        if not res.ok: return "%d %s" % (res.status_code, res.reason), res.status_code
        data.update(res.json())
    except requests.exceptions.ConnectionError:
        return "503 Service temporarily unavailable", 503

    if "user" in auth_status and auth_status["user"]:
        data["login_user"] = auth_status["user"]

    response = None
        
    if "template" in data:
        response = flask.Response(flask.render_template(data["template"], **data))
    else:
        response = flask.jsonify(data)

    for k, v in response_headers.iteritems():
        response.headers[k] = v

    if flask.session.get("XSRF-TOKEN") is None:
        xsrf_token = "%030x" % random.randrange(16**30)
        flask.session["XSRF-TOKEN"] = xsrf_token
        response.set_cookie("XSRF-TOKEN", xsrf_token)
        
    return response

@app.template_filter("markdown")
def __markdown(md):
    return markdown.markdown(md, extensions=['gfm'])

@app.template_filter("datetime")
def _datetime(t):
    now = datetime.datetime.fromtimestamp(t / 1000)
    return now.strftime(u"%Y-%m-%d %H:%M")

@app.template_filter("gravater_hash")
def _gravater_hash(email):
    return hashlib.md5(email.lower()).hexdigest()

@app.template_filter("yen")
def _yen(value):
    return u'￥{:,d}'.format(value)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        API_ROOT = sys.argv[1]
        if not API_ROOT.endswith("/"): API_ROOT += "/"
    print "API_ROOT=%s" % API_ROOT
    app.run(host='0.0.0.0',debug=True)

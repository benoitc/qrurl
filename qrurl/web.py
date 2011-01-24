# -*- coding: utf-8 -
#
# This file is part of qrurl released under the MIT license. 
# See the NOTICE for more information.

import os
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import flask
from flask import Flask, g, jsonify, request, render_template, Response
from gevent import monkey; monkey.patch_socket()
from gevent_zeromq import zmq
import redis

from qrimg import encode_to_img
from qrurl.api import create_url, get_url, get_url_info, get_consumers

app = Flask("qrurl")

_conn = None
def connect_redis(redis_host, redis_port, redis_db):
    """ connect to redis """
    global _conn
    if _conn is None:
        print "connect redis %s (%s)" % ("%s:%s" % (redis_host, redis_port), 
                os.getpid())
        _conn = redis.Redis(host=redis_host, port=redis_port,
                db=redis_db)
    return _conn

_zmq_ctx = None
_zmq_sock = None
def zmq_socket():
    """ create a socket """
    global _zmq_ctx, _zmq_sock
    created = False
    if not _zmq_ctx:
        _zmq_ctx = zmq.Context()
        _zmq_sock = _zmq_ctx.socket(zmq.PUSH)
        created = True
    return (_zmq_sock, created)
        
@app.before_request
def before_request():
    # init redis conn
    g.redis_conn = connect_redis(app.config.get('redis_host',
                'localhost'), app.config.get('redis_port', 6379),
                app.config.get('redis_db', 0))

    # connect to zmq consummers if needed
    g.zmq_sock, created = zmq_socket()
    consumers = list(get_consumers(g.redis_conn))

    for zmq_uri in consumers:
        g.zmq_sock.connect(zmq_uri)
    
    
class QRUrl(object):
    """ This is the main web application, called by external scripts """

    def __init__(self, redis_host='localhost', redis_port=6379, 
            redis_db=0, domain='http://lqr.co', debug=False):

        # update app conf
        app.config.update(
                redis_host = redis_host,
                redis_port = redis_port,
                redis_db = redis_db,
                domain = domain,
                debug = debug
        )

        if debug:
            from werkzeug.debug import DebuggedApplication
            app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

    def __call__(self, environ, start_response):
        return app(environ, start_response)

@app.route("/", methods=['GET', 'POST'])
def index():
    """ homepage view """
    error = None
    url = None
    domain = app.config.get('domain', 'qru.cc')
    print request.environ

    if request.method == "POST":
        try:
            if request.json:
                url = request.json.get['shorten']
                uid = create_url(g.redis_conn, g.zmq_sock, url)
                resp = jsonify(
                        ok = True,
                        uid = uid,
                        shortened = "%s/%s" % (domain, uid),
                        url = url
                )
            else:
                url = request.form.get("shorten")
                print "start create %s" % url
                uid = create_url(g.redis_conn, g.zmq_sock, url)
                print uid
                resp = dict(
                        shortened = "%s/%s" % (domain, uid),
                        url = url,
                        uid = uid
                )
                resp = render_template('index.html', **resp)
            return resp
        except KeyError:
            error =  "unkown 'shorten' url"
        except ValueError, e:
            error = str(e)
        except Exception, e:
            if app.config['debug']:
                raise
            error = "unkown error '%s'" % str(e)

        if error and request.json:
            return jsonify(error=error, url=url)

    return render_template('index.html', error=error, domain=domain)

@app.route("/<uid>")
def redirect(uid):
    """ redirecr uri """
    url = get_url(g.redis_conn, uid)
    if not url:
        flask.abort(404)
    return flask.redirect(url) 


@app.route("/<uid>.qr")
def qr(uid):
    """ get qr image """
    url = get_url(g.redis_conn, uid)
    if not url:
        flask.abort(404)

    domain = app.config.get('domain', 'qru.cc')
    img = encode_to_img("%s/%s" % (domain, uid))

    f = StringIO()
    img.save(f, "PNG", quality=80)
    f.seek(0)

    response = Response(f)
    response.mimetype = "image/png"
    return response

@app.route("/info/<uid>")
def info(uid):
    """ display uri infos """
    url = get_url_info(g.redis_conn, uid)
    if not url:
        flask.abort(404)

    mimetypes = request.accept_mimetypes
    if 'application/json' in mimetypes and not mimetypes.accept_html:
        resp = url.update({"ok": True})
        return jsonify(resp)

    return render_template("info.html", url=url, uid=uid, 
            domain=app.config.get('domain', 'http://qru.cc'))

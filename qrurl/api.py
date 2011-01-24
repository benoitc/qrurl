# -*- coding: utf-8 -
#
# This file is part of qrurl released under the MIT license. 
# See the NOTICE for more information.

import hashlib
import re
import time

from qrurl.base62 import b62encode

URL_PATTERN = ur'^[a-z]+://([^/:]+\.[a-z]{2,10}|([0-9]{1,3}\.){3}[0-9]{1,3})(:[0-9]+)?(\/.*)?$'
RE_URL = re.compile(URL_PATTERN, re.IGNORECASE)

def key(*args):
    return ':'.join(["URL"] + [arg.upper() for arg in args])

def valid_url(url):
    if not RE_URL.match(url):
        raise ValueError("invalid url")
    return url

def create_url(conn, sock, url):
    url = valid_url(url)

    uri_key = key(hashlib.sha1(url).hexdigest())
   
    uri_id = str(b62encode(int(conn.incr(key("id")))))
    conn.set(uri_key, uri_id)
    conn.set(key("hash", uri_id), uri_key)
    t = int(time.time())
    data_key = key("uid", "data", uri_id)
    conn.hset(data_key, 'date_creation', t)
    conn.hset(data_key, 'url', url)

    # send url creation to consumers
    sock.send("URL:%s" % uri_id)
    return uri_id

def get_url(conn, uid):
    u = conn.hget(key("uid", "data", uid), 'url')
    if u:
        return u

def get_url_info(conn, uid):
    u = conn.hgetall(key("uid", "data", uid))
    if u:
        return u

def set_click(conn, uid, info):
    conn.hmset(key("uid", "click"), info)

def get_click(conn, uid):
    click = conn.hgetall(key("uid", "click", uid))
    if click:
        return click

def add_consumer(conn, consumer_uri):
    return conn.sadd("consumers", consumer_uri)

def get_consumers(conn):
    return conn.smembers("consumers")

def remove_consumer(conn, consumer_uri):
    return conn.srem("consumers", consumer_uri)


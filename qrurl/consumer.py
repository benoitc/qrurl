# -*- coding: utf-8 -
#
# This file is part of qrurl released under the MIT license. 
# See the NOTICE for more information.

import json
from optparse import OptionParser, make_option
import sys
import time

import couchdbkit
import gevent
from gevent import monkey; monkey.patch_socket()
from gevent_zeromq import zmq
import redis

from qrurl import api

class Consumer(object):
    """ simple consumer class saving infos from redis on couchdb to
    process them later and allows their replication to final users """


    def __init__(self, couch_uri="http://127.0.0.1:5984/lqr",
            redis_host="127.0.0.1", redis_port=6379, redis_db=0,
            zmq_uri="tcp://127.0.0.1:5000"):

        self.conf = dict(
                couch_uri = couch_uri,
                redis_host = redis_host,
                redis_port = redis_port,
                redis_db = redis_db,
                zmq_uri = zmq_uri
        )

        # set redis connections
        self.conn_redis = redis.Redis(host=redis_host, port=redis_port,
                db=redis_db)
        
        # set couch database
        self.couch_db = couchdbkit.Database(couch_uri, create=True)
        self.docs = []
        self.last_updated = 0

        # create zmq context
        self.zmq_ctx = zmq.Context()
        self.zmq_sock = self.zmq_ctx.socket(zmq.PULL)
        self.zmq_sock.bind(zmq_uri)

        # we are alive
        self.alive = True

        # register consumer so it can receive messages
        self.register()

        # start doc loop
        self.start_batch()


    def start_batch(self):
        """Start the batch Greenlet used to send docs each mn"""

        def batch():
            while self.alive:
                gevent.sleep(60.0)
                if len(self.docs) > 0:
                    self.couch_db.save_docs(self.docs)
                    self.docs = []

        return gevent.spawn(batch)

    def stop(self):
        self.alive = False
        
        
    def register(self):
        api.add_consumer(self.conn_redis, self.conf['zmq_uri'])

    def unregister(self):
        api.remove_consumer(self.conn_redis, self.conf['zmq_uri'])

        try:
            self.zmq_sock.close()
            self.zmq_ctx.term()
        except:
            pass

    def handle_message(self, msg):
        kind, uri = msg.split(":", 1)
        
        print uri
        if kind == "URL":
            doc = api.get_url_info(self.conn_redis, uri)
            print "got doc"
        if kind == "CLICK":
            doc = api.get_click(self.conn_redis, uri)

        diff = time.time() - self.last_updated
        if len(self.docs) == 100 or (len(self.docs) > 0 and diff >= 60):
            # we update each 100 docs or each minutes
            self.couch_db.save_docs(self.docs)
            self.docs = []

        if not doc:
            return
        self.docs.append(doc)
        self.last_updated = time.time()

    def listen(self):
        while True:
            msg = self.zmq_sock.recv()
            if not msg:
                break
            print "got msg %s" % msg
            gevent.spawn(self.handle_message, msg)
            
        self.alive = False


def run():
    usage = "usage: %prog [options]"
    options = [
            make_option("--with-couch", action="store",
                type="string", dest="couch_uri", help="couchdb uri"),
            make_option("--with-redis-host", action="store",
                type="string", dest="redis_host", help="redis host"),
            make_option("--with-redis-port", action="store",
                type="string", dest="redis_port", help="redis port"),
            make_option("--with-redis-db", action="store", type="int",
                dest="redis_db", help="redis db"),
            make_option("--with-zmq", action="store", type="string",
                dest="zmq_uri", help="zmq uri")

    ]
    parser = OptionParser(usage=usage, option_list=options)
    opts, args = parser.parse_args()

    # settings default here is not needed but while we are here...
    couchdb_uri = opts.couch_uri or "http://127.0.0.1:5984/lqr"
    redis_host = opts.redis_host or "127.0.0.1"
    redis_port = opts.redis_port or 6379
    redis_db = opts.redis_db or 0
    zmq_uri = opts.zmq_uri or "tcp://127.0.0.1:5000"

    consumer = Consumer(couch_uri=couchdb_uri, redis_host=redis_host,
            redis_port=redis_port, redis_db=redis_db, zmq_uri=zmq_uri)

    try:
        consumer.listen()
    except (KeyboardInterrupt, SystemExit):
        consumer.stop()
    finally:
        consumer.unregister()
    
    sys.exit(0)

if __name__ in ('__main__', 'qrurl.consumer'):
    run()

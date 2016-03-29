#!/usr/bin/env python

import datetime
import logging
import os
import sys
import time

import simplejson as json
from tweepy import API, Stream, OAuthHandler
from tweepy.streaming import StreamListener

from daemon import Daemon

corgibotdir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=corgibotdir + "/corgibot.log", filemode='w', level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')

with open(corgibotdir + "/creds.json", 'r') as f:
    creds = json.loads(f.read())

consumer_key = creds["consumer_key"]
consumer_secret = creds["consumer_secret"]
access_token_key = creds["access_token_key"]
access_token_secret = creds["access_token_secret"]

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)

api = API(auth)


def tweet_about_corgi(status):
    username = status.user.screen_name
    logging.debug("User who tweeted was %s", username)
    name = status.user.name

    if "corgi" in username.lower() or "corgi" in name.lower() or username.lower() == api.me().screen_name.lower():
        logging.info("Not replying to a corgi-themed twitter or myself")
        return

    tid = status.id
    if tid:
        logging.info("Everything in order; tweeting about the corgi!")
        message = "@%s corgi!" % (username,)
        api.update_status(status=message, in_reply_to_status_id=tid)


class CorgiListener(StreamListener):
    def on_status(self, status):
        logging.debug("Got status from %s", status.user.screen_name)
        if "corgi" in status.text.lower():
            logging.info("CORGI!!!!!")
            time.sleep(.1)
            tweet_about_corgi(status)

        return True

    def keep_alive(self):
        logging.debug("Keep alive at %s", datetime.datetime.now())

    def on_error(self, status):
        logging.warning("Error occurred: status %s", status)

    def on_exception(self, exception):
        logging.warning("Error occurred: exception %s", exception)

    def on_timeout(self):
        logging.warning("Error occurred: timeout")

    def on_disconnect(self, notice):
        # https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
        logging.warning("Error occurred: disconnect %s", notice)

    def on_warning(self, notice):
        logging.warning("Warning occurred: disconnect warning %s", notice)


class ClosedException(Exception):
    pass    


class Tweeter(Daemon):
    def run(self):
        def except_on_closed(*args):
            raise ClosedException("Twitter closed the stream!")

        while True:
            logging.info("Looping to start the tweeter")
            try:
                tStream = Stream(auth, CorgiListener())
                tStream.on_closed = except_on_closed
                tStream.userstream()
            except Exception as e:
                logging.exception("Encountered an error: %s", e)


if __name__ == "__main__":

    tweetd = Tweeter(corgibotdir + "/corgibot.pid", stdout=corgibotdir + "/corgibotd.log", stderr=corgibotdir + "/corgibotd.err")

    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            tweetd.start()
        elif 'stop' == sys.argv[1]:
            tweetd.stop()
        elif 'restart' == sys.argv[1]:
            tweetd.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)

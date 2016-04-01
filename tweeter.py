#!/usr/bin/env python

import datetime
import logging
import os
import sys
import time

import argparse
import simplejson as json
from tweepy import API, Stream, OAuthHandler
from tweepy.streaming import StreamListener

from daemon import Daemon

WATCHWORD = "corgi"

botdir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=botdir + "/bot.log", filemode='w', level=logging.DEBUG, format='[%(asctime)s] %(levelname)s: %(message)s')

with open(botdir + "/creds.json", 'r') as f:
    creds = json.loads(f.read())

consumer_key = creds["consumer_key"]
consumer_secret = creds["consumer_secret"]
access_token_key = creds["access_token_key"]
access_token_secret = creds["access_token_secret"]

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)

api = API(auth)


def tweet_about_watchword(status, watchword):
    username = status.user.screen_name
    logging.debug("User who tweeted was %s", username)
    name = status.user.name

    if watchword in username.lower() or watchword in name.lower() or username.lower() == api.me().screen_name.lower():
        logging.info("Not replying to a %s-themed twitter or myself", watchword)
        return

    tid = status.id
    if tid:
        logging.info("Everything in order; tweeting about the %s!", watchword)
        message = "@%s %s!" % (username, watchword)
        api.update_status(status=message, in_reply_to_status_id=tid)


class WatchwordListener(StreamListener):
    def __init__(self, watchword):
        super(WatchwordListener, self).__init__()
        self.watchword = watchword

    def on_status(self, status):
        logging.debug("Got status from %s", status.user.screen_name)
        if self.watchword in status.text.lower():
            logging.info("%s!!!!!", self.watchword.upper())
            time.sleep(.1)
            tweet_about_watchword(status, self.watchword)

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


class WatchwordTweeter(Daemon):
    def __init__(self, *args, **kwargs):
        self.watchword = kwargs.pop('watchword', WATCHWORD)
        super(WatchwordTweeter, self).__init__(*args, **kwargs)

    def run(self):
        def except_on_closed(*args):
            raise ClosedException("Twitter closed the stream!")

        while True:
            logging.info("Looping to start the tweeter; watching for %s", self.watchword)
            try:
                tStream = Stream(auth, WatchwordListener(self.watchword))
                tStream.on_closed = except_on_closed
                tStream.userstream()
            except Exception as e:
                logging.exception("Encountered an error: %s", e)


if __name__ == "__main__":


    parser = argparse.ArgumentParser()

    parser.add_argument('-w', '--watchword', default=WATCHWORD, help='Keyword to watch for and tweet about! (default: %s)' % WATCHWORD)
    parser.add_argument('cmd', choices=['start', 'stop', 'restart'], help='Command to run')

    args = parser.parse_args()

    tweetd = WatchwordTweeter(botdir + "/bot.pid", stdout=botdir + "/botd.log", stderr=botdir + "/botd.err", watchword=args.watchword)

    if args.cmd == 'start':
        tweetd.start()
    elif args.cmd == 'stop':
        tweetd.stop()
    elif args.cmd == 'restart':
        tweetd.restart()

    sys.exit(0)

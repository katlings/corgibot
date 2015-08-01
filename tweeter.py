#!/usr/bin/env python

import logging
import os
import sys
import time

import simplejson as json
from tweepy import API, Stream, OAuthHandler
from tweepy.streaming import StreamListener

from daemon import Daemon

corgibotdir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=corgibotdir + "/corgibot.log", filemode='w', level=logging.INFO)

with open(corgibotdir + "/creds.json", 'r') as f:
    creds = json.loads(f.read())

consumer_key=creds["consumer_key"]
consumer_secret=creds["consumer_secret"]
access_token_key=creds["access_token_key"]
access_token_secret=creds["access_token_secret"]

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)

api = API(auth)


def tweet_about_corgi(tweet):
    username = tweet.get("user", {}).get("screen_name", "")
    logging.debug("User who tweeted was %s", username)
    name = tweet.get("user", {}).get("name", "")

    if "corgi" in username.lower() or "corgi" in name.lower() or username.lower() == "hartknyx":
        logging.info("Not replying to a corgi-themed twitter or myself")
        return

    tid = tweet.get("id")
    if tid:
        logging.info("Everything in order; tweeting about the corgi!")
        message = "@%s corgi!" % (user,)
        api.update_status(status=message, in_reply_to_status_id=tid)


class corgiListener(StreamListener):
    def on_data(self, data):
        logging.debug(data)
        tweet = json.loads(data)

        if "corgi" in tweet.get("text", "").lower():
            logging.info("CORGI!!!!!")
            tweet_about_corgi(tweet)

        return True

    def on_error(self, status):
        logging.warning("Error occurred: status %s", status)


class Tweeter(Daemon):
    def run(self):
        tStream = Stream(auth, corgiListener())
        while True:
            try:
                tStream.userstream()
            except Exception as e:
                logging.warning("Encountered an error: %s", e)
                continue


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

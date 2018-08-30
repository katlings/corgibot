#!/usr/bin/env python3

import datetime
import logging
import os
import sys
import time

import argparse
import simplejson as json
import tweepy
from tweepy import API, Cursor, Stream, OAuthHandler
from tweepy.streaming import StreamListener

#from daemon import Daemon

WATCHWORD = "corgi"

botdir = os.path.dirname(os.path.abspath(__file__))
logging.basicConfig(filename=botdir + "/bot.log", filemode='w', level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

with open(botdir + "/creds.json", 'r') as f:
    creds = json.loads(f.read())

consumer_key = creds["consumer_key"]
consumer_secret = creds["consumer_secret"]
access_token_key = creds["access_token_key"]
access_token_secret = creds["access_token_secret"]

auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token_key, access_token_secret)

api = API(auth)


def tweet_about_watchword(status, watchword, reply):
    username = status.user.screen_name
    logging.info("User who tweeted was %s", username)
    name = status.user.name

    if watchword in username.lower() or watchword in name.lower() or username.lower() == api.me().screen_name.lower():
        logging.info("Not replying to a %s-themed twitter or myself", watchword)
        return

    tid = status.id
    if tid:
        logging.info("Everything in order; tweeting about the %s!", watchword)
        message = "@%s %s!" % (username, reply)
        api.update_status(status=message, in_reply_to_status_id=tid)


class HomeTimelinePoller:
    def __init__(self, watchword, reply):
        self.last_seen = None
        self.watchword = watchword
        self.reply = reply

    def check_rate_limit(self):
        limits = api.rate_limit_status(resources='statuses')
        home = limits['resources']['statuses']['/statuses/home_timeline']
        logging.info(home)
        return home['remaining'], home['reset']
    
    def await_rate_limit(self):
        calls_left, reset_time = self.check_rate_limit()
        logging.info(f'{calls_left} calls left; resets at {reset_time}')
        if calls_left > 0:
            return

        # wait for our rate limiting to reset....
        now = int(time.time())
        wait_time = reset_time - now
        logging.warning(f'sleeping for {wait_time} seconds')
        time.sleep(wait_time + 1)
        return

    def should_tweet(self, status):
        if self.watchword in status.full_text.lower():
            logging.info('Found word in regular status')
            return True

        if status.is_quote_status:
            try:
                logging.debug('Trying quoted status')
                quoted_status_id = status.quoted_status_id
                quoted_status = api.get_status(quoted_status_id, tweet_mode='extended')
                return self.watchword in quoted_status.user.name.lower() or self.watchword in quoted_status.user.screen_name.lower() or self.should_tweet(quoted_status)

            except AttributeError as e:
                logging.exception("Failed to handle quoted status well")
                pass

        return False
    
    def process_timeline(self):
        """ cursor doesn't seem to be working; don't use this for now """
        def limit_handled(cursor):
            while True:
                try:
                    calls_left, reset_time = self.check_rate_limit()
                    logging.warning(f'{calls_left} rate limit calls left; resets at {reset_time}')
                    yield cursor.next()
                except (tweepy.RateLimitError, tweepy.error.TweepError):
                    self.await_rate_limit()
                except StopIteration:
                    logging.info('sleeping for 60 seconds')
                    time.sleep(60)
        first = True

        cursor = Cursor(api.home_timeline, since_id=self.last_seen, tweet_mode='extended')

        # special case for first because fuck it sloppy python
        if self.last_seen is None:
            for status in limit_handled(cursor.items(20)):
                if first:
                    self.last_seen = status.id
                    first = False
                logging.info(status.full_text)
                if self.should_tweet(status):
                    logging.info(f'TWEET TWEET {status.full_text}')
                    tweet_about_watchword(status, self.watchword, self.reply)
            return

        for status in limit_handled(cursor.items()):
            logging.info('status %s', status)
            if first:
                self.last_seen = status.id
                first = False
            logging.info(status.full_text)
            if self.should_tweet(status):
                logging.info(f'TWEET TWEET {status.full_text}')
                tweet_about_watchword(status, self.watchword, self.reply)

    def check_timeline(self):
        self.await_rate_limit()

        # special case for first because fuck it sloppy python
        if self.last_seen is None:
            latest_tweets = api.home_timeline(since_id=None, max_id=None, count=200, tweet_mode='extended')
            self.last_seen = latest_tweets[-1].id
            logging.info(f'last seen {self.last_seen}')

            for status in latest_tweets:
                logging.debug(status.full_text)
                if self.should_tweet(status):
                    logging.info(f'TWEET TWEET {status.full_text}')
                    tweet_about_watchword(status, self.watchword, self.reply)
            return

        latest_tweets = api.home_timeline(since_id=self.last_seen, max_id=None, count=200, tweet_mode='extended')
        # let's just pray we never see more than 200 tweets in a 15 minute window
        if latest_tweets and len(latest_tweets) > 150:
            logging.warning(f'WTF, we saw {len(latest_tweets)} tweets since the last one')
        self.last_seen = latest_tweets[0].id if latest_tweets else self.last_seen
        logging.info(f'Gathered {len(latest_tweets)} tweets')
        for status in latest_tweets:
            if self.should_tweet(status):
                logging.info(f'TWEET TWEET {status.full_text}')
                tweet_about_watchword(status, self.watchword, self.reply)

    def run(self):
        while True:
            try:
                self.check_timeline()
            except:
                logging.exception('Something went wrong')
            finally:
                logging.info('sleeping for 60 seconds')
                time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-w', '--watchword', default=WATCHWORD, help='Keyword to watch for! (default: %s)' % WATCHWORD)
    parser.add_argument('-r', '--reply', default=WATCHWORD, help='Keyword to tweet about! (default: %s)' % WATCHWORD)
    args = parser.parse_args()
    p = HomeTimelinePoller(args.watchword, args.reply)
    p.run()

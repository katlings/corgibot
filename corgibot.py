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
#       api.update_status(status=message, in_reply_to_status_id=tid)


class HomeTimelinePoller:
    def __init__(self, watchword, reply):
        self.last_seen = None
        self.watchword = watchword
        self.reply = reply

    def check_rate_limit(self):
        limits = api.rate_limit_status(resources='statuses')
        home = limits['resources']['statuses']['/statuses/home_timeline']
        return home['remaining'], home['reset']
    
    def await_rate_limit(self):
        calls_left, reset_time = self.check_rate_limit()
        logging.info(f'{calls_left} calls left; resets at {reset_time}')
        if calls_left > 0:
            return

        # wait for our rate limiting to reset....
        now = int(time.time())
        wait_time = reset_time - now
        logging.warning(f'Waiting {wait_time} seconds')
        time.sleep(wait_time + 1)
        return


    def should_tweet(self, status):
        if self.watchword in status.full_text.lower():
            logging.info('Found word in regular status')
            return True

        if status.is_quote_status:
            try:
                logging.info('Trying quoted status')
                quoted_status = status.quoted_status
                return self.watchword in quoted_status.user.name.lower() or self.watchword in quoted_status.user.screen_name.lower() or self.should_tweet(quoted_status)

            except AttributeError as e:
                logging.exception("Failed to handle quoted status well")
                pass

#        try:
#            if status.truncated and status.extended_tweet and self.watchword in status.extended_tweet.get('full_text', '').lower():
#                logging.info('Found word in extended status')
#                return True
#        except AttributeError as e:
#            logging.exception("Failed to handle extended status well")
#            pass

        return False
    
    def process_timeline(self):
        def limit_handled(cursor):
            while True:
                try:
                    a, b = self.check_rate_limit()
                    logging.warning(f'{a} rate limit calls left; resets at {b}')
                    yield cursor.next()
                except (tweepy.RateLimitError, tweepy.error.TweepError):
                    self.await_rate_limit()
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
            if first:
                self.last_seen = status.id
                first = False
            logging.info(status.full_text)
            if self.should_tweet(status):
                logging.info(f'TWEET TWEET {status.full_text}')
                tweet_about_watchword(status, self.watchword, self.reply)

    def check_timeline(self):
        """ probably deprecated """
        self.await_rate_limit()

        # special case for first because fuck it sloppy python
        if self.last_seen is None:
            latest_tweets = api.home_timeline(since_id=None, max_id=None, count=200)
            self.last_seen = latest_tweets[-1].id
            logging.info(f'last seen {self.last_seen}')

            for status in latest_tweets:
                if self.should_tweet(status):
                    logging.info(f'TWEET TWEET {status.text}')
                    tweet_about_watchword(status, self.watchword, self.reply)
            return 

        latest_tweets = api.home_timeline(since_id=self.last_seen, max_id=None, count=20)
        if latest_tweets and len(latest_tweets) > 18:
            max_id = latest_tweets[-1].id
            while max_id and self.await_rate_limit():
                logging.info(f'fetching more tweets between {self.last_seen} and {max_id}')
                more_tweets = api.home_timeline(since_id=self.last_seen, max_id=max_id-1, count=20)
                latest_tweets.extend(more_tweets)
                max_id = more_tweets[-1].id if more_tweets else None
        self.last_seen = latest_tweets[0].id if latest_tweets else self.last_seen
        logging.info('Gathered %d tweets', len(latest_tweets))
        for status in latest_tweets:
            if self.should_tweet(status):
                logging.info(f'TWEET TWEET {status.text}')
                tweet_about_watchword(status, self.watchword, self.reply)
        
    def run(self):
        while True:
            try:
                self.process_timeline()
            except:
                logging.exception('Something went wrong')
            finally:
                time.sleep(60)


#class WatchwordListener(StreamListener):
#    def __init__(self, watchword, reply):
#        super(WatchwordListener, self).__init__()
#        self.watchword = watchword
#        self.reply = reply
#
#    def on_status(self, status):
#        def should_fire(status):
#            if self.watchword in status.text.lower():
#                logging.debug('Found word in regular status')
#                return True
#
#            if status.truncated and status.extended_tweet and self.watchword in status.extended_tweet.get('full_text', '').lower():
#                logging.debug('Found word in extended status')
#                return True
#
#            if status.is_quote_status:
#                try:
#                    logging.debug('Trying quoted status')
#                    quoted_status = status.quoted_status
#                    return self.watchword in quoted_status.user.name.lower() or self.watchword in quoted_status.user.screen_name.lower() or should_fire(quoted_status)
#
#                except AttributeError as e:
#                    logging.exception("Failed to handle quoted status well")
#                    pass
#
#            return False
#
#        def should_like(status):
#            return status.user.screen_name.lower() == 'skyeplaysgames' and ('kh' in status.text.lower() or 'kingdom hearts' in status.text.lower())
#
#        logging.debug("Got status from %s", status.user.screen_name)
#        if should_fire(status):
#            logging.info("%s!!!!!", self.watchword)
#            time.sleep(.1)
#            tweet_about_watchword(status, self.watchword, self.reply)
#        if status.id and should_like(status):
#            logging.info('lol found a kh tweet from skye')
#            api.create_favorite(status.id)
#
#        return True
#
#    def keep_alive(self):
#        logging.debug("Keep alive at %s", datetime.datetime.now())
#
#    def on_error(self, status):
#        logging.warning("Error occurred: status %s", status)
#
#    def on_exception(self, exception):
#        logging.warning("Error occurred: exception %s", exception)
#
#    def on_timeout(self):
#        logging.warning("Error occurred: timeout")
#
#    def on_disconnect(self, notice):
#        # https://dev.twitter.com/docs/streaming-apis/messages#Disconnect_messages_disconnect
#        logging.warning("Error occurred: disconnect %s", notice)
#
#    def on_warning(self, notice):
#        logging.warning("Warning occurred: disconnect warning %s", notice)
#
#
#class ClosedException(Exception):
#    pass    
#
#
#class WatchwordTweeter(Daemon):
#    def __init__(self, *args, **kwargs):
#        self.watchword = kwargs.pop('watchword', WATCHWORD)
#        self.reply = kwargs.pop('reply', WATCHWORD)
#        super(WatchwordTweeter, self).__init__(*args, **kwargs)
#
#    def run(self):
#        def except_on_closed(*args):
#            raise ClosedException("Twitter closed the stream!")
#
#        while True:
#            logging.info("Looping to start the tweeter; watching for %s and replying with %s", self.watchword, self.reply)
#            try:
#                tStream = Stream(auth, WatchwordListener(self.watchword, self.reply))
#                tStream.on_closed = except_on_closed
#                tStream.userstream()
#            except Exception as e:
#                logging.exception("Encountered an error: %s", e)
#            time.sleep(20)
#
#
#if __name__ == "__main__":
#
#
#    parser = argparse.ArgumentParser()
#
#    parser.add_argument('-w', '--watchword', default=WATCHWORD, help='Keyword to watch for! (default: %s)' % WATCHWORD)
#    parser.add_argument('-r', '--reply', default=WATCHWORD, help='Keyword to tweet about! (default: %s)' % WATCHWORD)
#    parser.add_argument('cmd', choices=['start', 'stop', 'restart'], help='Command to run')
#
#    args = parser.parse_args()
#
#    tweetd = WatchwordTweeter(botdir + "/bot.pid", stdout=botdir + "/botd.log", stderr=botdir + "/botd.err", watchword=args.watchword, reply=args.reply)
#
#    if args.cmd == 'start':
#        tweetd.start()
#    elif args.cmd == 'stop':
#        tweetd.stop()
#    elif args.cmd == 'restart':
#        tweetd.restart()
#
#    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-w', '--watchword', default=WATCHWORD, help='Keyword to watch for! (default: %s)' % WATCHWORD)
    parser.add_argument('-r', '--reply', default=WATCHWORD, help='Keyword to tweet about! (default: %s)' % WATCHWORD)
    args = parser.parse_args()
    p = HomeTimelinePoller(args.watchword, args.reply)
    p.run()

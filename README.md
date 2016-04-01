# Corgibot

A small bot written in Python to watch a user's Twitter timeline and express
excitement when someone the user follows mentions a corgi (corgi!).
Customizable for any keyword, but corgis are best.

## Usage

### First-Time Setup

Recommended: Create a virtualenv with required libraries. Most notably, this
bot uses [tweepy](http://www.tweepy.org) to  access the Twitter streaming API.

```
$ virtualenv corgienv
$ . corgienv/bin/activate
(corgienv)$ pip install --upgrade pip  # make sure pip is up to date
(corgienv)$ pip install -r requirements.txt
```

Required: Generate an API key for an app at http://apps.twitter.com, and store
access tokens in `corgibot/creds.json`.

```
{
    "consumer_key": "www",
    "consumer_secret": "xxx",
    "access_token_key": "yyy",
    "access_token_secret": "zzz"
}
```

### Running the Bot

The bot runs as a daemon, logging to `corgibot/bot.log`.

```
(corgienv)$ ./tweeter.py start
(corgienv)$ ./tweeter.py restart
(corgienv)$ ./tweeter.py stop
(corgienv)$ ./tweeter.py -w labradoodle restart
```

Check for running status with `ps aux | grep tweeter`.

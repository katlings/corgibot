# Corgibot

A small bot written in Python to watch a user's Twitter timeline and express
excitement when someone the user follows mentions a corgi (corgi!).

## Usage

### First-Time Setup

Recommended: Create a virtualenv with required libraries. Most notably, this
bot uses [tweepy](http://www.tweepy.org) to  access the Twitter streaming API.

```
$ virtualenv corgienv
$ . corgienv/bin/activate
(corgienv)$ pip install -r requirements.txt
```

Required: Generate an API key for an app at http://apps.twitter.com, and store
access tokens in `corgibot/creds.json`. Also include the username these keys
were generated under, so the corgibot doesn't reply to itself infinitely.


```
{
    "consumer_key": www,
    "consumer_secret": xxx,
    "access_token_key": yyy,
    "access_token_secret": zzz,
    "username": "hartknyx"
}
```

### Running the Bot

The bot runs as a daemon, logging to `corgibot/corgibot.log`.

```
(corgienv)$ ./tweeter.py start
(corgienv)$ ./tweeter.py restart
(corgienv)$ ./tweeter.py stop
```

Check for running status with `ps aux | grep tweeter`.

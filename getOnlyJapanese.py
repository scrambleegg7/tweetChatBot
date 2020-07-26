import tweepy
import json
import sys
import codecs
import config #標準のjsonモジュールとconfig.pyの読み込み

from tweepy import OAuthHandler
from tweepy import API
from tweepy import Stream



CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET



class StdOutListener(tweepy.StreamListener):
    def on_data(self, data):
        tweet = json.loads(data)
        U_img = (tweet["user"]["profile_image_url"])
        Created_at = (tweet["created_at"])
        User = (tweet["user"]["screen_name"].encode("utf-8"))
        Name = (tweet["user"]["name"].encode("utf-8"))
        #Text = (tweet["text"].encode("utf-8"))
        Text = (tweet["text"])
        Lang = (tweet["user"]["lang"])

        #if tweet["user"]["lang"] == "ja":
        print( Text, Lang ) #, User, Name, Created_at)

        return True

    def on_error(self, status):
        print(status)


l = StdOutListener()

auth = OAuthHandler(CK, CS)
auth.set_access_token(AT, ATS)


#auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
#auth.set_access_token(access_token, access_token_secret)
stream = tweepy.Stream(auth, l)
stream.filter(track=['#'])
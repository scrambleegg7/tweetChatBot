
from tweepy import OAuthHandler
from tweepy import API
from tweepy import Stream


import sys
from tweepy.streaming import StreamListener


import json, config #標準のjsonモジュールとconfig.pyの読み込み
#from requests_oauthlib import OAuth1Session #OAuthのライブラリの読み込み
import tweepy
import time

CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET
#twitter = OAuth1Session(CK, CS, AT, ATS) #認証処理


class Listener(StreamListener):
    def __init__(self, output_file=sys.stdout):
        super(Listener,self).__init__()
        self.output_file = output_file
        self.idx = 0
    #def on_status(self, status):
    #    self.idx = self.idx + 1
    #    print(status.text, file=self.output_file)
    #    print("** counter ** : %d" % self.idx)

    def on_data(self, data):
        self.idx = self.idx + 1
        tweet = json.loads(data)
        

        #U_img = (tweet["user"]["profile_image_url"])
        #Created_at = (tweet["created_at"])
        #User = (tweet["user"]["screen_name"].encode("utf-8"))
        #Name = (tweet["user"]["name"].encode("utf-8"))
        #Text = (tweet["text"].encode("utf-8"))

        #if tweet["user"]["lang"] == "ja":
            #print(Text, User, Name, Created_at)
        print(tweet["created_at"])
        return True



    def on_error(self, status_code):
        print(status_code)
        return False


#auth = tweepy.AppAuthHandler(CK, CS)    
auth = OAuthHandler(CK, CS)
auth.set_access_token(AT, ATS)

#auth = OAuthHandler(CK, CS)
#auth.set_access_token(AT, ATS)
api = API(auth, wait_on_rate_limit=True,
          wait_on_rate_limit_notify=True)


listener = Listener()

stream = Stream(auth=api.auth, listener=listener)
try:
    print('Start streaming.')
    stream.filter(["#"])
except KeyboardInterrupt as e :
    print("Stopped.")
finally:
    print('Done.')
    stream.disconnect()
    #output.close()

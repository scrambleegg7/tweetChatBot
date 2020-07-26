import json, config #標準のjsonモジュールとconfig.pyの読み込み
#from requests_oauthlib import OAuth1Session #OAuthのライブラリの読み込み
import tweepy
import time

CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET
#twitter = OAuth1Session(CK, CS, AT, ATS) #認証処理




def limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15 * 60)

def main():

    auth = tweepy.AppAuthHandler(CK, CS)
    api = tweepy.API(auth)


    idx = 0
    for tweet in limit_handled( tweepy.Cursor(api.search, q="コロナ").items()  ):

        idx = idx + 1
        print("{}".format(tweet.text))
        print("counter : %d" % idx )



if __name__ == "__main__":
    main()

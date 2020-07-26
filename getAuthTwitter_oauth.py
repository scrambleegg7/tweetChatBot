import json, config #標準のjsonモジュールとconfig.pyの読み込み
from requests_oauthlib import OAuth1Session #OAuthのライブラリの読み込み
import datetime, time, sys
import oauth2


CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET


def oauth_req(url, key, secret, http_method="GET", post_body="", http_headers=None):
    consumer = oauth2.Consumer(key=CK, secret=CS)
    token = oauth2.Token(key=key, secret=secret)
    client = oauth2.Client(consumer, token)
    resp, content = client.request( url, method=http_method, body=post_body.encode('utf-8'), headers=http_headers )
    return content


session = OAuth1Session(CK, CS, AT, ATS)

url = 'https://api.twitter.com/1.1/search/tweets.json'
res = session.get(url, params = {'q':u'頭痛', 'count':100})

#--------------------
# ステータスコード確認
#--------------------
if res.status_code != 200:
    print ("Twitter API Error: %d" % res.status_code)
    sys.exit(1)


print ('アクセス可能回数 %s' % res.headers['X-Rate-Limit-Remaining'])
print ('リセット時間 %s' % res.headers['X-Rate-Limit-Reset'])
sec = int(res.headers['X-Rate-Limit-Reset'])\
           - time.mktime(datetime.datetime.now().timetuple())
print ('リセット時間 （残り秒数に換算） %s' % sec)

res_text = json.loads(res.text)
for tweet in res_text['statuses']:
    print ('-----')
    print (tweet['created_at'])
    print (tweet['text'])
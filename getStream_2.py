import tweepy  
import config
from datetime import timedelta

import datetime, time, sys
import re
import emoji

from requests_oauthlib import OAuth1Session #OAuthのライブラリの読み込み
from socket import error as SocketError
import errno
import json

CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET

session = OAuth1Session(CK, CS, AT, ATS) #認証処理
start_time = 1288834974657

p = re.compile('[\u3041-\u309F]+')

keyword = ["コロナ", "Go To", "布マスク"]
#*******************************************************************************
#                                                                              *
# sleep処理　resetで指定した時間スリープする                                   *
#                                                                              *
#*******************************************************************************
def waitUntilReset(reset):
    seconds = reset - time.mktime(datetime.datetime.now().timetuple())
    seconds = max(seconds, 0)
    print ('\n     =====================')
    print ('     == waiting %d sec ==' % (seconds + 10) )
    print ('     =====================')
    sys.stdout.flush()
    time.sleep(seconds + 10)  # 念のため + 10 秒



def getResponseText(id, in_text):

    url2 = 'https://api.twitter.com/1.1/statuses/lookup.json'

    cnt_req = 0
    max_tweet=start_time

    total_text = []                           # tweet本文（発話／応答）のリスト
    tweet_list = []                           # n_reply_to_status_idと応答tweetの対のリスト

    #--------------------------------------------------------------------------*
    #                                                                          *
    # 発話tweet抽出取得                                                        *
    #                                                                          *
    #--------------------------------------------------------------------------*   

    #複数status_id指定で発話tweet取得
    unavailableCnt = 0
    while True :
        try :
            req = session.get(url2, params = {'id':id,'count':1})
        except SocketError as e:
            print('ソケットエラー errno=',e.errno)
            if unavailableCnt > 10:
                raise

            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            unavailableCnt += 1
            continue

        if req.status_code == 503:
            # 503 : Service Unavailable
            if unavailableCnt > 10:
                raise Exception('Twitter API error'  )

            unavailableCnt += 1
            print ('Service Unavailable 503')
            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            continue

        unavailableCnt = 0

        if req.status_code == 200 :
            req_text = json.loads(req.text)
            break
        else :
            raise Exception('Twitter API error')    

    #print("- " * 20)
    #print("req_text",  req_text)
    # 発話tweet本文スクリーニング
    for j in range(0,len(req_text)) :
        if req_text[j]['id_str'] == id :
            #req_sentence = req_text['text']

            if len(req_text) <= 0 :
                #print(req_text)
                continue

            req_sentence = req_text[j]['text'] 
                #RTを対象外にする
            if req_sentence[0:3] == "RT " :
                continue

            req_sentence = screening(req_sentence)

            #スクリーニングの結果、ブランクだったら対象外
            if req_sentence == '' :
                continue   
            # 発話tweetと応答tweetを対で書き込み
            if req_sentence != in_text:      
                total_text.append("REQ:"+req_sentence)
                total_text.append('RES:'+in_text)
                cnt_req += 1

    max_tweet = max(max_tweet,start_time)
    return max_tweet,cnt_req ,total_text


def screening(text) :
    s = text

    #RTを外す
    if s[0:3] == "RT " :
        s = s.replace(s[0:3],"")
    #@screen_nameを外す
    while s.find("@") != -1 :
        index_at = s.find("@")
        if s.find(" ") != -1  :
            index_sp = s.find(" ",index_at)
            if index_sp != -1 :
                s = s.replace(s[index_at:index_sp+1],"")
            else :
                s = s.replace(s[index_at:],"")
        else :
            s = s.replace(s[index_at:],"")

    #改行を外す
    while s.find("\n") != -1 :
        index_ret = s.find("\n")
        s = s.replace(s[index_ret],"")

    #URLを外す
    s = re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", s)
    #絵文字を「。」に置き換え その１
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), '。')
    s = s.translate(non_bmp_map)
    #絵文字を「。」に置き換え　その２
    s=''.join(c if c not in emoji.UNICODE_EMOJI else '。' for c in s  )

    #置き換えた「。」が連続していたら１つにまとめる
    while s.find('。。') != -1 :
        index_period = s.find('。。')
        s = s.replace(s[index_period:index_period+2],'。')

    #ハッシュタグを外す
    while s.find('#') != -1 :
        index_hash = s.find('#') 
        s = s[0:index_hash]

    return s


# StreamListenerを継承するクラスListener作成
class Listener(tweepy.StreamListener):

    def __init__(self):
        super(Listener, self).__init__()
        self.counter = 0

    def on_status(self, status):
        status.created_at += timedelta(hours=9)#世界標準時から日本時間に

        date = datetime.date.today()
        fname = 'tweet/tweet_' + keyword[0] + "_" +str(date)+'.txt'

        streamText = status.text

        if streamText[0:3] != "RT " and status.in_reply_to_status_id_str != None:
            #print("RT")
        #else:

            streamText = screening(streamText)

            # only matched Japanese Character あ->ん
            if p.search(streamText):

                self.counter = self.counter + 1
                print('------------------------------')
                #print(streamText)
                #print("{name}({screen}) {created} via {src}\n".format(
                #                                                    name=status.author.name, screen=status.author.screen_name,
                #                                                    created=status.created_at, src=status.source))



                id = status.in_reply_to_status_id_str

                #print(id)
                print("Counter:%d" % self.counter)

                _ , _ ,total_text = getResponseText(id, streamText)

                f=open(fname,'a')
                for i in range(0,len(total_text)):
                    f.write(str(total_text[i])+"\n")
                f.close()
                print(total_text)
        
        return True

    def on_error(self, status_code):
        print('エラー発生: ' + str(status_code))
        return True

    def on_timeout(self):
        print('Timeout...')
        return True



auth = tweepy.OAuthHandler(CK, CS)
auth.set_access_token(AT, ATS)


listener = Listener()

stream = tweepy.Stream(auth, listener)
stream.filter(track=keyword)

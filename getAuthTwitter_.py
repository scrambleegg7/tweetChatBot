import json, config #標準のjsonモジュールとconfig.pyの読み込み
from requests_oauthlib import OAuth1Session #OAuthのライブラリの読み込み

import datetime, time, sys
import re
import datetime
import emoji
import sys

from socket import error as SocketError
import errno

p = re.compile('[\u3041-\u309F]+')

CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET
session = OAuth1Session(CK, CS, AT, ATS) #認証処理

url = "https://api.twitter.com/1.1/statuses/user_timeline.json" #タイムライン取得エンドポイント




def tweet_id2time(tweet_id) :
    id_bin = bin(tweet_id>>22)
    tweet_time=int(id_bin,2)
    tweet_time += 1288834974657
    return tweet_time


#*******************************************************************************
#                                                                              *
# 発話tweet本文取得                                                            *
#                                                                              *
#*******************************************************************************    
def getTweet(res,start_time,reset):
    res_text = json.loads(res.text)
    url1 = 'https://api.twitter.com/1.1/statuses/user_timeline.json'    #今回こちらは使わない
    url2 = 'https://api.twitter.com/1.1/statuses/lookup.json'

    cnt_req = 0
    max_tweet=start_time

    total_text = []                           # tweet本文（発話／応答）のリスト
    tweet_list = []                           # n_reply_to_status_idと応答tweetの対のリスト
    #--------------------------------------------------------------------------*
    #                                                                          *
    # 応答tweet抽出取得                                                        *
    #                                                                          *
    #--------------------------------------------------------------------------*        
    
    
    print(" tweet length  --->   %d" % len(res_text['statuses']))
    
    for tweet in res_text['statuses']:
        status_id = tweet['in_reply_to_status_id_str']
        tweet_id=tweet['id']                  # 応答tweetのid

        #print("tweetID ---> %d " % tweet_id)

        if status_id != None :               # 当該tweetが応答かどうかの判断

            tweet_time = tweet_id2time(tweet_id)
            if tweet_time <= start_time :    # 前回処理より新しいtweetのみ処理する
                continue

            if max_tweet < tweet_time :
                max_tweet = tweet_time

            res_sentence = tweet['text']
            #RTを対象外にする
            if res_sentence[0:3] == "RT " :
                continue

            if not ( p.search(res_sentence) ):
                continue

            res_sentence = screening(res_sentence)
            if res_sentence == '' :
                continue

            tweet_list.append([status_id,res_sentence])


    if len(tweet_list) == 0 :
        return max_tweet,cnt_req ,total_text

    print("- " * 20)
    print("** tweet list ** ")
    print(tweet_list)

    #複数status_idを連結する   
    id_list = tweet_list[0][0]
    for i in range(1,len(tweet_list)) :
        id_list += ','
        id_list += tweet_list[i][0]

    #--------------------------------------------------------------------------*
    #                                                                          *
    # 発話tweet抽出取得                                                        *
    #                                                                          *
    #--------------------------------------------------------------------------*   

    #複数status_id指定で発話tweet取得
    unavailableCnt = 0
    while True :
        try :
            req = session.get(url2, params = {'id':id_list ,'count':len(tweet_list)})
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
                raise Exception('Twitter API error %d' % res.status_code)

            unavailableCnt += 1
            print ('Service Unavailable 503')
            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            continue

        unavailableCnt = 0

        if req.status_code == 200 :
            req_text = json.loads(req.text)
            break
        else :
            raise Exception('Twitter API error %d' % res.status_code)    


    #print("result of req" , json.loads( req.text ) )

    # 発話tweet本文スクリーニング
    for i in range(0,len(tweet_list)) :
        for j in range(0,len(req_text)) :
            if req_text[j]['id_str'] == tweet_list[i][0] :
                req_sentence = req_text[j]['text']

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
                if req_sentence != tweet_list[i][1] :      
                    total_text.append("REQ:"+req_sentence)
                    total_text.append('RES:'+tweet_list[i][1])
                    cnt_req += 1

    max_tweet = max(max_tweet,start_time)
    return max_tweet,cnt_req ,total_text




#*******************************************************************************
#                                                                              *
# tweet本文スクリーニング                                                      *
#                                                                              *
#*******************************************************************************    
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


# 回数制限を問合せ、アクセス可能になるまで wait する

#*******************************************************************************
#                                                                              *
# 回数制限を問合せ、アクセス可能になるまで wait する                           *
#                                                                              *
#*******************************************************************************
def checkLimit(session):
    unavailableCnt = 0
    url = "https://api.twitter.com/1.1/application/rate_limit_status.json"

    while True :
        try :
            res = session.get(url)
        except SocketError as e:
            print('erron=',e.errno)
            print('ソケットエラー')
            if unavailableCnt > 10:
                raise

            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            unavailableCnt += 1
            continue

        if res.status_code == 503:
            # 503 : Service Unavailable
            if unavailableCnt > 10:
                raise Exception('Twitter API error %d' % res.status_code)

            unavailableCnt += 1
            print ('Service Unavailable 503')
            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            continue

        unavailableCnt = 0

        if res.status_code != 200:
            raise Exception('Twitter API error %d' % res.status_code)

        remaining_search,remaining_user, remaining_limit ,reset = getLimitContext(json.loads(res.text))
        if remaining_search <= 1 or remaining_user <=1 or remaining_limit <= 1:
            waitUntilReset(reset+30)
        else :
            break

    sec = reset - time.mktime(datetime.datetime.now().timetuple())
    print(remaining_search,remaining_user, remaining_limit ,sec)
    return reset

#*******************************************************************************
#                                                                              *
# sleep処理　resetで指定した時間スリープする                                   *
#                                                                              *
#*******************************************************************************
def waitUntilReset(reset):
    seconds = reset - time.mktime(datetime.datetime.now().timetuple())
    seconds = max(seconds, 0)
    print ('\n     =====================')
    print ('     == waiting %d sec ==' % seconds)
    print ('     =====================')
    sys.stdout.flush()
    time.sleep(seconds + 10)  # 念のため + 10 秒

#*******************************************************************************
#                                                                              *
# 回数制限情報取得                                                             *
#                                                                              *
#*******************************************************************************    
def getLimitContext(res_text):
    # searchの制限情報
    remaining_search = res_text['resources']['search']['/search/tweets']['remaining']
    reset1     = res_text['resources']['search']['/search/tweets']['reset']
    # lookupの制限情報
    remaining_user = res_text['resources']['statuses']['/statuses/lookup']['remaining']
    reset2     = res_text['resources']['statuses']['/statuses/lookup']['reset']
    # 制限情報取得の制限情報
    remaining_limit = res_text['resources']['application']['/application/rate_limit_status']['remaining']
    reset3     = res_text['resources']['application']['/application/rate_limit_status']['reset']

    return int(remaining_search),int(remaining_user),int(remaining_limit) ,max(int(reset1),int(reset2),int(reset3))



def main(args):

    total= -1
    total_count = 0
    cnt = 0
    unavailableCnt = 0
    url = 'https://api.twitter.com/1.1/search/tweets.json'

    start_time = 1288834974657
    while True:
        #----------------
        # 回数制限を確認
        #----------------
        #
        reset  = checkLimit(session) 
        get_time = time.mktime(datetime.datetime.now().timetuple()) #getの時刻取得
        
        keyword = 'Go To'
        
        try :
            res = session.get(url, params = {'q':keyword, 'count':100})
        except SocketError as e:
            print('ソケットエラー errno=',e.errno)
            if unavailableCnt > 10:
                raise

            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            unavailableCnt += 1
            continue

        if res.status_code == 503:
            # 503 : Service Unavailable
            if unavailableCnt > 10:
                raise Exception('Twitter API error %d' % res.status_code)

            unavailableCnt += 1
            print ('Service Unavailable 503')
            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 30)
            continue

        unavailableCnt = 0

        if res.status_code != 200:
            raise Exception('Twitter API error %d' % res.status_code)

        #----------------
        # 取得したtweetに対する発話取得とファイル書き込み
        #----------------
        start_time ,count ,total_text = getTweet(res,start_time,reset)

        date = datetime.date.today()
        fname = 'tweet/tweet'+str(date)+'.txt'

        #f=open(fname,'a')
        #for i in range(0,len(total_text)):
        #    f.write(str(total_text[i])+"\n")
        #f.close()
        print(total_text)

        total_count += count
        print('total_count=',total_count,'start_time=',start_time)

        current_time = time.mktime(datetime.datetime.now().timetuple()) 
        # 処理時間が2秒未満なら2秒wait
        if current_time - get_time < 2 :
            waitUntilReset(time.mktime(datetime.datetime.now().timetuple()) + 2)

        #デバッグ用
        if total > 0 :
            cnt += 100
        if total > 0 and cnt >= total:
            break


if __name__ == "__main__":
    args = sys.argv
    main(args)


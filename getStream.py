import tweepy  
import config
from datetime import timedelta

import datetime, time, sys
import re
import emoji


CK = config.CONSUMER_KEY
CS = config.CONSUMER_SECRET
AT = config.ACCESS_TOKEN
ATS = config.ACCESS_TOKEN_SECRET

p = re.compile('[\u3041-\u309F]+')

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



        streamText = status.text

        if streamText[0:3] != "RT " and status.in_reply_to_status_id_str != None:
            #print("RT")
        #else:

            streamText = screening(streamText)

            # only matched Japanese Character あ->ん
            if p.search(streamText):

                self.counter = self.counter + 1
                print('------------------------------')
                print(streamText)
                print("{name}({screen}) {created} via {src}\n".format(
                                                                    name=status.author.name, screen=status.author.screen_name,
                                                                    created=status.created_at, src=status.source))
                print(status.in_reply_to_status_id_str)
                print("Counter:%d" % self.counter)
        
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
stream.filter(track=['Go To'])

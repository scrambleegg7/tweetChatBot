from TweetsGetter import TweetsGetter


if __name__ == '__main__':

    # キーワードで取得
    getter = TweetsGetter.bySearch(u'頭痛')
    
    # ユーザーを指定して取得 （screen_name）
    #getter = TweetsGetter.byUser('AbeShinzo')

    cnt = 0
    for tweet in getter.collect(total = 30000):
        cnt += 1
        print ('------ %d' % cnt)
        print ('{} {} {}'.format(tweet['id'], tweet['created_at'], '@'+tweet['user']['screen_name']))
        print (tweet['text'])
 
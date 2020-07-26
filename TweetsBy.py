
from TweetsGetter import TweetsGetter

class TweetsGetterBySearch(TweetsGetter):
    '''
    キーワードでツイートを検索
    '''
    def __init__(self, keyword):
        super(TweetsGetterBySearch, self).__init__()
        self.keyword = keyword
        
    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/search/tweets.json'
        params = {'q':self.keyword, 'count':100}
        return url, params

    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text['statuses']:
            results.append(tweet)

        return results

    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['search']['/search/tweets']['remaining']
        reset     = res_text['resources']['search']['/search/tweets']['reset']

        return int(remaining), int(reset)
    

class TweetsGetterByUser(TweetsGetter):
    '''
    ユーザーを指定してツイートを取得
    '''
    def __init__(self, screen_name):
        super(TweetsGetterByUser, self).__init__()
        self.screen_name = screen_name
        
    def specifyUrlAndParams(self):
        '''
        呼出し先 URL、パラメータを返す
        '''
        url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
        params = {'screen_name':self.screen_name, 'count':200}
        return url, params

    def pickupTweet(self, res_text):
        '''
        res_text からツイートを取り出し、配列にセットして返却
        '''
        results = []
        for tweet in res_text:
            results.append(tweet)

        return results

    def getLimitContext(self, res_text):
        '''
        回数制限の情報を取得 （起動時）
        '''
        remaining = res_text['resources']['statuses']['/statuses/user_timeline']['remaining']
        reset     = res_text['resources']['statuses']['/statuses/user_timeline']['reset']

        return int(remaining), int(reset)


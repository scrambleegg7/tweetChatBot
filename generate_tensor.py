import pickle
import numpy as np



class GenTensorClass(object):

    def __init__(self, maxlen_e=50, maxlen_d=50):


        self.maxlen_e = maxlen_e
        self.maxlen_d = maxlen_d


        #単語ファイルロード
        with open('dict/words.pickle', 'rb') as f :
            self.words=pickle.load(f)    

        #作成した辞書をロード
        with open('dict/word_indices.pickle', 'rb') as f :
            self.word_indices=pickle.load(f)

        with open('dict/indices_word.pickle', 'rb') as g :
            self.indices_word = pickle.load(g)

        #コーパスロード
        with open('dict/mat_urtext.pickle', 'rb') as ff :
            self.mat_urtext = pickle.load(ff)




    def positioning(self):

        req = self.word_indices['REQREQ']
        res = self.word_indices['RESRES']

        print("reqreq", req)
        print("resres", res)

        self.delimiters  = []
        self.req_delimiters  = []
        self.res_delimiters  = []

        print("original word matrix size", self.mat_urtext.shape[0])
        #コーパス上のデリミタの位置を特定する
        for i in range(0,self.mat_urtext.shape[0]) :
            if self.mat_urtext[i,0] == req or self.mat_urtext[i,0] == res:
                self.delimiters.append(i)
            if self.mat_urtext[i,0] == req:
                self.req_delimiters.append(i)
            if self.mat_urtext[i,0] == res:
                self.res_delimiters.append(i)


        self.n = len( self.delimiters ) // 2
        print("half size of delimiters", self.n)
        #入力、ラベルテンソルの初期値定義（０値マトリックス）
        self.enc_input = np.zeros((self.n,  self.maxlen_e))
        self.dec_input = np.zeros((self.n,  self.maxlen_d))
        self.target = np.zeros((self.n,     self.maxlen_d))

    def process(self):
        pass


    def sanitaryCheck(self):

        print("counter REQREQ", len(self.req_delimiters))
        print("counter RESRES", len(self.res_delimiters))
        print("counter total REQ RES", len(self.delimiters))

        test_mat_index = self.mat_urtext[:20,0]
        print( test_mat_index )
        print( [ self.indices_word[n] for n in test_mat_index  ])
        test_words = [ self.indices_word[n] for n in test_mat_index  ]
        print( [ self.word_indices[n] for n in test_words  ])

        for idx, i in enumerate( self.req_delimiters[:-1] ):
            #print("---" * 5)
            #print(idx,i)
            #print( [indices_word[j]  for j in    mat_urtext[i:req_delimiters[idx+1]  ,0]])
            RESRES =  self.indices_word[ self.mat_urtext[   self.res_delimiters[idx], 0 ]   ]

            if RESRES != "RESRES":
                print("ERROR index : %d  req_delimiter_position : %d  "  % (idx, i)   )    


    def buildMatrix(self):

        print("building matrix...")

        j = 0
        for idx, i in enumerate( self.req_delimiters[:-1] ):
        
            len_e = self.res_delimiters[idx] - i 
            len_d = self.req_delimiters[idx+1] - self.res_delimiters[idx]
            
            if len_e < 0 or len_d < 0:
                print("** error **")
            #系列長より短い会話のみ、入力／ラベルマトリックスに書き込む
            if len_e <= self.maxlen_e and len_d <= self.maxlen_d  :
                self.enc_input[j,0:len_e] = self.mat_urtext[i:self.res_delimiters[idx],0].T
                self.dec_input[j,0:len_d] = self.mat_urtext[self.res_delimiters[idx]:self.req_delimiters[idx+1],0].T
                self.target[j,0:len_d] = self.mat_urtext[   (self.res_delimiters[idx] + 1):(self.req_delimiters[idx+1] + 1) , 0 ].T
                j += 1
            #if i % 1000000 == 0 :
            #    print(i)
        print("total ", j)


        #会話文データを書き込んだ分だけ切り出す
        e = self.enc_input[0:j,:].reshape(j,self.maxlen_e,1)
        d = self.dec_input[0:j,:].reshape(j,self.maxlen_d,1)
        t = self.target[0:j,:].reshape(j,self.maxlen_d,1)

        print(e.shape,d.shape,t.shape)

        print("Encoder Inputデータをセーブ")
        with open('dict/e.pickle', 'wb') as f :
            pickle.dump(e , f)

        #Decoder Inputデータをセーブ
        with open('dict/d.pickle', 'wb') as g :
            pickle.dump(d , g)

        #ラベルデータをセーブ
        with open('dict/t.pickle', 'wb') as h :
            pickle.dump(t , h)

        #maxlenセーブ
        with open('dict/maxlen.pickle', 'wb') as maxlen :
            pickle.dump([self.maxlen_e, self.maxlen_d] , maxlen)

def main():
    genTensor = GenTensorClass()
    genTensor.positioning()

    genTensor.sanitaryCheck()

    genTensor.buildMatrix()



if __name__ == "__main__":
    main()


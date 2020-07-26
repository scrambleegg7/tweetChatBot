import numpy.random as nr
import pickle
import numpy as np
import sys


def generate_tensors(maxlen_e,maxlen_d) :

    #--------------------------------------------------------------------------*
    #                                                                          *
    # 単語配列、コーパス配列、辞書のロード                                     *
    #                                                                          *
    #--------------------------------------------------------------------------*    

    #単語ファイルロード
    with open('dict/words.pickle', 'rb') as f :
        words=pickle.load(f)    

    #作成した辞書をロード
    with open('dict/word_indices.pickle', 'rb') as f :
        word_indices=pickle.load(f)

    with open('dict/indices_word.pickle', 'rb') as g :
        indices_word = pickle.load(g)

    #コーパスロード
    with open('dict/mat_urtext.pickle', 'rb') as ff :
        mat_urtext = pickle.load(ff)  


    print("top10 words")
    print(words[:10])
    print("- " * 20)
    print("word_indices")
    print(word_indices[:10])
    print("indices_word")
    print(indices_word[:10])
    print("mat_urtext")
    print(mat_urtext[:10, 0])
        
    #--------------------------------------------------------------------------*
    #                                                                          *
    # コーパスをエンコーダ入力、デコーダ入力応答文のテンソルに変換             *
    #                                                                          *
    #--------------------------------------------------------------------------*
    req = word_indices['REQREQ']
    res = word_indices['RESRES']

    print("index : req %d res %d" %  (req, res)  )

    delimiters  = []

    #コーパス上のデリミタの位置を特定する
    for i in range(0,mat_urtext.shape[0]) :
        if mat_urtext[i,0] == req or mat_urtext[i,0] == res:
            delimiters.append(i) 
        if i % 10000000 == 0 :
            print(i)

    print("delimiters length", len(delimiters))
    n=len(delimiters) // 2
    print("half size of delimiters.", n)

    #入力、ラベルテンソルの初期値定義（０値マトリックス）
    enc_input = np.zeros((n,maxlen_e))
    dec_input = np.zeros((n,maxlen_d))
    target = np.zeros((n,maxlen_d))

    #デリミタを目印に、コーパスから文章データを切り出して入力／ラベルマトリックスにコピー
    j = 0
    err_cnt = 0
    for i in range(0,n) :
        index1=2*i+err_cnt         # 「REQREQ」のインデックス
        index2=2*i+1+err_cnt       # 「RESRES」のインデックス
        index3=2*i+2+err_cnt       # 次の「REQREQ」のインデックス
        if index3 >= n :
            break
        #発話／応答の組が崩れていた時はスキップする
        if mat_urtext[delimiters[index1],0] != req or mat_urtext[delimiters[index2],0] != res :
            print('シーケンスエラー ',i)
            print(index1,index2)
            print(delimiters[index1],delimiters[index2])
            print(mat_urtext[delimiters[index1] ,0], mat_urtext[delimiters[index2],0])
            print(mat_urtext[delimiters[index1]:delimiters[index3],0])
            err_cnt += 1
            continue
        len_e = delimiters[index2] - delimiters[index1] - 1
        len_d = delimiters[index3] - delimiters[index2]
        #系列長より短い会話のみ、入力／ラベルマトリックスに書き込む
        if len_e <= maxlen_e and len_d <= maxlen_d  :
            enc_input[j,0:len_e] = mat_urtext[delimiters[index1]+1:delimiters[index2],0].T
            dec_input[j,0:len_d] = mat_urtext[delimiters[index2]:delimiters[index3],0].T
            target[j,0:len_d] = mat_urtext[delimiters[index2]+1:delimiters[index3]+1,0].T
            j += 1
        if i % 1000000 == 0 :
            print(i)

    #会話文データを書き込んだ分だけ切り出す
    e = enc_input[0:j,:].reshape(j,maxlen_e,1)
    d = dec_input[0:j,:].reshape(j,maxlen_d,1)
    t = target[0:j,:].reshape(j,maxlen_d,1)

    print(e.shape,d.shape,t.shape)

    # シャッフル処理
    z = list(zip(e, d, t))
    nr.seed(12345)
    nr.shuffle(z)                               #シャッフル
    e,d,t=zip(*z)
    nr.seed()

    e = np.array(e).reshape(j,maxlen_e,1)
    d = np.array(d).reshape(j,maxlen_d,1)
    t = np.array(t).reshape(j,maxlen_d,1)

    print(e.shape,d.shape,t.shape)

    #--------------------------------------------------------------------------*
    #                                                                          *
    # 作成したエンコーダ／デコーダ入力テンソル、ラベルテンソルをセーブ         *
    #                                                                          *
    #--------------------------------------------------------------------------* 
    #Encoder Inputデータをセーブ
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
        pickle.dump([maxlen_e, maxlen_d] , maxlen)

#*******************************************************************************
#                                                                              *
# メイン処理                                                                   *
#                                                                              *
#*******************************************************************************    
if __name__ == '__main__':  


    args = sys.argv

    #args[1] = 50                                              # jupyter上で実行するとき用
    #args[2] = 50                                              # jupyter上で実行するとき用

    generate_tensors(int(args[1]) ,int(args[2]))
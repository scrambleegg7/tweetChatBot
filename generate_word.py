# coding: utf-8

#**********************************************************************************
#                                                                                 *
#  juman++の品詞分解結果をリストに書き出し                                        *
#                                                                                 *
#**********************************************************************************
def genarate_npy(source_csv ,list_corpus) :
    #with open(source_csv, 'r') as f :
    with open(source_csv, encoding="utf_8") as file:

        df2 = csv.reader(file,delimiter=' ')
        #print(df2)

        mat = [ v for v in df2]
        print(len(mat))
        j=0
        #補正
        for i in range(0,len(mat)):
            if len(mat[i]) !=  0 :

                if mat[i][0] != '' :

                    if mat[i][0] != '@' and mat[i][0] != 'EOS' and mat[i][0] != ':' and mat[i][0][0] != '\\' :
                        if mat[i][0] == 'REQ' and mat[i+1][0] == '*' : #デリミタ「REQ:」対応
                            list_corpus.append('REQREQ')
                        elif mat[i][0] == 'RES' and mat[i+1][0] == '*' : #デリミタ「RES:」対応
                            list_corpus.append('RESRES')
                        else :
                            list_corpus.append(mat[i][0])
                        if i % 1000000 == 0 :
                            print(i,list_corpus[j])
                        j += 1

    print(len(list_corpus))
    del mat
    return 

#**********************************************************************************
#                                                                                 *
#  メイン処理                                                                     *
#                                                                                 *
#**********************************************************************************
if __name__ == '__main__':
    import numpy as np
    import csv
    import glob
    import re
    import pickle

    file_list = glob.glob('corpus/*')
    print(len(file_list))

    n_words = 0
    for j in range(0,len(file_list)) :

        print(file_list[j])
        generated_list=[]
        genarate_npy(file_list[j],generated_list)
        #コーパスリストセーブ
        with open('list_corpus/list_corpus'+str(j)+'.pickle', 'wb') as g :
            pickle.dump(generated_list , g)
        n_words += len(generated_list)
        print(n_words)
        del generated_list
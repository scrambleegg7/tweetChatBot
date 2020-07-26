
from pyknp import Juman
import numpy as np
import csv
import glob
import re

def modification(word) :
    if len(word) > 7 and word[:7] == 'SSSSUNK' :
        modified = ['SSSS', word[7:]]
    elif len(word) > 4 and word[:4] == 'SSSS' :
        modified = ['SSSS', word[4:]]
    elif word == 'UNKUNK' :
        modified = ['UNK']
    elif len(word) > 3 and word[:3] == 'UNK' :
        modified = ['UNK', word[3:]]
    
    elif len(word) > 10 and word[1:] == "'u3000":
        modified = ['UNK']
    else :
        modified = [word]
    return modified

def decomposition(file, jumanpp) :
    f=open(file, 'r')
    df1 = csv.reader(f)
    data = [ v for v in df1]
    print('number of rows :', len(data))

    parts = []
    for i in range(len(data)) :
        if len(data[i][0].encode('utf-8')) <= 4096 :
            result = jumanpp.analysis(data[i][0])
        else :
            print(i, ' skip')
            continue
        for mrph in result.mrph_list():
            parts += modification(mrph.midasi)
        if i % 50 == 0 :
            print(parts)
    return parts

def genarate_npy(source_csv ,list_corpus) :
    with open(source_csv, 'r') as f :

        df2 = csv.reader(f,delimiter=' ')

        mat = [ v for v in df2]
        print("length of sentences --> ", len(mat))
        j=0

        print(mat[0][0])
        #補正
        for i in range(0,len(mat)):
            if len(mat[i]) !=  0 :

                if mat[i][0] != '' :

                    if mat[i][0] != '@' and mat[i][0] != 'EOS' and mat[i][0] != ':' and mat[i][0][0] != '\\' :
                        if mat[i][0] == 'REQ' and mat[i+1][0] == ':' : #デリミタ「REQ:」対応
                            list_corpus.append('REQREQ')
                        elif mat[i][0] == 'RES' and mat[i+1][0] == ':' : #デリミタ「RES:」対応
                            list_corpus.append('RESRES')
                        else :
                            list_corpus.append(mat[i][0])
                        if i % 1000000 == 0 :
                            print(i,list_corpus[j])
                        j += 1

    print(len(list_corpus))
    del mat
    return 


def make_data(fname,data2) :
    f = open(fname, 'r')
    df1 = csv.reader(f)
    data1 = [ v for v in df1]

    print("length of data1", len(data1))
    
    print("first data of data1", data1[0])
    print("second data of data1", data1[1])    

    print("data [0] [0]",data1[0][0])
    #ファイル読み込み
    text = ''
    for i in range(0,len(data1)):
        if len(data1[i]) == 0:
            print('null')
            continue

        s = data1[i][0]
        if s[0:5] == "％ｃｏｍ：" :
            continue
        if s[0]  != '＠' :
            #不明文字をUNKに置き換え
            s = s.replace('＊＊＊','UNK')
            #会話文セパレータ
            if s[0] == 'F' or s[0] == 'M':
                s = 'SSSS'+s[5:]
            if s[0:2] == 'Ｘ：':
                s = 'SSSS'+s[2:]

            s = re.sub('F[0-9]{3}',"UNK",s)
            s = re.sub('M[0-9]{3}',"UNK",s)
            s = s.replace("＊","")
        else :
            continue

        while s.find("（") != -1 :
            start_1 = s.find("（")
            if s.find("）") != -1 :
                end_1 = s.find("）")
                if start_1 >= end_1 :
                    s = s.replace(s[end_1],"")
                else :
                    s = s.replace(s[start_1:end_1+1],"")
                if len(s) == 0 :
                    continue
            else :
                s=s[0:start_1]

        while s.find("［") != -1 :
            start_2 = s.find("［")
            if s.find("］") != -1 :
                end_2=s.find("］")
                s=s.replace(s[start_2:end_2+1],"")
            else :
                s=s[0:start_2]    

        while s.find("＜") != -1 :
            start_3 = s.find("＜")
            if s.find("＞") != -1 :
                end_3 = s.find("＞")
                s = s.replace(s[start_3:end_3+1],"")
            else :
                s = s[0:start_3] 

        while s.find("【") != -1 :
            start_4 = s.find("【")
            if s.find("】") != -1 :
                end_4 = s.find("】")
                s = s.replace(s[start_4:end_4+1],"")
            else :
                s = s[0:start_4] 

        #いろいろ削除したあとに文字が残っていたら出力文字列に追加
        if s != "\n" and s != "SSSS" :
            text += s
    #セパレータごとにファイル書き込み
    text =text[4:]
    while text.find("SSSS") != -1 :
        end_s = text.find("SSSS")
        t = text[0:end_s]
        #長い会話文を分割
        if end_s > 100 :
            while len(t) > 100 :
                if t.find("。") != -1 :
                    n_period = t.find("。")
                    data2.append("SSSS"+t[0:n_period+1])
                    t = t[n_period+1:]
                else :
                    break
        data2.append("SSSS"+t)
        text = text[end_s+4:]
    f.close()
    return

file_list = glob.glob('tweet/*')
print("file names : " , file_list)
print(len(file_list))

jumanpp = Juman()

data2=[]
for j in range(0,len(file_list)) :
    print("processing ....", file_list[j])
    #make_data(file_list[j],data2)
    data2 += decomposition(file_list[j], jumanpp)
#ファイルセーブ
#f = open('corpus/corpus_TWEET.txt','w')
#for i in range(0,len(data2)):
#    f.write(str(data2[i])+"\n")
#f.close()
#print(len(data2))
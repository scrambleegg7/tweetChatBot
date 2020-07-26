
#from pyknp import Juman
import MeCab

import csv
import glob
import re,os
import codecs
import pandas as pd
from io import StringIO
import numpy as np
from collections import defaultdict
from sklearn.feature_extraction.text import CountVectorizer
import string
import unicodedata
import urllib.request as urllib2
import platform

import pickle

import numpy as np
import neologdn
import sys

sys.path.insert(0,'./unicode_script_for_python')

import unicode_script_map as usm
from unicode_script import ScriptType


plt = platform.system()

#mecab = MeCab.Tagger ('-Ochasen')
if plt == "Linux":
    tagger = MeCab.Tagger('-d /usr/lib/mecab/dic/mecab-ipadic-neologd')
if plt == "Windows":
    tagger = MeCab.Tagger("-r C:\MeCab\etc\mecabrc")

def remove_unicode(text):
    removed_str = "".join([c for c in text if usm.get_script_type(c) != ScriptType.U_Common])
    return removed_str


def sloth_stop_words():
    slothlib_path = 'http://svn.sourceforge.jp/svnroot/slothlib/CSharp/Version1/SlothLib/NLP/Filter/StopWord/word/Japanese.txt'
    slothlib_file = urllib2.urlopen(slothlib_path)
    slothlib_stopwords = [line.decode("utf-8").strip() for line in slothlib_file]
    slothlib_stopwords = [ss for ss in slothlib_stopwords if not ss==u'']
    
    #print(slothlib_stopwords)
    return slothlib_stopwords

def req_res_sentence_adjust(data):
    
    flag = 0
    prev_idx = 0
    req_idx = []
    res_idx = []

    print("req res sentence adjust routine (replace short with long sentence.)")

    for idx, d in enumerate(data):

        prefix = data[idx][0].split(":")[0]
        sentence = data[idx][0].split(":")[1]
        
        if len(sentence) < 10:
            #print("short response/ request ")
            print(idx,prefix,sentence)
            if prefix == "REQ":
                req_idx.append(idx)
            if prefix == "RES":
                res_idx.append(idx)
                    
        if prefix == "REQ" and idx % 2 == 0:
            flag = 1
            prev_idx = idx
        if prefix == "RES" and idx % 2 == 1:
            if idx - prev_idx != 1:
                print("ERROR", prev_idx, idx)    
    
    return req_idx, res_idx

def req_res_sentence_swap(data, req_idx, res_idx):

    for req_i in req_idx:
        sentence = data[req_i + 1][0].split(":")[1]
        #print(sentence)
        data[req_i][0] = "REQ:" + sentence

    for res_i in res_idx:
        sentence = data[res_i - 1][0].split(":")[1]
        data[res_i][0] = "RES:" + sentence

    return data

def removeChar(text):
    
    text=re.sub(r'[!-~]', "", text)#半角記号,数字,英字
    text=re.sub(r'[︰-＠]', "", text)#全角記号
    text=re.sub('\n', " ", text)#改行文字
    text=re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
        
    text = unicodedata.normalize("NFKC", text)  # 全角記号をざっくり半角へ置換（でも不完全）

    text = remove_unicode(text)
    
    kigo = string.punctuation + "「」、。・"
    collon = str.maketrans( '', '',':')
    
    kigo = kigo.translate(collon)
    table = str.maketrans( '', '',kigo)
    text = text.translate(table)

    return text

def sentence_neologdn(data):

    for idx, d in enumerate(data):

        prefix = data[idx][0].split(":")[0]
        sentence = data[idx][0].split(":")[1]
        
        sentence = neologdn.normalize(sentence)
        # remove Char
        sentence = removeChar(sentence)
        data[idx][0] = prefix + ":" + sentence

    return data

def removeShortSentence(data):
    
    flag = 0
    prev_idx = 0
    req_idx = []
    res_idx = []
    
    new_data = []

    print("remove short sentence.")

    for idx in range(0, len(data), 2):

        prefix = data[idx][0].split(":")[0]
        sentence_req = data[idx][0].split(":")[1]
        sentence_res = data[idx][0].split(":")[1]
        
        if len(sentence_req) >= 10:
            new_data.append( data[idx]    )
            new_data.append( data[idx+1]    )
                     
            #print("short response/ request ")

    return  new_data

def is_nan(x):
    return (x != x)

def lower_text(text):
    return text.lower()

def normalize_number(text):
    # 連続した数字を0で置換

    replaced_text = re.sub(r'\d+', '0', text)
    return replaced_text

def decomposition(file, stop_words) :
    with codecs.open(file, "r", "utf8", "ignore") as f:

        df1 = csv.reader(f)
        data = [ v for v in df1]
        print('number of rows :', len(data))

        data = sentence_neologdn(data)
        req_idx, res_idx = req_res_sentence_adjust(data)
        data = req_res_sentence_swap(data, req_idx, res_idx)
        data = removeShortSentence(data)
        print("sanitary checking...")
        _, _ = req_res_sentence_adjust(data)

        parts = []

        # Stop Words
        count_vectorizer = CountVectorizer(stop_words=stop_words,token_pattern=u'(?u)\\b\\w+\\b')
                    
        reqreq_counts = []
        resres_counts = []

        skip_counts = 0
        prev_ok_sentence = ""
        for i in range(len(data)) :

            #words_store = []

            prefix = data[i][0].split(":")[0]
            sentence = data[i][0].split(":")[1]

            #if prefix == "REQ":
            if (re.search("REQ:", data[i][0])):
                #words_store.append("REQREQ")
                prefix = "REQREQ"
                reqreq_counts.append("REQREQ")
            #if prefix == "RES":
            if (re.search("RES:", data[i][0])):
                #words_store.append("RESRES")
                prefix = "RESRES"
                resres_counts.append("RESRES")

            try:
                result = tagger.parse(sentence)
                df_analyzed = pd.read_csv(StringIO(result), delimiter='\t', names=['単語'] )
            except:
                print("- " * 20)
                print()
                print("*********          error           ********")
                print("ERROR Contents --> ", data[i][0])

                continue

            sentence_extracted_words = []
            
            for idx, w in enumerate(df_analyzed["単語"]):
                #print(w.split(",")[6])
                if w != "EOS" and not is_nan(w):

                    #word = w.split(",")[6]
                    word = df_analyzed.index[idx]
                    type = w.split(",")[0]
                    if not type in ("名詞","動詞","形容詞","感動詞"):
                        continue
                        
                    word = normalize_number(word)
                    word = lower_text(word)
                    #print("words...%d %s " % (idx, word)  )
                    if word in ["go", "to", "goto"]:
                        continue

                    sentence_extracted_words.append(word)
            

                else :
                    #print(i, ' skip')
                    skip_counts += 1
                    continue


            try:
                feature_vectors = count_vectorizer.fit_transform(sentence_extracted_words)
                vocabulary = count_vectorizer.get_feature_names()
                sentence_extracted_words = [p for p in sentence_extracted_words if p in vocabulary ]

                if len(sentence_extracted_words) == 0:
                    print("")
                    print("*********          error  ZERO WORDS          ********")
                    print("  ERROR Contents --> ", prefix, sentence)
                else:
                    parts.extend( [prefix] )
                    parts.extend( sentence_extracted_words)
                    prev_ok_sentence = sentence_extracted_words 
            except:
                print()
                print("")
                print("*********    stop words error           ********")
                print("ERROR Contents --> ", prefix, sentence)
                print("mecab split words : ", sentence_extracted_words)
                print("---  ")
                print("** replaced wrong with previous sentence **")
                print(prev_ok_sentence)
                parts.extend( [prefix] )
                parts.extend( prev_ok_sentence )



        #for mrph in result:
                
            if i % 1000 == 0 :
                print("--  " *20)
                #print(df_analyzed)
                print("sentence line counts --> ", (i)  )
                print("original sentence : ", data[i][0])
                print("word counts by MeCab :", len(parts))
                print("extracted words : ", sentence_extracted_words)

    print("reqreq counter", len(reqreq_counts))
    print("resres counter", len(resres_counts))
                    #print("Skip counts :", skip_counts)
                    #print(df_analyzed)
                    #print("--  " *20)

    #print("Total Skip counts ", skip_counts)
    print("parts printing (top100)...")
    print(parts[:100])
    print("====")

    new_parts = []
    re_hiragana = re.compile(r'[あ-んA-Za-z0-9]$')
    hiragana_status = [ re_hiragana.fullmatch(w) for w in parts]
    for idx, status in enumerate(hiragana_status):
        if not status:
            new_parts.append(parts[idx])

    return new_parts


def wordFreqChecker(data):

    frequency = defaultdict(int)

    for w in data:
        frequency[w] += 1

    dataset = [w for w in data if frequency[w] > 1]

    return dataset

def main():

    path = "corpus/stop_words.txt"
    #stop_words = create_stopwords(path)
    sloth_stopwords = sloth_stop_words()

    file_list = glob.glob('tweet/*')
    print("file names : " , file_list)
    print(len(file_list))

    data2=[]
    for j in range(0,len(file_list)) :
        print("processing ....", file_list[j])
        #make_data(file_list[j],data2)
        data2 += decomposition(file_list[j], sloth_stopwords ) #, jumanpp)
    
    data2 = wordFreqChecker(data2)

    #ファイルセーブ
    print("corpus file save. total word counts --> ", len(data2))
    f = open('corpus/corpus_TWEET.txt','w')
    for i in range(0,len(data2)):
        try:
            f.write(str(data2[i])+"\n")
        except:
            print("")
            print("******  WRITE ERROR   *********")
            print(data2[i])
    f.close()
    #print(len(data2))


    print("--- " * 40)
    print("******* build pickle file saving word *******")
    file_list = glob.glob('corpus/*')
    print(len(file_list))

    n_words = 0
    #コーパスリストセーブ
    with open('list_corpus/list_corpus_0.pickle', 'wb') as g :
        pickle.dump(data2 , g)

if __name__ == "__main__":
    main()

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

plt = platform.system()

#mecab = MeCab.Tagger ('-Ochasen')
if plt == "Linux":
    tagger = MeCab.Tagger('-d /usr/lib/mecab/dic/mecab-ipadic-neologd')
if plt == "Windows":
    tagger = MeCab.Tagger("-r C:\MeCab\etc\mecabrc")

def unicode_normalize(cls, s):
    pt = re.compile('([{}]+)'.format(cls))

    def norm(c):
        return unicodedata.normalize('NFKC', c) if pt.match(c) else c

    s = ''.join(norm(x) for x in re.split(pt, s))
    s = re.sub('－', '-', s)
    return s

def remove_extra_spaces(s):
    s = re.sub('[ 　]+', ' ', s)
    blocks = ''.join(('\u4E00-\u9FFF',  # CJK UNIFIED IDEOGRAPHS
                      '\u3040-\u309F',  # HIRAGANA
                      '\u30A0-\u30FF',  # KATAKANA
                      '\u3000-\u303F',  # CJK SYMBOLS AND PUNCTUATION
                      '\uFF00-\uFFEF'   # HALFWIDTH AND FULLWIDTH FORMS
                      ))
    basic_latin = '\u0000-\u007F'

    def remove_space_between(cls1, cls2, s):
        p = re.compile('([{}]) ([{}])'.format(cls1, cls2))
        while p.search(s):
            s = p.sub(r'\1\2', s)
        return s

    s = remove_space_between(blocks, blocks, s)
    s = remove_space_between(blocks, basic_latin, s)
    s = remove_space_between(basic_latin, blocks, s)
    return s

def normalize_neologd(s):
    s = s.strip()
    s = unicode_normalize('０-９Ａ-Ｚａ-ｚ｡-ﾟ', s)

    def maketrans(f, t):
        return {ord(x): ord(y) for x, y in zip(f, t)}

    s = re.sub('[˗֊‐‑‒–⁃⁻₋−]+', '-', s)  # normalize hyphens
    s = re.sub('[﹣－ｰ—―─━ー]+', 'ー', s)  # normalize choonpus
    s = re.sub('[~∼∾〜〰～]', '', s)  # remove tildes
    s = s.translate(
        maketrans('!"#$%&\'()*+,-./:;<=>?@[¥]^_`{|}~｡､･｢｣',
              '！”＃＄％＆’（）＊＋，－．／：；＜＝＞？＠［￥］＾＿｀｛｜｝〜。、・「」'))

    s = remove_extra_spaces(s)
    s = unicode_normalize('！”＃＄％＆’（）＊＋，－．／：；＜＞？＠［￥］＾＿｀｛｜｝〜', s)  # keep ＝,・,「,」
    s = re.sub('[’]', '\'', s)
    s = re.sub('[”]', '"', s)
    return s

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

def omitChar(text):
    text=re.sub('お気に入り', "", text)
    text=re.sub('まとめ', "", text)
    #text=re.sub(r'[!-~]', "", text)#半角記号,数字,英字
    text=re.sub(r'[︰-＠]', "", text)#全角記号
    text=re.sub('\n', " ", text)#改行文字 
    
    #kigo = '\"!"#$%&'()*+\,-./;<=>?@[\]^_`{|}~"'
    kigo = string.punctuation
    collon = str.maketrans( '', '',':')
    
    kigo = kigo.translate(collon)
    table = str.maketrans( '', '',kigo)
    text = text.translate(table)
    
    return text

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

        req_idx, res_idx = req_res_sentence_adjust(data)
        data = req_res_sentence_swap(data, req_idx, res_idx)
        print("sanitary checking...")
        _, _ = req_res_sentence_adjust(data)

        parts = []

        reqreq_counts = []
        resres_counts = []

        skip_counts = 0
        for i in range(len(data)) :
            if len(data[i][0].encode('utf-8')) <= 4096 :

                
                try:
                    after_data =omitChar(data[i][0])
                    result = tagger.parse(after_data)
                    df_analyzed = pd.read_csv(StringIO(result), delimiter='\t', names=['単語'] )
                except:
                    print("- " * 20)
                    print()
                    print("*********          error           ********")
                    #print(data[i][0])
                    print("BEFORE--> ",normalize_neologd(data[i][0]))
                    after_data =omitChar(data[i][0])
                    print("AFTER --> ", after_data)
                    #result = tagger.parse( after_data )
                    #df_analyzed = pd.read_csv(StringIO(result), delimiter='\t', names=['単語'] )

                    continue

                sentence_extracted_words = []
                for idx, w in enumerate(df_analyzed["単語"]):
                    #print(w.split(",")[6])
                    if w != "EOS" and not is_nan(w):

                        #word = w.split(",")[6]
                        word = df_analyzed.index[idx]
                        type = w.split(",")[0]
                        if not type in ("名詞","動詞","形容詞"):
                            continue

                        if word == "REQ" and df_analyzed.index[idx+1] == ":":
                            word = "REQREQ"
                            reqreq_counts.append(word)
                        if word == "RES" and df_analyzed.index[idx+1] == ":":
                            word = "RESRES"
                            resres_counts.append(word)
                            
                        word = normalize_number(word)
                        word = lower_text(word)
                        #print("words...%d %s " % (idx, word)  )
                        if word in ["go", "to", "goto"]:
                            continue
                        parts.append( word )
                        sentence_extracted_words.append(word)
                

                    else :
                        #print(i, ' skip')
                        skip_counts += 1
                        continue
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

    print("Total Skip counts ", skip_counts)

    print("exclude Stop words")
    count_vectorizer = CountVectorizer(stop_words=stop_words,token_pattern=u'(?u)\\b\\w+\\b')
    feature_vectors = count_vectorizer.fit_transform(parts)
    vocabulary = count_vectorizer.get_feature_names()


    parts = [p for p in parts if p in vocabulary ]
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
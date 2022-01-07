"""
Python script to generate lipogrammatic word list and enciphered dictionary
"""

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--letters', type=str, help='Even number of letters (e.g. abcd)')
args = parser.parse_args()
letters = list(args.letters)
lst_letters = list(letters)
print('letters: %s' % lst_letters)

# for debugging
letters = 'abcdef'
lst_letters = list(letters)

assert len(letters) % 2 == 0, 'There are an odd number of letters!'

# Load modules
import os
import requests
import numpy as np
import pandas as pd
from time import time
from funs_cipher import encipherer

##########################
# --- (1) DICTIONARY --- #

# source: http://wordlist.aspell.net/12dicts/

url_dict='https://cfhcable.dl.sourceforge.net/project/wordlist/12Dicts/6.0/12dicts-6.0.2.zip'



annos = '%:&#=<^~+$'
annos = '|'.join(['\\'+anno for anno in list(annos)])

dir_dicts = os.path.join(os.getcwd(), 'dicts')
fn_dicts = pd.Series(os.listdir(dir_dicts))
fn_dicts = fn_dicts[fn_dicts.str.contains('.txt',regex=False)]
holder = []
for fn in fn_dicts:
    print(fn)
    path = os.path.join(dir_dicts, fn)
    tmp_df = pd.read_csv(path, sep='\t', header=None, na_values='',keep_default_na=False)
    tmp_df.rename(columns={0:'word'}, inplace=True)
    tmp_df['word'] = tmp_df['word'].str.strip()
    tmp_df = tmp_df.drop_duplicates()
    holder.append(tmp_df)
df_12 = pd.concat(holder).drop_duplicates()
# Keep letters only
df_12['word'] = df_12['word'].str.replace('[^a-zA-Z\\-]',' ')
# Lower case
df_12['word'] = df_12['word'].str.lower()
# Clean up spaces
df_12['word'] = df_12['word'].str.strip()
df_12['word'] = df_12['word'].str.replace('\\s{2,}',' ')
df_12 = df_12.assign(word=lambda x: x['word'].str.split('\\s')).explode('word')
df_12 = df_12.drop_duplicates()
# Add n-grams
df_12 = df_12.merge(df_1gram,'inner')
# df_12['n'] = df_12['n'].fillna(df_12['n'].min()).astype(int)
# Sort
df_12 = df_12.sort_values('n',ascending=False).reset_index(drop=True)

# (v) Add on definitions where possible
url_api = 'https://api.dictionaryapi.dev/api/v2/entries/en'
stime = time()
n_word = len(df_12)
holder = []
for i, word in enumerate(df_12['word']):
    if (i+1) % 10 == 0:
        dtime = time() - stime
        rate = (i+1)/dtime
        n_left = n_word-i-1
        eta = n_left / rate
        print('Iteration %i of %i (ETA: %i seconds)' % (i+1, n_word, eta))
    url_word = os.path.join(url_api, word)
    json = requests.get(url_word).text
    if not 'No Definitions Found' in json:
        json = pd.read_json(json)
        pos = json['meanings'][0][0]['partOfSpeech']
        res = pd.DataFrame({'word':word, 'pos':pos},index=[i])
        holder.append(res)
res_dict = pd.concat(holder)


##########################
# --- (2) ENCIPHERED --- #

self = encipherer(df_english=df_12, cn_word='word')
self.set_letters(letters=letters)
self.get_pos()
self.score_ciphers(cn_weight='n')
self.df_score
self.df_encipher



########################
# --- (X)  --- #

# # (i) n-gram data from
# url_1gram = 'http://norvig.com/ngrams/count_1w.txt'
# fn_1gram = 'words_ngram.txt'

# if not os.path.exists(fn_1gram):
#     os.system('wget -q -O %s %s' % (fn_1gram, url_1gram))

# df_1gram = pd.read_csv(fn_1gram, sep='\t',header=None,na_values='',keep_default_na=False)
# df_1gram.rename(columns={0:'word', 1:'n'}, inplace=True)

# # (ii) simple english words
# url_english = 'https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt'
# fn_english = 'words_english.txt'

# if not os.path.exists(fn_english):
#     os.system('wget -q -O %s %s' % (fn_english, url_english))

# df_english = pd.read_csv(fn_english, sep='\t',header=None,na_values='',keep_default_na=False)
# df_english.rename(columns={0:'word'}, inplace=True)

# # (iii) Keep only intersection
# df_merge = df_1gram.merge(df_english,'inner')
# # Check that it has same words as xenotext
# xenotext = pd.read_csv('xenotext.txt',header=None)[0].to_list()
# xenotext = sum([z.split(' ') for z in xenotext], [])
# xenowords = np.unique(xenotext)
# word_match = df_merge['word'][df_merge['word'].isin(xenowords)]
# word_diff = np.setdiff1d(xenowords, word_match)
# assert len(word_diff) == 0, 'Missing words: %s' % word_diff


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
import numpy as np
import pandas as pd
from funs_cipher import encipherer

########################
# --- (1) GET DATA --- #

# (i) n-gram data from
url_1gram = 'http://norvig.com/ngrams/count_1w.txt'
fn_1gram = 'words_ngram.txt'

if not os.path.exists(fn_1gram):
    os.system('wget -q -O %s %s' % (fn_1gram, url_1gram))

df_1gram = pd.read_csv(fn_1gram, sep='\t',header=None,na_values='',keep_default_na=False)
df_1gram.rename(columns={0:'word', 1:'n'}, inplace=True)

# (ii) simple english words
url_english = 'https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt'
fn_english = 'words_english.txt'

if not os.path.exists(fn_english):
    os.system('wget -q -O %s %s' % (fn_english, url_english))

df_english = pd.read_csv(fn_english, sep='\t',header=None,na_values='',keep_default_na=False)
df_english.rename(columns={0:'word'}, inplace=True)

# (iii) Keep only intersection
df_merge = df_1gram.merge(df_english,'inner')
# Check that it has same words as xenotext
xenotext = pd.read_csv('xenotext.txt',header=None)[0].to_list()
xenotext = sum([z.split(' ') for z in xenotext], [])
xenowords = np.unique(xenotext)
word_match = df_merge['word'][df_merge['word'].isin(xenowords)]
word_diff = np.setdiff1d(xenowords, word_match)
assert len(word_diff) == 0, 'Missing words: %s' % word_diff

# (iv) 12 dicts data: http://wordlist.aspell.net/12dicts/
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
for word in df_12['word']:
    word
    break

##########################
# --- (2) ENCIPHERED --- #

self = encipherer(df_english=df_12, cn_word='word')
self.set_letters(letters=letters)
self.get_pos()
self.score_ciphers(cn_weight='n')
self.df_score
self.df_encipher



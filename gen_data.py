"""
Python script to generate lipogrammatic word list and enciphered dictionary
"""

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--letters', type=str, help='Even number of letters (e.g. abcd)')
args = parser.parse_args()
print(args)
letters = args.letters
lst_letters = list(letters)
print('letters: %s' % (lst_letters))
assert len(letters) % 2 == 0, 'There are an odd number of letters!'

# # for debugging
# letters = 'etoaisnrlchdum'
# lst_letters = list(letters)

# Load modules
import os
import pickle
import requests
import numpy as np
import pandas as pd
from time import time, sleep
from zipfile import ZipFile
from funs_support import download
from funs_cipher import encipherer
from string import ascii_lowercase as lowercase

# Get world list from Xenotext
xenotext = pd.read_csv('xenotext.txt',header=None)[0].to_list()
xenotext = sum([z.split(' ') for z in xenotext], [])
xenowords = np.unique(xenotext)


##########################
# --- (1) DICTIONARY --- #

# source: http://wordlist.aspell.net/12dicts/
url_dict='https://cfhcable.dl.sourceforge.net/project/wordlist/12Dicts/6.0/12dicts-6.0.2.zip'
if not os.path.exists('dicts'):
    print('Downloading dictionary')
    # Download zip file
    fn = 'tmp.zip'
    download(url=url_dict, path=fn)
    # Unzip
    with ZipFile(fn, 'r') as zip:
        zip.extractall('dicts')
    os.remove(fn)
else:
    print('dicts folder already exists locally')

# Define the annotations to remove
annos = '%:&#=<^~+$'
annos = '|'.join(['\\'+anno for anno in list(annos)])

# Walk through subfolders
dir_dicts = os.path.join(os.getcwd(), 'dicts')
fold_dicts = [x[0] for x in os.walk(dir_dicts)][1:]
holder = []
for fold in fold_dicts:
    fn_dicts = pd.Series(os.listdir(fold))
    fn_dicts = fn_dicts[fn_dicts.str.contains('.txt',regex=False)]
    for fn in fn_dicts:
        print(fn)
        path = os.path.join(fold, fn)
        tmp_df = pd.read_csv(path, sep='\t', header=None, na_values='',keep_default_na=False)
        tmp_df.rename(columns={0:'word'}, inplace=True)
        tmp_df['word'] = tmp_df['word'].str.strip()
        tmp_df = tmp_df.drop_duplicates()
        holder.append(tmp_df)
df_dict = pd.concat(holder).drop_duplicates()
# Keep letters only
df_dict['word'] = df_dict['word'].str.replace('[^a-zA-Z\\-]',' ',regex=True)
# Lower case
df_dict['word'] = df_dict['word'].str.lower()
# Clean up spaces
df_dict['word'] = df_dict['word'].str.strip()
df_dict['word'] = df_dict['word'].str.replace('\\s{2,}',' ',regex=True)
df_dict = df_dict.assign(word=lambda x: x['word'].str.split('\\s')).explode('word')
# Remove anything that starts or ends with a hyphen
df_dict = df_dict[~df_dict['word'].str.contains('^\\-|\\-$',regex=True)]
# Remove single letters except A/I
letter1 = np.setdiff1d(list(lowercase), ['a','i'])
df_dict = df_dict[~df_dict['word'].isin(letter1)]
# Remove all two letter words except reserved list
letter2 = ['ab','ad','ah','am','an','as','at','aw','ax','be','bc','by','ce','do','eu','ew','go','ha','he','hi','id','if','in','iq','is','it','me','my','of','oh','ok','on','or','ow','ox','pi','so','to','uh','uk','um','up','us','we']
letter2 = np.setdiff1d([[l1+l2 for l2 in lowercase] for l1 in lowercase], letter2)
df_dict = df_dict[~df_dict['word'].isin(letter2)]
# Remove duplicates
df_dict = df_dict.drop_duplicates().reset_index(drop=True)


#########################
# --- (2) WORD FREQ --- #

# source: norvig.com
url_1gram = 'http://norvig.com/ngrams/count_1w.txt'
fn_1gram = 'words_ngram.csv'
download(url=url_1gram, path=fn_1gram, overwrite=False)
df_1gram = pd.read_csv(fn_1gram, sep='\t',header=None,na_values='',keep_default_na=False)
df_1gram.rename(columns={0:'word', 1:'n'}, inplace=True)


###########################
# --- (3) DEFINITIONS --- #

# source: https://api.dictionaryapi.dev/api/v2/entries/en/<word>
url_dict='https://raw.githubusercontent.com/meetDeveloper/freeDictionaryAPI/master/meta/wordList/english.txt'
fn_dict=url_dict.split('/')[-1]
download(url=url_dict, path=fn_dict)
df_def = pd.read_csv(url_dict,header=None,on_bad_lines='skip')
df_def = df_def.rename(columns={0:'word'}).assign(has_def=True)

# source: https://github.com/krishnakt031990
url_acro = 'https://raw.githubusercontent.com/krishnakt031990/Crawl-Wiki-For-Acronyms/master/AcronymsFile.csv'
fn_acro = url_acro.split('/')[-1]
download(url=url_acro, path=fn_acro)
df_acro = pd.read_csv(fn_acro, on_bad_lines='skip', header=None)
df_acro.rename(columns={0:'word'}, inplace=True)
df_acro['word'] = df_acro['word'].str.strip()
df_acro['word'] = df_acro['word'].str.split('\\s\\-',1,True)[0]
df_acro['word'] = df_acro['word'].str.strip().str.lower()
df_acro = df_acro.assign(is_acro=True).drop_duplicates()


#####################
# --- (4) MERGE --- #

# (i) Merge English dictionary with word frequency
df_merge = df_dict.merge(df_1gram,'left')
n_min = df_merge['n'].min()
df_merge['n'] = df_merge['n'].fillna(n_min).astype(int)
# (ii) See if a definition is available
df_merge = df_merge.merge(df_def,'left').fillna(False)
# (iii) Subset to defintion only
df_merge = df_merge.query('has_def')
df_merge.drop(columns='has_def', inplace=True)
# # (iv) Add on possible acronoym
# df_merge = df_merge.merge(df_acro,'left').fillna(False)
# (v) Sort
df_merge.sort_values('n',ascending=False,inplace=True)
df_merge.reset_index(drop=True,inplace=True)
# (vi) Check for Xenotext alignment
word_match = df_merge['word'][df_merge['word'].isin(xenowords)]
word_diff = np.setdiff1d(xenowords, word_match)
assert len(word_diff) == 0, 'Missing words: %s' % word_diff


########################
# --- (5) ENCIPHER --- #

# Run the encipherment
enc = encipherer(df_english=df_merge, cn_word='word', cn_weight='n')
enc.set_letters(letters=letters)
enc.get_pos()
enc.score_ciphers(set_best=True)


###############################
# --- (6) GET DEFINITIONS --- #

# 300 request per 5 minutes!!!!

url_api = 'https://api.dictionaryapi.dev/api/v2/entries/en'
n_word = len(enc.word_list)
holder = []
for i, word in enumerate(enc.word_list):
    stime = time()
    if (i+1) % 10 == 0:
        print('Definition %i of %i' % (i+1, n_word))
    url_word = os.path.join(url_api, word)
    json = requests.get(url_word).text
    if not 'No Definitions Found' in json:
        json = pd.read_json(json)
        # Get definitions and parts of speech
        meanings = json['meanings'][0]
        if 'definitions' in meanings[0]:
            lst_def = [k['definitions'][0]['definition'].replace('.','') for k in meanings]
        else:
            lst_def = ['']
        if 'partOfSpeech' in meanings[0]:
            lst_pos = [k['partOfSpeech'] for k in meanings]
        else:
            lst_pos = ['']
        pos_def = ' | '.join([p+': '+d for d,p in zip(lst_def, lst_pos)])
        res = pd.DataFrame({'word':word, 'def':pos_def},index=[i])
        holder.append(res)
    dtime = time() - stime
    # Need to ensure we do not submit more than one request per second
    if dtime < 1:
        sleep(1 - dtime + 0.01)
res_def = pd.concat(holder)
res_def.to_csv('res_def.csv',index=False)
# res_def = pd.read_csv('res_def.csv')
# Add on the relevant definitions
enc.df_english = enc.df_english.merge(res_def,'left','word').fillna('')

# Pickle
with open('enc.pickle', 'wb') as handle:
    pickle.dump(enc, handle, protocol=pickle.HIGHEST_PROTOCOL)

print('~~~ End of gen_data.py ~~~')
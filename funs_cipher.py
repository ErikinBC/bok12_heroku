# Functions to support enciphered alphabet

import nltk
import string
import numpy as np
import pandas as pd
from time import time
from scipy.special import comb
from funs_support import capture, str_replace, str_translate

"""
df_english:         A DataFrame with a column of words (and other annotations)
cn_word:            Column name in df_english with the English words
letters:            A string of letters (e.g. "abqz")
n_letters:          If letters is None, how many letters to pick from
idx_letters:        If letters is None, which combination index to pick from
"""
class encipherer():
    def __init__(self, df_english, cn_word, cn_weight):
        # df_english=df_merge.copy();cn_word='word';cn_weight='w'
        assert isinstance(df_english, pd.DataFrame), 'df_english needs to be a DataFrame'
        cn_dtype = df_english.dtypes[cn_weight]
        assert (cn_dtype == float) | (cn_dtype == int), 'cn_weight needs to be a float/int not %s' % cn_dtype
        self.df_english = df_english.rename(columns={cn_word:'word', cn_weight:'weight'}).drop_duplicates()
        assert not self.df_english['word'].duplicated().any(), 'Duplicate words found'
        self.latin = string.ascii_lowercase
        self.n = len(self.latin)

    """
    After class has been initialized, letters must be chosen. This can be done by either manually specifying the letters, or picking from (26 n_letters)
    letters:        String (e.g. 'aBcd')
    n_letters:      Number of letters to use (must be ≤ 26)
    idx_letters:    When letters is not specified, which of the combination indices to use from (n C k) choices
    """
    def set_letters(self, letters=None, n_letters=None, idx_letters=None):
        if letters is not None:
            assert isinstance(letters, str), 'Letters needs to be a string'
            self.letters = pd.Series([letter.lower() for letter in letters])
            self.letters = self.letters.drop_duplicates()
            self.letters = self.letters.sort_values().reset_index(drop=True)
            self.n_letters = self.letters.shape[0]
            self.idx_max = {k:v[0] for k,v, in self.n_encipher(self.n_letters).to_dict().items()}
        else:
            has_n = n_letters is not None
            has_idx = idx_letters is not None
            assert has_n and has_idx, 'If letters is None, n_letters and idx_letters must be provided'
            self.idx_max = {k:v[0] for k,v, in self.n_encipher(n_letters).to_dict().items()}
            assert idx_letters <= self.idx_max['n_lipogram'], 'idx_letters must be ≤ %i' % self.idx_max['n_lipogram']
            assert idx_letters > 0, 'idx_letters must be > 0'
            self.n_letters = n_letters
            tmp_idx = self.get_comb_idx(idx_letters, self.n, self.n_letters)
            self.letters = pd.Series([self.latin[idx-1] for idx in tmp_idx])
            self.letters = self.letters.sort_values().reset_index(drop=True)
        assert self.n_letters % 2 == 0, 'n_letters must be an even number'
        assert self.n_letters <= self.n, 'n_letters must be ≤ %i' % self.n
        self.k = int(self.n_letters/2)
        # Remove words that have a letter outside of the lipogram
        words = self.df_english['word'].str.lower()
        self.regex_lipo = '[%s]' % ''.join(np.setdiff1d(list(self.latin), self.letters))
        self.regex_keep = '[^%s]' % ''.join(self.letters)
        self.df_english = self.df_english[~words.str.contains(self.regex_lipo)]
        self.df_english.reset_index(drop=True, inplace=True)

    
    """
    After letters have been set, either specify mapping or pick from an index
    pairing:        String specifying pairing order (e.g. 'a:e, i:o')
    idx_pairing:    If the pairing is not provided, pick one of the 1 to n_encipher possible permutations
    """
    def set_encipher(self, pairing=None, idx_pairing=None):
        # idx_pairing=1
        if pairing is not None:
            assert isinstance(pairing, str), 'pairing needs to be a string'
            lst_pairing = pairing.replace(' ','').split(',')
            self.mat_pairing = np.array([pair.split(':') for pair in lst_pairing])
            assert self.k == self.mat_pairing.shape[0], 'number of rows does not equal k: %i' % self.k
            assert self.mat_pairing.shape[1] == 2, 'mat_pairing does not have 2 columns'
            tmp_letters = self.mat_pairing.flatten()
            n_tmp = len(tmp_letters)
            assert n_tmp == self.n_letters, 'The pairing list does not match number of letters: %i to %i' % (n_tmp, self.n_letters)
            lst_miss = np.setdiff1d(self.letters, tmp_letters)
            assert len(lst_miss) == 0, 'pairing does not have these letters: %s' % lst_miss
        else:
            assert idx_pairing > 0, 'idx_pairing must be > 0'
            assert idx_pairing <= self.idx_max['n_encipher'], 'idx_pairing must be ≤ %i' % self.idx_max['n_encipher']
            # Apply determinstic formula
            self.mat_pairing = self.get_encipher_idx(idx_pairing)
        # Pre-calculated values for alpha_trans() method
        s1 = ''.join(self.mat_pairing[:,0])
        s2 = ''.join(self.mat_pairing[:,1])
        self.trans = str.maketrans(s1+s2, s2+s1)
        self.str_pairing = pd.DataFrame(self.mat_pairing)
        self.str_pairing = ','.join(self.str_pairing.apply(lambda x: x[0]+':'+x[1],1))


    """
    Find enciphered corpus
    """
    def get_corpus(self):
        # Pure letters only
        lwords = pd.Series(str_replace(self.df_english['word'].str.lower(), self.regex_keep, ''))
        # Find word matches
        words_trans = self.alpha_trans(lwords)
        idx_match = lwords.isin(words_trans)
        tmp1 = self.df_english['word'][idx_match]
        tmp2 = self.alpha_trans(self.df_english['word'])[idx_match]
        # Combine with annotations
        tmp_df = pd.DataFrame({'num':range(len(tmp1)),'x':tmp1,'y':tmp2})    
        tmp_df = tmp_df.melt('num',None,'tt','word')
        tmp_df = tmp_df.merge(self.df_english,'left')
        cn_val = ['word', 'weight']
        if hasattr(self, 'pos_def'):
            cn_val += ['pos']
        cn_val += list(np.setdiff1d(tmp_df.columns,['num','tt']+cn_val))
        tmp_df = tmp_df.pivot_table(values=cn_val,index='num',columns='tt',aggfunc=lambda x: x)[cn_val]
        # Save as df_encipher
        tmp_df.columns = ['_'.join(col) for col in tmp_df.columns.values]
        # Add on any other columns from the original dataframe
        self.df_encipher = tmp_df.reset_index().assign(num=lambda x: x['num']+1)
        cn_weight = ['weight_x', 'weight_y']
        self.df_encipher = self.df_encipher.assign(weight=lambda x: x[cn_weight].min(1)).drop(columns=cn_weight)
        

    """
    Iterate through all possible cipher combinations
    cn_weight:          A column from df_english that has a numerical score
    set_best:           Should the highest scoring index be set for idx_pairing?
    """
    def score_ciphers(self, set_best=True):
        # self=enc;set_best=True
        n_encipher = self.idx_max['n_encipher']
        holder = np.zeros([n_encipher,2])
        self.word_list = []
        stime = time()
        for i in range(1, n_encipher+1):
            if (i + 1) % 25 == 0:
                dtime = time() - stime
                rate, n_left = i/dtime, n_encipher-i
                eta = n_left / rate
                n_words = len(self.word_list)
                print('Cipher %i of %i, n_words=%i (ETA: %i seconds)' % (i+1, n_encipher, n_words, eta))
            self.set_encipher(idx_pairing=i)
            self.get_corpus()
            self.word_list = np.union1d(self.word_list,self.df_encipher['word_x'])
            # Calcule the number of words and the weighted score
            n_i = self.df_encipher.shape[0]
            w_i = self.df_encipher['weight'].sum()
            holder[i-1] = [n_i, w_i]
        # Get the rank
        self.df_score = pd.DataFrame(holder,columns=['n_word','weight'])
        self.df_score['n_word'] = self.df_score['n_word'].astype(int)
        self.df_score = self.df_score.rename_axis('idx').reset_index()
        self.df_score['idx'] += 1
        self.df_score = self.df_score.sort_values('weight',ascending=False).reset_index(drop=True)
        if set_best:
            self.set_encipher(idx_pairing=self.df_score['idx'][0])
            self.get_corpus()

    """
    Get the different parts of speech
    """
    def get_pos(self):
        pos_lst = [z[1] for z in nltk.pos_tag(self.df_english['word'].to_list())]
        pos_lst = pd.Series(pos_lst).str.replace('[^A-Z]','',regex=True)
        self.df_english.insert(self.df_english.shape[1],'pos',pos_lst)
        self.pos_def = pd.Series([capture(nltk.help.upenn_tagset,p) for p in self.df_english['pos'].unique()])
        self.pos_def = self.pos_def.str.split('\\:\\s|\\n',expand=True,n=3).iloc[:,:2]
        self.pos_def.rename(columns={0:'pos',1:'desc'},inplace=True)

    """
    Deterministically returns encipher
    """
    def get_encipher_idx(self, idx):
        j = 0
        lst = self.letters.to_list()
        holder = np.repeat('1',self.n_letters).reshape([self.k, 2])
        for i in list(range(self.n_letters-1,0,-2)):
            l1 = lst[0]
            q, r = divmod(idx, i)
            r += 1
            l2 = lst[r]
            lst.remove(l1)
            lst.remove(l2)
            holder[j] = [l1, l2]
            j += 1
            idx = q
        return holder

    """
    Deterministically return (n C k) indices
    """
    @staticmethod
    def get_comb_idx(idx, n, k):
        c, r, j = [], idx, 0
        for s in range(1,k+1):
            cs = j+1
            while r-comb(n-cs,k-s)>0:
                r -= comb(n-cs,k-s)
                cs += 1
            c.append(cs)
            j = cs
        return c

    """
    Uses mat_pairing to translate the strings
    txt:        Any string or Series
    """
    def alpha_trans(self, txt):
        # Remove any of the letters not to be found
        z = pd.Series(str_translate(txt, self.trans))
        return z

    """
    Function to calculate total number lipogrammatic and enciphering combinations
    """
    @staticmethod
    def n_encipher(n_letters):
        assert n_letters % 2 == 0, 'n_letters is not even'
        n1 = int(np.prod(np.arange(1,n_letters,2)))
        n2 = int(comb(26, n_letters))
        n_tot = n1 * n2
        res = pd.DataFrame({'n_letter':n_letters,'n_encipher':n1, 'n_lipogram':n2, 'n_total':n_tot},index=[0])
        return res

import os
import io
import re
import requests
import contextlib
import numpy as np

# Vectorized string replace
def gsub(string, pat, rep):
    return re.sub(pat, rep, string)

str_replace = np.vectorize(gsub, excluded=['pat','rep'])

# Vectorize string translation
def tsub(string, trans):
    return string.translate(trans)

str_translate = np.vectorize(tsub, excluded=['trans'])

# Calculate total memory in use
def all_mem():
    import psutil
    process = psutil.Process(os.getpid())
    mi = process.memory_info()
    return sum([z for z in mi])

# Capture print output
def capture(fun,arg):
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        fun(arg)
    output = f.getvalue()
    return output


# Save download
def download(url, path=None, overwrite=False):
    if path is None:
        path = url.split('/')[-1]
    if (not os.path.exists(path)) | overwrite:
        req = requests.get(url)
        with open(path, 'wb') as file:
            file.write(req.content)
    else:
        print('File will not downloaded')

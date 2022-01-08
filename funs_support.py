import os
import io
import requests
import contextlib

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

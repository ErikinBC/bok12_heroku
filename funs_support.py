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
def download(url, path=None):
    req = requests.get(url)
    if path is None:
        path = req.url.split('/')[-1]
    with open(path, 'wb') as file:
        file.write(req.content)

import io
import contextlib

def capture(fun,arg):
    f = io.StringIO()
    with contextlib.redirect_stdout(f):
        fun(arg)
    output = f.getvalue()
    return output


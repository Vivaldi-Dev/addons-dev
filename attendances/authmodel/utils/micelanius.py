import hashlib
import os
from datetime import datetime, timedelta


def random_token(length=40, prefix="", cicles=8):
    rbytes = ""
    for i in range(cicles):
        rbytes += "{}".format(str(hashlib.sha1(os.urandom(length)).hexdigest()))
    now = datetime.now().timestamp()
    return "{}{}{}".format(prefix, rbytes, now)

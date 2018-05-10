
import re

evil_fn_chars_re = re.compile('[\\/:"*?<>|]+')
def sanitize_filename(filename):
    """
    Dis-allow characters not allowed on all platforms
    This is so you can't save '*' which doesn't work on Windows
    which prevents ZK portability.
    """
    return evil_fn_chars_re.sub('-', filename)
    

import os
import os.path
import sys

from distutils import sysconfig
from distutils.core import setup

try:
    import xpybutil
except:
    print ''
    print 'pager-multihead requires xpybutil'
    print 'See: https://github.com/BurntSushi/xpybutil'

try:
    import pygtk
    pygtk.require('2.0')
    import gtk
except:
    print ''
    print 'pager-multihead requires pygtk'
    print 'See: http://www.pygtk.org/'
    sys.exit(1)

try:
    import keybinder
except:
    print ''
    print 'pager-multihead requires python-keybinder'
    print 'See: https://github.com/engla/keybinder'
    sys.exit(1)

setup(
    name = 'pager-multihead',
    author = 'Andrew Gallant',
    author_email = 'andrew@pytyle.com',
    version = '0.0.1',
    license = 'WTFPL',
    description = 'A pager that supports per-monitor desktops',
    long_description = 'See README',
    url = 'https://github.com/BurntSushi/pager-mutlihead',
    platforms = 'POSIX',
    packages = ['pagermh'],
    data_files = [('share/doc/pager-multihead', ['README', 'COPYING', 'INSTALL']),
                  ('/etc/xdg/pager-multihead', 
                   ['config.py', 'keymousebind.py'])],
    scripts = ['pager-multihead']
)


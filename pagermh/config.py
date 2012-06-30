import os
import os.path
import sys

xdg = os.getenv('XDG_CONFIG_HOME') or os.path.join(os.getenv('HOME'), '.config')
conffile = os.path.join(xdg, 'pager-multihead', 'config.py')

if not os.access(conffile, os.R_OK):
    conffile = os.path.join('/', 'etc', 'xdg', 'pager-multihead', 'config.py')
    if not os.access(conffile, os.R_OK):
        print >> sys.stderr, 'UNRECOVERABLE ERROR: ' \
                             'No configuration file found at %s' % conffile
        sys.exit(1)

execfile(conffile)

def desk_views(config):
    return not hasattr(config, "show_desk_views") or config.show_desk_views


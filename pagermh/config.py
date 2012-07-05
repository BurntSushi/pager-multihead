import argparse
import os
import os.path
import sys

parser = argparse.ArgumentParser(
    description='Pager that manages dynamic workspaces for Openbox Multihead.',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
aa = parser.add_argument
aa('-x', type=int, metavar='X_POSITION', default=None,
   help='Force a particular x position of the pager. This overrides any '
        'value specified in the config file.')
aa('-y', type=int, metavar='Y_POSITION', default=None,
   help='Force a particular y position of the pager. This overrides any '
        'value specified in the config file.')
aa('--width', type=int, metavar='WIDTH', default=None,
   help='Force a particular width of the pager. This overrides any '
        'value specified in the config file.')
aa('--height', type=int, metavar='HEIGHT', default=None,
   help='Force a particular height of the pager. This overrides any '
        'value specified in the config file.')
args = parser.parse_args()

xdg = os.getenv('XDG_CONFIG_HOME') or os.path.join(os.getenv('HOME'), '.config')
conffile = os.path.join(xdg, 'pager-multihead', 'config.py')

if not os.access(conffile, os.R_OK):
    conffile = os.path.join('/', 'etc', 'xdg', 'pager-multihead', 'config.py')
    if not os.access(conffile, os.R_OK):
        print >> sys.stderr, 'UNRECOVERABLE ERROR: ' \
                             'No configuration file found at %s' % conffile
        sys.exit(1)

execfile(conffile)

# Check the x/y/width/height values if set on the command line.
if args.x is not None:
    x = args.x
if args.y is not None:
    y = args.y
if args.width is not None:
    width = args.width
if args.height is not None:
    height = args.height

def desk_views(config):
    return not hasattr(config, "show_desk_views") or config.show_desk_views


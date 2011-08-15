import sys
import time

import gtk
import keybinder

from xpybutil import conn, root
import xpybutil.ewmh as ewmh

wmrunning = False
while not wmrunning:
    w = ewmh.get_supporting_wm_check(conn, root).reply()
    if w:
        childw = ewmh.get_supporting_wm_check(conn, w).reply()
        if childw == w:
            wmrunning = True
            wmname = ewmh.get_wm_name(conn, childw).reply()
            print '%s window manager is running...' % wmname
            sys.stdout.flush()

    time.sleep(1)

import xcb.xinerama

import config
from keymousebind import keybinds

xinerama = conn(xcb.xinerama.key)

gtk_display = gtk.gdk.display_get_default()
gtk_screen = gtk_display.get_default_screen()
gtk_root = gtk_screen.get_root_window()
gtk_rootwin = gtk.Invisible()

gtk_root.set_user_data(gtk_rootwin)
gtk_root.set_events(gtk.gdk.PROPERTY_CHANGE_MASK | gtk.gdk.KEY_PRESS_MASK)

# Initial setup
ewmh.set_desktop_names_checked(conn, root, config.desktops).check()
ewmh.set_desktop_layout_checked(conn, root, ewmh.Orientation.Horz, 
                                len(config.desktops), 1, 
                                ewmh.StartingCorner.TopLeft).check()
ewmh.request_number_of_desktops_checked(conn, len(config.desktops)).check()

# Is this a horizontal or vertical pager?
if config.width > config.height:
    orient = 'H'
elif config.width < config.height:
    orient = 'V'
else: # weirdo, could go either way
    orient = 'V'

# Grab keybindings
for key_string, fun in keybinds.iteritems():
    if not keybinder.bind(key_string, fun):
        print >> sys.stderr, 'could not bind %s' % key_string

# Start loading information
desk_num = ewmh.get_number_of_desktops(conn, root).reply()
desk_names = ewmh.get_desktop_names(conn, root).reply()
root_geom = ewmh.get_desktop_geometry(conn, root).reply()

activewin = ewmh.get_active_window(conn, root).reply()
desktop = ewmh.get_current_desktop(conn, root).reply()
stacking = ewmh.get_client_list_stacking(conn, root).reply()
visibles = ewmh.get_visible_desktops(conn, root).reply()

clients = {}
monitors = []
xtophys = []

def get_desk_name(i):
    if i < len(desk_names):
        return desk_names[i]
    else:
        return str(i)

def rect_intersect_area(r1, r2):
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    if x2 < x1 + w1 and x2 + w2 > x1 and y2 < y1 + h1 and y2 + h2 > y1:
        iw = min(x1 + w1 - 1, x2 + w2 - 1) - max(x1, x2) + 1
        ih = min(y1 + h1 - 1, y2 + h2 - 1) - max(y1, y2) + 1
        return iw * ih

    return 0

def get_monitor_area(search):
    marea = 0
    mon = None
    for mx, my, mw, mh in monitors:
        a = rect_intersect_area((mx, my, mw, mh), search)
        if a > marea:
            marea = a
            mon = (mx, my, mw, mh)

    return mon

def update_monitor_area():
    global monitors, xtophys

    monitors = []
    screenpos = []
    xtophys = []

    for i, m in enumerate(xinerama.QueryScreens().reply().screen_info):
        monitors.append((m.x_org, m.y_org, m.width, m.height))
        screenpos.append((m.y_org, m.x_org, i))
    for x, y, xscreen in sorted(screenpos):
        xtophys.append(xscreen)

# def cb_keypress(widget, e): 
    # print 'hey-oh' 

def cb_keypress(event):
    print 'hey-oh'
    print event.type
    print '-' * 80
    sys.stdout.flush()
    return gtk.gdk.FILTER_CONTINUE

def cb_prop_change(widget, e):
    global activewin, desk_names, desk_num, desktop, stacking, visibles

    if e.atom == '_NET_DESKTOP_GEOMETRY':
        root_geom = ewmh.get_desktop_geometry(conn, root).reply()
        update_monitor_area()
    elif e.atom == '_NET_ACTIVE_WINDOW':
        activewin = ewmh.get_active_window(conn, root).reply()
    elif e.atom == '_NET_CURRENT_DESKTOP':
        desktop = ewmh.get_current_desktop(conn, root).reply()
    elif e.atom == '_NET_CLIENT_LIST_STACKING':
        stacking = ewmh.get_client_list_stacking(conn, root).reply()
    elif e.atom == '_NET_VISIBLE_DESKTOPS':
        visibles = ewmh.get_visible_desktops(conn, root).reply()
    elif e.atom in ('_NET_DESKTOP_NAMES', '_NET_NUMBER_OF_DESKTOPS'):
        desk_num = ewmh.get_number_of_desktops(conn, root).reply()
        desk_names = ewmh.get_desktop_names(conn, root).reply()

        # This works around what I think is weird behavior in Openbox.
        # Sometimes Openbox will "fix" the desktop names... please don't!
        if len(desk_names) > desk_num:
            names = desk_names[0:desk_num]
            ewmh.set_desktop_names_checked(conn, root, names).check()
        desk_names = ewmh.get_desktop_names(conn, root).reply()


update_monitor_area()
    

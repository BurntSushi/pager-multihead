import sys
import time

import gtk
import keybinder

import xpybutil
from xpybutil.compat import xinerama
import xpybutil.ewmh as ewmh

wmname = 'N/A'
wmrunning = False
while not wmrunning:
    w = ewmh.get_supporting_wm_check(xpybutil.root).reply()
    if w:
        childw = ewmh.get_supporting_wm_check(w).reply()
        if childw == w:
            wmrunning = True
            wmname = ewmh.get_wm_name(childw).reply()
            print '%s window manager is running...' % wmname
            sys.stdout.flush()

    if not wmrunning:
        time.sleep(1)

import config
from keymousebind import keybinds

xinerama = xpybutil.conn(xinerama.key)

gtk_display = gtk.gdk.display_get_default()
gtk_screen = gtk_display.get_default_screen()
gtk_root = gtk_screen.get_root_window()
gtk_rootwin = gtk.Invisible()

gtk_root.set_user_data(gtk_rootwin)
gtk_root.set_events(gtk.gdk.PROPERTY_CHANGE_MASK | gtk.gdk.KEY_PRESS_MASK)

# Initial setup
if config.desktops:
    ewmh.set_desktop_names_checked(config.desktops).check()
    ewmh.set_desktop_layout_checked(ewmh.Orientation.Horz, 
                                    len(config.desktops), 1, 
                                    ewmh.StartingCorner.TopLeft).check()
    ewmh.request_number_of_desktops_checked(len(config.desktops)).check()

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
desk_num = ewmh.get_number_of_desktops().reply()
desk_names = ewmh.get_desktop_names().reply()
root_geom = ewmh.get_desktop_geometry().reply()

activewin = ewmh.get_active_window().reply()
desktop = ewmh.get_current_desktop().reply()
stacking = ewmh.get_client_list_stacking().reply()
visibles = ewmh.get_visible_desktops().reply()

clients = {}
monitors = []
xtophys = []

def get_desk_name(i):
    if i < len(desk_names):
        return desk_names[i]
    else:
        return str(i)

def update_monitor_area():
    global monitors, xtophys

    monitors = []
    screenpos = []
    xtophys = []

    for i, m in enumerate(xinerama.QueryScreens().reply().screen_info):
        monitors.append((m.x_org, m.y_org, m.width, m.height))
        screenpos.append((m.x_org, m.y_org, i))
    for x, y, xscreen in sorted(screenpos):
        xtophys.append(xscreen)

def cb_prop_change(widget, e):
    global activewin, desk_names, desk_num, desktop, stacking, visibles

    if e.atom == '_NET_DESKTOP_GEOMETRY':
        root_geom = ewmh.get_desktop_geometry().reply()
        update_monitor_area()
    elif e.atom == '_NET_ACTIVE_WINDOW':
        activewin = ewmh.get_active_window().reply()
    elif e.atom == '_NET_CURRENT_DESKTOP':
        desktop = ewmh.get_current_desktop().reply()
    elif e.atom == '_NET_CLIENT_LIST_STACKING':
        stacking = ewmh.get_client_list_stacking().reply()
    elif e.atom == '_NET_VISIBLE_DESKTOPS':
        visibles = ewmh.get_visible_desktops().reply()
    elif e.atom in ('_NET_DESKTOP_NAMES', '_NET_NUMBER_OF_DESKTOPS'):
        desk_num = ewmh.get_number_of_desktops().reply()
        desk_names = ewmh.get_desktop_names().reply()

        # This works around what I think is weird behavior in Openbox.
        # Sometimes Openbox will "fix" the desktop names... please don't!
        if len(desk_names) > desk_num:
            names = desk_names[0:desk_num]
            ewmh.set_desktop_names_checked(names).check()
        desk_names = ewmh.get_desktop_names().reply()

update_monitor_area()
    

import gtk

from xpybutil.compat import xproto
import xpybutil.ewmh as ewmh
import xpybutil.rect as rect
import xpybutil.util as util
import xpybutil.window as window

import state
import pager

def update_tracking_clients():
    clist = ewmh.get_client_list().reply()
    for c in clist:
        if c not in state.clients:
            track_client(c)
    for c in state.clients.keys():
        if c not in clist:
            untrack_client(c)

def track_client(c):
    assert c not in state.clients

    wstate = ewmh.get_wm_state(c).reply()
    for atom in wstate:
        aname = util.get_atom_name(atom)
        
        # For now, while I decide how to handle these guys
        if aname == '_NET_WM_STATE_STICKY':
            break
        if aname in ('_NET_WM_STATE_SHADED', '_NET_WM_STATE_SKIP_PAGER',
                     '_NET_WM_STATE_HIDDEN'):
            break
    else:
        state.clients[c] = Client(c)

def untrack_client(c):
    assert c in state.clients

    client = state.clients[c]
    del state.clients[c]
    client.remove()

def cb_prop_change(widget, e):
    if e.atom == '_NET_CLIENT_LIST':
        update_tracking_clients()

class Client(object):
    def __init__(self, wid):
        self.wid = wid
        self.gdk = gtk.gdk.window_foreign_new_for_display(state.gtk_display, 
                                                          self.wid)
        self.name = ewmh.get_wm_name(self.wid).reply()
        self.geom = self.get_geometry()
        self.desk = ewmh.get_wm_desktop(self.wid).reply()
        self.invis = gtk.Invisible()

        self.gdk.set_events(gtk.gdk.PROPERTY_CHANGE_MASK
                            | gtk.gdk.STRUCTURE_MASK)
        self.gdk.set_user_data(self.invis)
        self.invis.connect('property_notify_event', self.cb_prop_change)

        # This is interesting; look for configure events on the decor window
        if state.wmname.lower() == 'openbox':
            pid = window.get_parent_window(self.wid)
            pgdk = gtk.gdk.window_foreign_new_for_display(state.gtk_display,
                                                          pid)
            pinvis = gtk.Invisible()
            pgdk.set_events(gtk.gdk.STRUCTURE_MASK)
            pgdk.set_user_data(pinvis)
            pinvis.connect('configure_event', self.cb_configure)
        else:
            self.invis.connect('configure_event', self.cb_configure)

        self.update_state()

    def update_state(self):
        self.hidden = False
        
        hatom = util.get_atom('_NET_WM_STATE_HIDDEN')
        states = ewmh.get_wm_state(self.wid).reply()
        if states is not None and hatom in states:
            self.hidden = True

    def get_monitor_area(self):
        return rect.get_monitor_area(self.geom, state.monitors)

    def get_geometry(self):
        return window.get_geometry(self.wid)

    def remove(self):
        pager.update(self.desk)

    def cb_configure(self, widget, event):
        # Sometimes we'll get a configure event from a window that is dead
        try:
            self.geom = self.get_geometry()
            pager.update(self.desk)
        except xproto.BadWindow:
            pass

    def cb_prop_change(self, widget, e):
        try:
            if e.atom == '_NET_WM_DESKTOP':
                newd = ewmh.get_wm_desktop(self.wid).reply()
                if newd is not None and newd != self.desk:
                    oldd = self.desk
                    self.desk = newd
                    pager.update(oldd)
                    pager.update(self.desk)
            elif e.atom == '_NET_WM_STATE':
                self.update_state()
                pager.update(self.desk)
        except xproto.BadWindow:
            pass

update_tracking_clients()


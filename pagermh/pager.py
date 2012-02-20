import gtk

import xpybutil.ewmh as ewmh
import xpybutil.rect as rect

import config
from keymousebind import desktop_clicked
import state

desktops = []

_window = None
_box = None

def init():
    global _window, _box

    _window = gtk.Window(gtk.WINDOW_TOPLEVEL)

    _window.connect('delete_event', gtk.main_quit)

    if config.dock:
        _window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
    else:
        _window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_NORMAL)

    if config.sticky:
        _window.stick()
    if config.above:
        _window.set_keep_above(True)

    _window.set_resizable(False)
    _window.set_decorated(False)
    _window.set_title('pager-multihead')
    _window.set_skip_pager_hint(True)
    _window.set_skip_taskbar_hint(True)
    _window.set_geometry_hints(None, min_width=config.width,
                               min_height=config.height, max_width=config.width,
                               max_height=config.height)
    _window.move(config.x, config.y)

    _window.modify_bg(gtk.STATE_NORMAL, 
                      gtk.gdk.color_parse(config.pager_bgcolor))

    if state.orient == 'H':
        _box = gtk.HBox(True, 0)
    else:
        _box = gtk.VBox(True, 0)
    _window.add(_box)

    for i in xrange(state.desk_num):
        d = Desktop(i)
        _box.pack_start(d.box, True, True, 0)
        desktops.append(d)

    update_desktop_order()
    _window.show_all()

    # If the user says to set struts, we *will* do it.
    # We are a little bit smart, though... We'll account for dead area.
    # This does not allow for between-monitor struts... For another day!
    if config.struts:
        wx, wy, ww, wh = config.x, config.y, config.width, config.height
        mx, my, mw, mh = rect.get_monitor_area((wx, wy, ww, wh), state.monitors)
        rw, rh = state.root_geom['width'], state.root_geom['height']

        struts = { nm: 0 for nm in
                            ['left', 'right', 'top', 'bottom',
                             'left_start_y', 'left_end_y',
                             'right_start_y', 'right_end_y',
                             'top_start_x', 'top_end_x',
                             'bottom_start_x', 'bottom_end_x'] }
        if state.orient == 'V':
            # left or right?
            if wx < rw / 2: # left
                struts['left'] = ww + mx + wx
                struts['left_start_y'] = wy
                struts['left_end_y'] = wy + wh
            else: # right
                struts['right'] = ww + rw - mw - mx
                struts['right_start_y'] = wy
                struts['right_end_y'] = wy + wh
        else:
            # top or bottom?
            if wy < rh / 2: # top
                struts['top'] = wh + my
                struts['top_start_x'] = wx
                struts['top_end_x'] = wx + ww
            else: #bottom
                struts['bottom'] = wh + rh - mh - my
                struts['bottom_start_x'] = wx
                struts['bottom_end_x'] = wx + ww

        ewmh.set_wm_strut_partial_checked(_window.window.xid, **struts).check()

def update_desktop_order():
    if not state.visibles:
        return
    for physind, xscreen in enumerate(state.xtophys):
        for d in desktops:
            if d.desk == state.visibles[xscreen]:
                old = desktops[physind]
                d.desk, old.desk = old.desk, d.desk

def update(d):
    if d < len(desktops):
        for desk in desktops:
            if desk.desk == d:
                desk.update()

def update_all():
    for d in desktops:
        d.update()

def cb_prop_change(widget, e):
    if e.atom in ('_NET_CLIENT_LIST', '_NET_ACTIVE_WINDOW',
                  '_NET_CURRENT_DESKTOP', '_NET_CLIENT_LIST_STACKING',
                  '_NET_DESKTOP_NAMES'):
        update_all()
    elif e.atom == '_NET_VISIBLE_DESKTOPS':
        update_desktop_order()
        update_all()
    elif e.atom == '_NET_NUMBER_OF_DESKTOPS':
        if state.desk_num < len(desktops):
            while state.desk_num < len(desktops):
                lastdesk = None
                for i, d in enumerate(desktops):
                    if lastdesk is None or d.desk > desktops[lastdesk].desk:
                        lastdesk = i
                desktops.pop(lastdesk).destroy()
        elif state.desk_num > len(desktops):
            while state.desk_num > len(desktops):
                d = Desktop(len(desktops))
                _box.pack_start(d.box, True, True, 0)
                desktops.append(d)

        update_desktop_order()
        update_all()

class Desktop(object):
    def __init__(self, desk):
        self.desk = desk
        self.area = gtk.DrawingArea()
        self.cmap = self.area.get_colormap()
        self.label = None
        self.eb = None
        self.gc = None
        self.box = gtk.VBox(False, 0)

        self.box.pack_start(self.area, True, True, 0)

        if config.show_desk_names:
            self.eb = gtk.EventBox()
            self.eb.modify_bg(gtk.STATE_NORMAL, 
                              gtk.gdk.color_parse(config.pager_bgcolor))
            self.label = gtk.Label()
            self.eb.add(self.label)
            self.box.pack_start(self.eb, False, False, 2)

        self.area.add_events(gtk.gdk.EXPOSURE_MASK
                             | gtk.gdk.BUTTON_PRESS_MASK)

        self.area.connect('expose-event', self.cb_exposed)
        self.area.connect('button_press_event', self.cb_button_press)
        self.box.show_all()

    def destroy(self):
        self.box.destroy()

    def update(self):
        x, y, w, h = self.get_pos_size()

        if self.label is not None:
            if self.desk == state.desktop:
                markup = config.active_name_markup
            elif state.visibles and self.desk in state.visibles:
                markup = config.visible_name_markup
            else:
                markup = config.hidden_name_markup
            self.label.set_markup(markup % state.get_desk_name(self.desk))
            self.eb.modify_bg(gtk.STATE_NORMAL,
                              gtk.gdk.color_parse(config.pager_bgcolor))

        if self.gc is None:
            self.gc = self.area.window.new_gc()

        self.gc.foreground = self.color(config.pager_bgcolor)
        self.area.window.draw_rectangle(self.gc, True, 0, 0,
                                        *self.area.window.get_size())

        self.gc.foreground = self.color(config.desk_bordercolor)
        self.area.window.draw_rectangle(self.gc, False, x, y, w, h)

        if self.desk == state.desktop:
            self.gc.foreground = self.color(config.active_desk_color)
        elif state.visibles and self.desk in state.visibles:
            self.gc.foreground = self.color(config.visible_desk_color)
        else:
            self.gc.foreground = self.color(config.hidden_desk_color)
        self.area.window.draw_rectangle(self.gc, True, x + 1, y + 1, 
                                        w - 1, h - 1)

        toint = lambda f: int(round(f))

        for cid in state.stacking:
            if cid not in state.clients:
                continue

            c = state.clients[cid]

            if c.desk != self.desk or c.hidden:
                continue

            mx, my, mw, mh = c.get_monitor_area()

            cx, cy, cw, ch = c.geom
            ratx = float(w) / mw
            raty = float(h) / mh

            # Get the initial scaled positions of this client
            dx = toint(x + 1 + (cx - mx) * ratx)
            dy = toint(y + 1 + (cy - my) * raty)
            dw = toint(cw * ratx - 1)
            dh = toint(ch * raty - 1)

            # Now bound them
            if dx < x + 1:
                dw -= (x + 1) - dx
            if dy < y + 1:
                dh -= (y + 1) - dy

            dx = min(w - 1, max(x + 1, dx))
            dy = min(h - 1, max(y + 1, dy))

            if dx + dw > x + w:
                dw -= dx + dw - (x + w)
            if dy + dh > y + h:
                dh -= dy + dh - (y + h)

            dw = max(1, dw)
            dh = max(1, dh)

            self.gc.foreground = self.color(config.window_border_color)
            self.area.window.draw_rectangle(self.gc, False, dx, dy, dw, dh)

            if c.wid == state.activewin:
                self.gc.foreground = self.color(config.active_window_color)
            else:
                self.gc.foreground = self.color(config.window_color)

            self.area.window.draw_rectangle(self.gc, True, 
                                            dx + 1, dy + 1, dw - 1, dh - 1)

    def get_pos_size(self):
        if self.area.window is None:
            return None

        m = config.desk_margin
        w, h = self.area.window.get_size()
        return m, m, w - (2 * m), h - (2 * m)

    def color(self, scolor):
        return self.cmap.alloc_color(gtk.gdk.color_parse(scolor))

    def cb_button_press(self, widget, e):
        desktop_clicked(self)

    def cb_exposed(self, area, e):
        self.update()

init()


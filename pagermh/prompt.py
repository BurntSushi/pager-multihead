import sys

import gobject
import gtk
import pango

from xpybutil import conn, root
import xpybutil.ewmh as ewmh

import config
import state

# I don't know why this is necessary, but I'm saving the last Prompt displayed
# so that it doesn't get used again. It was a very nutty problem.
currentPrompt = None

# Do some options

def desktops(result_fun, prefix_complete=True, homogenous=True):
    global currentPrompt

    desks = range(0, ewmh.get_number_of_desktops(conn, root).reply())
    names = ewmh.get_desktop_names(conn, root).reply()
    lst = []
    for d in desks:
        nm = names[d] if d < len(names) else d
        lst.append((nm, nm))

    currentPrompt = Prompt({ None: sorted(lst) }, result_fun, prefix_complete,
                           homogenous)

def windows(result_fun, prefix_complete=False, homogenous=False):
    global currentPrompt


    desks = range(0, ewmh.get_number_of_desktops(conn, root).reply())
    names = ewmh.get_desktop_names(conn, root).reply()

    content = {}
    for d in desks:
        name = d
        if d < len(names):
            name = names[d]

        content[name] = []

    clients = ewmh.get_client_list_stacking(conn, root).reply()
    for c in reversed(clients):
        nm = ewmh.get_wm_desktop(conn, c).reply()
        if nm < len(names):
            nm = names[nm]
        if nm in content:
            content[nm].append((ewmh.get_wm_name(conn, c).reply(), c))

    currentPrompt = Prompt(content, result_fun, prefix_complete, homogenous)

class Prompt(object):
    def __init__(self, content, cb, prefix_complete, homogenous):
        self.content = content
        self.cb = cb
        self.prefix_complete = prefix_complete
        self.homogenous = homogenous

        self.widgets = []
        self.labels = []
        self.hilite = -1

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('delete_event', self.destroy)
        self.window.connect('focus-out-event', self.destroy)

        self.window.set_decorated(False)
        self.window.set_keep_above(True)
        self.window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DIALOG)
        self.window.set_title('pager-desktop-list')
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.set_can_focus(True)

        self.window.modify_bg(gtk.STATE_NORMAL,
                              gtk.gdk.color_parse(config.prompt_border_color))

        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, 
                     gtk.gdk.color_parse(config.prompt_bgcolor))
        eb.set_border_width(config.prompt_border_width)
        self.window.add(eb)

        self.box = gtk.VBox(False, 0)
        eb.add(self.box)

        self.entry = gtk.Entry()
        self.entry.connect('key_press_event', self.quit_on_esc)
        self.entry.connect('key_release_event', self.completion)
        self.entry.connect('key_press_event', self.do_hilite)
        self.entry.connect('activate', self.do_result_fun)
        self.entry.set_has_frame(False)
        self.entry.set_inner_border(gtk.Border(10, 10, 10, 10))
        self.entry.modify_font(pango.FontDescription(config.prompt_text_font))
        self.entry.modify_text(gtk.STATE_NORMAL, 
                               gtk.gdk.color_parse(config.prompt_text_color))
        self.entry.modify_base(gtk.STATE_NORMAL, 
                               gtk.gdk.color_parse(config.prompt_bgcolor))

        self.box.pack_start(self.entry, False, False, 0)
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, 
                     gtk.gdk.color_parse(config.prompt_border_color))
        eb.set_size_request(-1, config.prompt_border_width)
        self.box.pack_start(eb, False, False, 0)

        self.update_content()

        self.window.show_all()
        self.window.present()

        self.last_text = self.entry.get_text()

    def update_content(self):
        if self.widgets:
            for w in self.widgets:
                w.destroy()

        self.widgets = []
        self.labels = []
        self.hilite = None

        text = self.entry.get_text().lower()
        ml = config.prompt_max_length

        def autocomp(item):
            if self.prefix_complete:
                return item.lower().startswith(text)
            else:
                return item.lower().find(text) != -1

        for header in sorted(self.content.keys()):
            lst = filter(lambda (fst, snd): autocomp(fst),
                         self.content[header])

            if not lst:
                continue

            if isinstance(header, basestring):
                hlabel = gtk.Label()
                hlabel.set_markup(config.prompt_header_markup % header[:ml])
                hlabel.set_alignment(0, 0.5)
                self.widgets.append(hlabel)
                self.box.pack_start(hlabel, True, True, 2)

            for i in xrange(0, len(lst), 2):
                item1, data1 = lst[i]
                item2 = data2 = None
                if i + 1 < len(lst):
                    item2, data2 = lst[i + 1]

                label1 = gtk.Label()
                label1.set_markup(config.prompt_item_markup % item1[:ml])
                label1.set_alignment(0, 0.5)
                self.labels.append((label1, item1, data1))

                if item2 is None:
                    label1.set_padding(10, 0)
                    self.box.pack_start(label1, True, True, 10)
                    self.widgets.append(label1)
                else:
                    label2 = gtk.Label()
                    label2.set_markup(config.prompt_item_markup % item2[:ml])
                    label2.set_alignment(0, 0.5)
                    self.labels.append((label2, item2, data2))

                    cols = gtk.HBox(self.homogenous, 0)
                    cols.pack_start(label1, True, True, 10)

                    
                    eb = gtk.EventBox()
                    eb.modify_bg(gtk.STATE_NORMAL, 
                                 gtk.gdk.color_parse(
                                     config.prompt_border_color))
                    eb.set_size_request(config.prompt_border_width, -1)
                    cols.pack_start(eb, False, False, 0)

                    cols.pack_start(label2, True, True, 10)
                    self.box.pack_start(cols, True, True, 10)
                    self.widgets.append(cols)

        self.box.show_all()

    def destroy(self, *args, **kwargs):
        self.window.destroy()

    def quit_on_esc(self, widget, e):
        if len(e.string) > 0 and ord(e.string[0]) == 27:
            self.destroy()
        return False

    def do_hilite(self, widget, e):
        if e.hardware_keycode == 23:
            if e.state & gtk.gdk.SHIFT_MASK:
                if self.hilite is None:
                    self.hilite = len(self.labels) - 1
                else:
                    self.hilite = (self.hilite - 1) % len(self.labels)
            else:
                if self.hilite is None:
                    self.hilite = 0
                else:
                    self.hilite = (self.hilite + 1) % len(self.labels)

            ml = config.prompt_max_length
            for i, (lab, content, data) in enumerate(self.labels):
                if self.hilite == i:
                    lab.set_markup(config.prompt_hilite_markup % content[:ml])
                else:
                    lab.set_markup(config.prompt_item_markup % content[:ml])

    def completion(self, widget, e):
        if e.hardware_keycode != 23 and self.last_text != self.entry.get_text():
            self.update_content()
        self.last_text = self.entry.get_text()

    def do_result_fun(self, *args, **kwargs):
        if self.hilite != -1:
            _, _, content = self.labels[self.hilite]
        elif len(self.labels) == 1:
            _, _, content = self.labels[0]
        else:
            content = self.entry.get_text()

        if not content:
            return

        self.cb(content)
        self.destroy()


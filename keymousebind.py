from functools import partial

import xpybutil.ewmh as ewmh

import prompt

keybinds = {}

# KEY BINDING CONFIGURATION
##########################

# Here's where using Python for configuration really shines. You can 
# completely control the way desktops are switched. For example, the current
# 'set_desktop' function takes either a desktop index or a prefix of a desktop
# name. One can use the keybindings '<Control><Alt>a' - '<Control><Alt>z'
# to switch between desktops starting with the corresponding letter.

# Also, I've stolen the "prompt" concept from Xmonad. If you know Python,
# check out 'prompt.py'; it should be fairly straight-forward to create your
# own prompts. If you want to modify it further (i.e., its appearance), you'll
# need to have some experiece with pygtk.
# There really aren't any docs, so please feel free to email me
# jamslam@gmail.com, or use https://bbs.archlinux.org/viewtopic.php?id=124331

def init():
    shifts = ['exclam', 'at', 'numbersign', 'dollar', 'percent', 'asciicircum',
              'ampersand', 'asterisk', 'parenleft']
    for i in xrange(1, 10):
        keybinds['<Alt>%d' % i] = mk_set_desktop(str(i))
        keybinds['<Alt>%s' % shifts[i - 1]] = mk_set_activewin_desktop(str(i))
    for c in xrange(ord('a'), ord('z') + 1):
        keybinds['<Control><Alt>%s' % chr(c)] = mk_set_desktop(chr(c))
        keybinds['<Super><Alt>%s' % chr(c)] = mk_set_activewin_desktop(chr(c))

    keybinds['<Super>BackSpace'] = remove_empty_current_desktop

    keybinds['<Super>Return'] = mk_prompt_desktop()
    keybinds['<Super><Shift>Return'] = prompt_set_activewin_desktop
    
    keybinds['<Super><Alt>space'] = mk_prompt_all_windows()
    keybinds['<Super>space'] = mk_prompt_windows()


# MOUSE BINDING CONFIGURATION
#############################

# There isn't much here yet, other than when one clicks on mini-desktop picture.
def desktop_clicked(desktop):
    ewmh.request_current_desktop_checked(desktop.desk).check()


# HELPER FUNCTIONS
##################

def mk_set_desktop(i_or_name):
    return partial(set_desktop, str(i_or_name))

def mk_set_activewin_desktop(i_or_name):
    return partial(set_activewin_desktop, str(i_or_name))

def mk_prompt_desktop():
    return partial(prompt.desktops, set_or_add_desktop)

def mk_prompt_windows():
    return partial(prompt.windows, goto_window, prefix_complete=False,
                   homogenous=False, current_desk=True)

def mk_prompt_all_windows():
    return partial(prompt.windows, goto_window)

def set_desktop(i_or_name):
    nextdesk = get_desk(i_or_name)
    if nextdesk is not None:
        ewmh.request_current_desktop_checked(nextdesk).check()

def set_activewin_desktop(i_or_name):
    awin = ewmh.get_active_window().reply()

    set_win_desktop(i_or_name, awin)

def set_win_desktop(i_or_name, win):
    nextdesk = get_desk(i_or_name)
    if None not in (nextdesk, win):
        ewmh.request_wm_desktop_checked(win, nextdesk, 2).check()

def set_or_add_desktop(name):
    names = ewmh.get_desktop_names().reply()

    if name not in names:
        names.append(name)
        ewmh.set_desktop_names_checked(names).check()
        num_desks = ewmh.get_number_of_desktops().reply()
        ewmh.request_number_of_desktops_checked(num_desks + 1).check()

    ewmh.request_current_desktop_checked(names.index(name)).check()

def prompt_set_activewin_desktop():
    activewin = ewmh.get_active_window().reply()
    def fun(name):
        names = ewmh.get_desktop_names().reply()
        if name not in names:
            names.append(name)
            ewmh.set_desktop_names_checked(names).check()
            num_desks = ewmh.get_number_of_desktops().reply()
            ewmh.request_number_of_desktops_checked(num_desks + 1).check()

        ewmh.request_wm_desktop_checked(activewin, 
                                        names.index(name), 2).check()

    prompt.desktops(fun)

def remove_empty_current_desktop():
    # This isn't as straight-forward as decrementing _NET_NUMBER_OF_DESKTOPS.
    # We need to make sure we remove the right name, too.
    # AND only do it if there are no clients on this desktop.
    clients = ewmh.get_client_list().reply()
    cur = ewmh.get_current_desktop().reply()
    for c in clients:
        if ewmh.get_wm_desktop(c).reply() == cur:
            return

    names = ewmh.get_desktop_names().reply()
    if cur < len(names):
        names.pop(cur)
        ewmh.set_desktop_names_checked(names).check()

    # Subtract one from every client's desktop above the current one
    for c in clients:
        cdesk = ewmh.get_wm_desktop(c).reply()
        if cdesk > cur and cdesk != 0xffffffff:
            ewmh.set_wm_desktop_checked(c, cdesk - 1).check()

    ndesks = ewmh.get_number_of_desktops().reply()
    ewmh.request_number_of_desktops_checked(ndesks - 1).check()

def goto_window(win_name_or_id):
    wid = win_name_or_id
    if isinstance(wid, basestring):
        clients = ewmh.get_client_list().reply()
        for c in clients:
            if wid == ewmh.get_wm_name(c).reply():
                wid = c
                break

    if isinstance(wid, int):
        wdesk = ewmh.get_wm_desktop(wid).reply()
        if wdesk not in ewmh.get_visible_desktops().reply():
            ewmh.request_current_desktop_checked(wdesk).check()
        ewmh.request_active_window_checked(wid, source=2).check()

def get_desk(i_or_name):
    if isinstance(i_or_name, int):
        return i_or_name

    assert isinstance(i_or_name, basestring)
    
    nextdesk = None
    names = ewmh.get_desktop_names().reply()
    ci = ewmh.get_current_desktop().reply()
    visibles = ewmh.get_visible_desktops().reply()

    cname = names[ci] if ci < len(names) else ''
    fnames = names[:]

    if visibles:
        not_cur_or_vis = lambda (i, nm): i not in visibles or i == ci
        fnames = [nm for i, nm in filter(not_cur_or_vis, enumerate(fnames))]

    fnames = filter(lambda n: n.lower().startswith(i_or_name.lower()), fnames)
    fnames = sorted(fnames)

    if cname in fnames:
        posInPrefix = (fnames.index(cname) + 1) % len(fnames)
        nextdesk = names.index(fnames[posInPrefix])
    elif len(fnames):
        nextdesk = names.index(fnames[0])

    return nextdesk

init()


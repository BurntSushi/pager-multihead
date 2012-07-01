import re
import sys

from xpybutil import conn, root
import xpybutil.ewmh as ewmh


# GENERAL CONFIGURATION
#######################

# A list of desktop names that will be made available.
# If this list is empty, the desktop setup (i.e., the names and number of them)
# will not be modified on startup.
desktops = []
#desktops = ['1', '2', '3', '4', '5', '6']
# desktops = map(str, range(1, 10)) 

# Whether to show desktop names below each mini-desktop picture
# Note that the behavior of pager-multihead when both 'show_desk_names' and
# 'show_desk_views' are False is undefined.
show_desk_names = True

# Whether to show desktop viewports (a mini-desktop picture of windows).
# Note that the behavior of pager-multihead when both 'show_desk_names' and
# 'show_desk_views' are False is undefined.
show_desk_views = True

# The geometry of the pager window
# These should be relative to the *root* window---beware of dead area!
x = 0
y = 0
width = 700
height = 100

# Most of the following options tend to be a forgone conclusion; particularly
# if 'dock' is true. Nevertheless, modify to your heart's content.

# Make it a dock
# If you're using openbox-multihead, it's dangerous to turn this off
dock = True

# Set struts
struts = True

# Make it available on all desktops
# This must be true if struts is true (otherwise struts won't work)
sticky = True

# Keep above
above = True


# THEME CONFIGURATION - PAGER
#############################

# The background color of the pager window
pager_bgcolor = '#ffffff'

# The spacing (in pixles) between each mini-desktop picture
desk_margin = 5

# The color of a mini-desktop picture border
desk_bordercolor = '#000000'

# Color of a window that is active
active_window_color = '#5f5fad'

# Color of a window that is not active
window_color = '#d67575'

# Color of a border drawn around a window
window_border_color = '#000000'

# Three different categories of desktops:
# A desktop that is active.
# A desktop that is visible but not active.
# A desktop that is not visible.
active_desk_color = '#b2b2b2'
visible_desk_color = '#dbdbdb'
hidden_desk_color = '#dbdbdb'

# Set different themes for the desktop name.
# The categorical breakdown is the same as above.
# '%s' is the desktop name.
# Use the Pango Markup Language
# http://www.pygtk.org/docs/pygtk/pango-markup-language.html
active_name_markup = re.sub('\s+', ' ', '''
    <span 
        font_desc="DejaVu Sans Mono 11" 
        weight="bold"
        foreground="#00bb00"
    >
    %s
    </span>
''')
visible_name_markup = re.sub('\s+', ' ', '''
    <span 
        font_desc="DejaVu Sans Mono 11" 
        weight="bold"
        foreground="#bb0000"
    >
    %s
    </span>
''')
hidden_name_markup = re.sub('\s+', ' ', '''
    <span 
        font_desc="DejaVu Sans Mono 11" 
        foreground="#000000"
    >
    %s
    </span>
''')

# This is applied on *any* desktop (regardless of whether it's active,
# visible or hidden) that is empty, in addition to the markup matching its
# active/visible/hidden state.
empty_name_markup = '%s'

# This is applied on *any* desktop (regardless of whether it's active,
# visible or hidden) that is NOT empty, in addition to the markup matching its
# active/visible/hidden state.
notempty_name_markup = re.sub('\s+', ' ', '''
    <span 
        weight="bold"
    >%s</span>
''')


# THEME CONFIGURATION - PROMPT
##############################

# The general background color of the prompt window
prompt_bgcolor = '#4c4c4c'

# The text color of the input prompt
prompt_text_color = '#ffffff'

# The font of the input prompt
prompt_text_font = 'DejaVu Sans Mono 11'

# The border color of the prompt
prompt_border_color = '#8e8e8e'

# The border width of the prompt
prompt_border_width = 5

# The maximum length of any item
# If this is too high, the prompt window is liable to get unwieldy
prompt_max_length = 50

# The text to use for showing an item string in a prompt window.
# '%s' is the item name.
# Use the Pango Markup Language
# http://www.pygtk.org/docs/pygtk/pango-markup-language.html
prompt_item_markup = re.sub('\s+', ' ', '''
    <span
        font_desc="DejaVu Sans Mono 11"
        foreground="#ffffff"
    >
    %s
    </span>
''')

prompt_hilite_markup = re.sub('\s+', ' ', '''
    <span
        font_desc="DejaVu Sans Mono 11"
        foreground="#535353"
        background="#ffffff"
    >
    %s
    </span>
''')

prompt_header_markup = re.sub('\s+', ' ', '''
    <span
        font_desc="DejaVu Sans Mono 12"
        weight="bold"
        foreground="#ffffff"
    >
    %s
    </span>
''')


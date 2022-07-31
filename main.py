import os
import xdnmb.globals
import xdnmb.action

from prompt_toolkit import Application
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.styles import Style

xdnmb.action.loadForumGroup()

Application(
    layout=xdnmb.globals.layout,
    key_bindings=xdnmb.globals.keyBinding,
    full_screen=True,
    style=Style.from_dict({
        'nav': 'bg:#ffffff #cc0000',
        'nav button': '#0077dd',
        'nav button.focused': 'bg:#bbeeff',
        'divide': 'bg:#ffffee #000000',
        'content': 'bg:#ffffee #800000',
        'content-rev': 'bg:#800000 #ffffee',
        'title': '#cc1105 bold',
        'name': '#117743 bold',
        'sage': '#d85030',
        'tips': '#707070',
        'admin': '#ff0000',
        'name-admin': '#444444',
        'name-po': '#2d7091',
        'reply': 'bg:#f0e0d6',
        'reference': '#789922',
        'content button': '#0077dd',
        'content button.focused': 'bg:#bbeeff',
        'form-label': 'bg:#eeaa88',
        'form-textarea': 'bg:#ffffff',
    }),
    color_depth=ColorDepth.DEPTH_1_BIT if xdnmb.globals.config['Config'].getboolean('Monochrome') else ColorDepth.DEPTH_24_BIT,
).run()

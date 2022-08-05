import datetime
import functools
import os
import re
import secrets
import subprocess
import tempfile
import typing
import warnings
import xdnmb.api
import xdnmb.globals
import xdnmb.model

from bs4 import BeautifulSoup
from bs4.element import Tag
from bs4 import MarkupResemblesLocatorWarning

from prompt_toolkit.completion import Completer
from prompt_toolkit.layout import Float
from prompt_toolkit.layout import HSplit
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Dialog
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import TextArea

warnings.filterwarnings('ignore', category=MarkupResemblesLocatorWarning, module='bs4')

def stripHTML(text: str|BeautifulSoup|Tag) -> str:
    if isinstance(text, (BeautifulSoup, Tag)):
        return re.sub(r'^\s+|\s+$', '\n', text.text.replace('\r', ''), flags=re.M)
    text = re.sub(r'<br ?/?>\r?\n?', '\n', text)
    text = re.sub(r'^\s+|\s+$', '\n', text, flags=re.M)
    return BeautifulSoup(text, features='lxml').text

def parseThreadTime(text: str) -> datetime.datetime:
    return datetime.datetime.strptime(
        re.sub(r'\([日一二三四五六]\)', ' ', text),
        '%Y-%m-%d %H:%M:%S',
    )

def floatAlert(title: str, body: str):
    b = Button('确定')
    d = Float(Dialog(
        title=title,
        body=Label(body),
        buttons=(
            b,
        ),
    ))
    b.handler = functools.partial(lambda e: (
        xdnmb.globals.container.floats.remove(e) or
        xdnmb.globals.layout.focus(xdnmb.globals.container)
    ), d)
    xdnmb.globals.container.floats.append(d)
    xdnmb.globals.layout.focus(b.window)

def floatAlertExceptionCatch(func: typing.Callable):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            floatAlert('错误', f'{type(ex).__name__}: {ex}')
    return wrapper

def floatPrompt(title: str, body: str, callback: typing.Callable[[str], None], completer: Completer|None = None):
    t = TextArea(
        multiline=False,
        completer=completer,
    )
    b0 = Button('确定')
    b1 = Button('取消')
    d = Float(Dialog(
        title=title,
        body=HSplit((
            Label(text=body, dont_extend_height=True),
            t,
        ), width=24),
        buttons=(
            b0,
            b1,
        ),
    ))
    b0.handler = functools.partial(lambda e: (
        xdnmb.globals.container.floats.remove(e) or
        xdnmb.globals.layout.focus(xdnmb.globals.container) or
        callback(t.text)
    ), d)
    b1.handler = functools.partial(lambda e: (
        xdnmb.globals.container.floats.remove(e) or
        xdnmb.globals.layout.focus(xdnmb.globals.container)
    ), d)
    xdnmb.globals.container.floats.append(d)
    xdnmb.globals.layout.focus(t.window)

def focusToButton(focusFrom: xdnmb.model.ButtonType|None, focusTo: xdnmb.model.ButtonType) -> bool:
    focused = xdnmb.globals.layout.current_window
    try:
        if focusFrom is None or focusFrom == getattr(focused, 'buttonType', xdnmb.model.ButtonType.Dummy):
            xdnmb.globals.layout.focus(next(
                button
                for button in xdnmb.globals.layout.get_visible_focusable_windows()
                if getattr(button, 'buttonType', xdnmb.model.ButtonType.Dummy) == focusTo
            ))
            return True
    except StopIteration:
        pass
    return False

# Chafa: Terminal Graphics for the 21st Century
# https://hpjansson.org/chafa/

@functools.cache
def detectChafa() -> bool:
    try:
        p = subprocess.Popen(
            ('chafa', '--version'),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return p.wait() == 0
    except FileNotFoundError:
        return False

@functools.lru_cache(1024)
def loadChafaImage(url: str, width: int, height: int) -> str:
    temp = os.path.join(tempfile.gettempdir(), secrets.token_urlsafe(12))
    cmd = (
        'chafa',
        '--duration', str(0),
        '--optimize', str(9),
        '--size', f'{width}x{height}',
        '--work', str(9),
        temp if os.name == 'nt' else '-',
    )
    with xdnmb.api.session.get(url, stream=True, timeout=3) as r:
        if os.name == 'nt':
            with open(temp, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
        with subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL if os.name == 'nt' else subprocess.PIPE,
            stdout=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
        ) as p:
            if os.name != 'nt':
                for chunk in r.iter_content(8192):
                    p.stdin.write(chunk)
                p.stdin.close()
            result = p.stdout.read()
        if os.name == 'nt':
            os.remove(temp)
    if p.returncode:
        raise subprocess.CalledProcessError(p.returncode, cmd)
    return result.decode('utf-8').split('\033[6A')[0].replace('\r', '').strip()

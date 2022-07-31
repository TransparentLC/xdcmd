import dataclasses
import datetime
import enum
import functools
import html
import math
import re
import xdnmb.action

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.containers import VSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.containers import WindowAlign
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Label

class ButtonType(enum.IntEnum):
    Dummy = 0
    Forum = enum.auto()
    Thread = enum.auto()
    Reply = enum.auto()
    Reference = enum.auto()

@dataclasses.dataclass(unsafe_hash=True)
class Forum:
    fid: int
    sort: int
    name: str
    notice: str
    threadCount: int

    @functools.cache
    def __pt_container__(self) -> Container:
        b = Button(
            text=f'  {self.name}',
            left_symbol='',
            right_symbol='',
            width=0,
            handler=functools.partial(xdnmb.action.loadForum, self)
        )
        b.window.align = WindowAlign.LEFT
        setattr(b.window, 'buttonType', ButtonType.Forum)
        return b.window

@dataclasses.dataclass(unsafe_hash=True)
class Timeline:
    fid: int
    name: str
    notice: str
    maxPage: int

    @functools.cache
    def __pt_container__(self) -> Container:
        b = Button(
            text=f'  {self.name}',
            left_symbol='',
            right_symbol='',
            width=0,
            handler=functools.partial(xdnmb.action.loadForum, self)
        )
        b.window.align = WindowAlign.LEFT
        setattr(b.window, 'buttonType', ButtonType.Forum)
        return b.window

@dataclasses.dataclass(unsafe_hash=True)
class ForumGroup:
    gid: int
    sort: int
    name: int
    forums: tuple[Forum|Timeline, ...]

    @functools.cache
    def __pt_container__(self) -> Container:
        children: list[Container] = [
            Window(Label(self.name).formatted_text_control),
        ]
        for forum in self.forums:
            children.append(forum.__pt_container__())
        return HSplit(tuple(children))

@dataclasses.dataclass(unsafe_hash=True)
class Reply:
    tid: int
    img: str|None
    imgThumb: str|None
    now: datetime.datetime
    userHash: str
    name: str
    title: str
    content: str
    admin: bool
    isPo: bool

    @functools.cache
    def __pt_container__(self) -> Container:
        import xdnmb.globals
        import xdnmb.util

        b = Button(
            text=f'No.{self.tid}',
            left_symbol='',
            right_symbol='',
            width=len(f'No.{self.tid}'),
        )
        b.window.align = WindowAlign.LEFT
        setattr(b.window, 'buttonType', ButtonType.Reply)
        children: list[Container] = [
            VSplit((
                Label(
                    HTML(
                        '<title>{0}</title> <name>{1}</name> {2} ID:' + (
                            '<admin>{3}</admin><name-admin>小会员</name-admin>'
                            if self.admin else
                            '{3}'
                        ) + (
                            '<name-po>(PO主)</name-po> '
                            if self.isPo else
                            ' '
                        )
                    ).format(
                        self.title,
                        self.name,
                        self.now.strftime('%Y-%m-%d %H:%M:%S'),
                        self.userHash,
                    ),
                    dont_extend_width=True,
                ),
                b,
                Label(' '),
            )),
        ]
        children.append(Label(HTML(re.sub(
            r'(&gt;&gt;No\.\d+)',
            lambda m: f'<reference>{m.group(1)}</reference>',
            html.escape(self.content),
        ))))
        if self.img:
            if (
                self.imgThumb
                and xdnmb.globals.config['Config'].getboolean('ImagePreview')
                and not xdnmb.globals.config['Config'].getboolean('Monochrome')
                and xdnmb.util.detectChafa()
            ):
                try:
                    children.append(Label(ANSI(xdnmb.util.loadChafaImage(
                        self.imgThumb,
                        xdnmb.globals.config['Config'].getint('ImagePreviewWidth'),
                        xdnmb.globals.config['Config'].getint('ImagePreviewHeight'),
                    ))))
                except Exception as ex:
                    children.append(Label(f'⚠️ 图片加载失败：{type(ex).__name__}: {ex}', style='class:tips'))
            children.append(Label(f'🖼️ 附加图片：{self.img}', style='class:tips'))
        return HSplit(tuple(children), style='class:content class:reply')

@dataclasses.dataclass(unsafe_hash=True)
class Thread(Reply):
    forum: Forum
    sage: bool
    replyCount: int
    replies: tuple[Reply, ...]|None = None

    @property
    def maxPage(self) -> int:
        return math.ceil(self.replyCount / 19) if self.replyCount else 1

    @functools.cache
    def __pt_container__(self) -> Container:
        import xdnmb.globals
        import xdnmb.util

        b = Button(
            text=f'No.{self.tid}',
            left_symbol='',
            right_symbol='',
            width=len(f'No.{self.tid}'),
            handler=functools.partial(xdnmb.action.loadThread, self),
        )
        b.window.align = WindowAlign.LEFT
        setattr(b.window, 'buttonType', ButtonType.Thread)
        children: list[Container] = [
            VSplit((
                Label(
                    HTML(
                        '<title>{0}</title> <name>{1}</name> {2} ID:' + (
                            '<admin>{3}</admin><name-admin>小会员</name-admin> '
                            if self.admin else
                            '{3} '
                        )
                    ).format(
                        self.title,
                        self.name,
                        self.now.strftime('%Y-%m-%d %H:%M:%S'),
                        self.userHash,
                    ),
                    dont_extend_width=True,
                ),
                b,
                Label(f' [{self.forum.name}]'),
            )),
        ]
        if self.sage:
            children.append(Label('👎 SAGE', style='class:sage'))
        children.append(Label(HTML(re.sub(
            r'(&gt;&gt;No\.\d+)',
            lambda m: f'<reference>{m.group(1)}</reference>',
            html.escape(self.content),
        ))))
        if self.img:
            if (
                self.imgThumb
                and xdnmb.globals.config['Config'].getboolean('ImagePreview')
                and not xdnmb.globals.config['Config'].getboolean('Monochrome')
                and xdnmb.util.detectChafa()
            ):
                try:
                    children.append(Label(ANSI(xdnmb.util.loadChafaImage(
                        self.imgThumb,
                        xdnmb.globals.config['Config'].getint('ImagePreviewWidth'),
                        xdnmb.globals.config['Config'].getint('ImagePreviewHeight'),
                    ))))
                except Exception as ex:
                    children.append(Label(f'⚠️ 图片加载失败：{type(ex).__name__}: {ex}', style='class:tips'))
            children.append(Label(f'🖼️ 附加图片：{self.img}', style='class:tips'))
        children.append(Label(f'➕ 回应共有 {self.replyCount} 篇', style='class:tips'))
        children.append(Window(height=1))
        if self.replies:
            for reply in self.replies:
                children.append(reply.__pt_container__())
                children.append(Window(height=1))
        return HSplit(tuple(children), style='class:content')

import configparser
import functools
import os
import sys
import xdnmb.action
import xdnmb.api
import xdnmb.model
import xdnmb.util

from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next
from prompt_toolkit.key_binding.bindings.focus import focus_previous
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout import Float
from prompt_toolkit.layout import FloatContainer
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout import ScrollablePane
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.containers import VSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.containers import WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.widgets import Button
from prompt_toolkit.widgets import Checkbox
from prompt_toolkit.widgets import Dialog
from prompt_toolkit.widgets import Frame
from prompt_toolkit.widgets import Label
from prompt_toolkit.widgets import TextArea

BASE_PATH: str = os.path.realpath(sys._MEIPASS if hasattr(sys, '_MEIPASS') else '')
APP_PATH = os.path.dirname(os.path.realpath(sys.executable if hasattr(sys, '_MEIPASS') else sys.argv[0]))

config = configparser.RawConfigParser()
config['DEFAULT'] = {
    'CDNPath': '',
    'Cookie': '',
    'Monochrome': False,
    'ImagePreview': True,
    'ImagePreviewWidth': 24,
    'ImagePreviewHeight': 6,
}
config['Config'] = {}
config.read(os.path.join(APP_PATH, 'config.ini'))
if config['Config'].get('CDNPath'):
    xdnmb.api.CDN_PATH = config['Config'].get('CDNPath')
else:
    xdnmb.api.CDN_PATH = xdnmb.api.getCDNPath()
if config['Config'].get('Cookie'):
    xdnmb.api.session.cookies.set('userhash', config['Config'].get('Cookie'))

EMOTICON = (
    "|∀ﾟ", "(´ﾟДﾟ`)", "(;´Д`)", "(｀･ω･)", "(=ﾟωﾟ)=", "| ω・´)", "|-` )", "|д` )",
    "|ー` )", "|∀` )", "(つд⊂)", "(ﾟДﾟ≡ﾟДﾟ)", "(＾o＾)ﾉ", "(|||ﾟДﾟ)", "( ﾟ∀ﾟ)", "( ´∀`)",
    "(*´∀`)", "(*ﾟ∇ﾟ)", "(*ﾟーﾟ)", "(　ﾟ 3ﾟ)", "( ´ー`)", "( ・_ゝ・)", "( ´_ゝ`)", "(*´д`)",
    "(・ー・)", "(・∀・)", "(ゝ∀･)", "(〃∀〃)", "(*ﾟ∀ﾟ*)", "( ﾟ∀。)", "( `д´)", "(`ε´ )",
    "(`ヮ´ )", "σ`∀´)", " ﾟ∀ﾟ)σ", "ﾟ ∀ﾟ)ノ", "(╬ﾟдﾟ)", "(|||ﾟдﾟ)", "( ﾟдﾟ)", "Σ( ﾟдﾟ)",
    "( ;ﾟдﾟ)", "( ;´д`)", "(　д ) ﾟ ﾟ", "( ☉д⊙)", "(((　ﾟдﾟ)))", "( ` ・´)", "( ´д`)", "( -д-)",
    "(>д<)", "･ﾟ( ﾉд`ﾟ)", "( TдT)", "(￣∇￣)", "(￣3￣)", "(￣ｰ￣)", "(￣ . ￣)", "(￣皿￣)",
    "(￣艸￣)", "(￣︿￣)", "(￣︶￣)", "ヾ(´ωﾟ｀)", "(*´ω`*)", "(・ω・)", "( ´・ω)", "(｀・ω)",
    "(´・ω・`)", "(`・ω・´)", "( `_っ´)", "( `ー´)", "( ´_っ`)", "( ´ρ`)", "( ﾟωﾟ)", "(oﾟωﾟo)",
    "(　^ω^)", "(｡◕∀◕｡)", "/( ◕‿‿◕ )\\", "ヾ(´ε`ヾ)", "(ノﾟ∀ﾟ)ノ", "(σﾟдﾟ)σ", "(σﾟ∀ﾟ)σ", "|дﾟ )",
    "┃電柱┃", "ﾟ(つд`ﾟ)", "ﾟÅﾟ )　", "⊂彡☆))д`)", "⊂彡☆))д´)", "⊂彡☆))∀`)", "(´∀((☆ミつ", "･ﾟ( ﾉヮ´ )",
    "(ﾉ)`ω´(ヾ)", "ᕕ( ᐛ )ᕗ", "(　ˇωˇ)", "( ｣ﾟДﾟ)｣＜", "( ›´ω`‹ )", "(;´ヮ`)7", "(`ゥ´ )", "(`ᝫ´ )",
    "( ᑭ`д´)ᓀ))д´)ᑫ", "σ( ᑒ )",
    "(`ヮ´ )σ`∀´) ﾟ∀ﾟ)σ",
    "( ﾉд`ﾟ);´д`) ´_ゝ`)",
    "Σ( ﾟдﾟ)´ﾟДﾟ)　ﾟдﾟ)))",
    "( ﾟ∀。)∀。)∀。)",
    "(　ˇωˇ )◕∀◕｡)^ω^)",
)
EMOTICON_MULTILINE = {
    'F5欧拉': "　σ　σ\nσ(　´ρ`)σ[F5]\n　σ　σ",
    '白羊': "╭◜◝ ͡ ◜◝ J J\n(　　　　 `д´) 　“咩！”\n╰◟д ◞ ͜ ◟д◞",
    '举高高': "　　　　_∧＿∧_ 　　　　\n            ((∀｀/ 　) 　　\n　       /⌒　　 ／ 　　\n         /(__ノ＼_ノ 　　\n          (_ノ ||| 举高高~~\n　∧＿∧　∧＿∧\n (( ・∀・ ))・∀・) )\n `＼　　 ∧ 　　ノ\n　/　｜/　　｜\n（＿ノ＿)_ノL＿)",
    '举糕糕': "举糕糕~\n　　☆☆☆☆☆☆☆☆\n 　╭┻┻┻┻┻┻┻┻╮\n 　┃╱╲╱╲╱╲╱╲┃\n ╭┻━━━━━━━━┻╮\n ┃╱╲╱╲╱╲╱╲╱╲┃\n ┗━━━━━━━━━━┛\n 　　　∧＿∧　∧＿∧\n　　(( ・∀・ ))・∀・) )\n 　　`＼　　 ∧ 　　ノ\n　　　/　　｜/　　｜\n 　　（＿ノ＿)_ノL＿)",
    '大嘘': "吁~~~~　　rnm，退钱！\n 　　　/　　　/\n(　ﾟ 3ﾟ) `ー´) `д´) `д´)",
    '催更喵': "　　　　　／＞　　フ\n　　　　　|  　_　 _ l 我是一只催更的\n　 　　　／` ミ＿xノ 喵喵酱\n　　 　 /　　　 　 | gkdgkd\n　　　 /　 ヽ　　 ﾉ\n　 　 │　　|　|　|\n　／￣|　　 |　|　|\n　| (￣ヽ＿_ヽ_)__)\n　＼二つ ",
    '巴拉巴拉': "    ∧＿∧\n （｡･ω･｡)つ━☆・*。\n ⊂　　 ノ 　　　・゜+.\n　しーＪ　　　°。+ *´¨)\n　　　 　　.· ´¸.·*´¨) ¸.·*¨)\n　　　　　　　 　(¸.·´ (¸.·’*",
}

forumGroups: list[xdnmb.model.ForumGroup] = []
forums: list[xdnmb.model.Forum] = []
forum: xdnmb.model.Forum = None
forumPage: int = None
forumThreads: list[xdnmb.model.Thread] = []
thread: xdnmb.model.Thread = None
threadPage: int = None
showReplyForm = False

homepageLabel = Label(text=(
    '\n'
    '久等了，欢迎回来\n'
    '\n'
    '|耶|\n'
    '|▒▒|\n'
    '|复|\n'
    '|活|\n'
    '|了|\n'
    '\n'
    '“人，是会思考的芦苇。” ——帕斯卡，《思想录》\n'
    '“开放包容 理性客观 有事说事 就事论事 顺猴者昌 逆猴者亡”\n'
    '免责声明：本站无法保证用户张贴内容的可靠性，投资有风险，健康问题请遵医嘱。\n'
    '\n'
    'X岛匿名版命令行客户端 XDCMD by TransparentLC\n'
    'https://github.com/TransparentLC/xdcmd\n'
), align=WindowAlign.CENTER)
forumBottomButton = Button('按 PgUp/PgDn 翻页')

@xdnmb.util.floatAlertExceptionCatch
def postThread():
    content = replyContentTextarea.text
    for alias, emoticon in EMOTICON_MULTILINE.items():
        content = content.replace(f'${alias}$', emoticon)
    if not content:
        return
    xdnmb.api.postThread(
        thread or forum,
        replyNameTextarea.text,
        replyTitleTextarea.text,
        content,
        replyImageTextarea.text,
        replyWaterCheckbox.checked,
    )
    global showReplyForm
    showReplyForm = False
    xdnmb.util.floatAlert('', '发表成功')

replyNameTextarea = TextArea(multiline=False)
replyTitleTextarea = TextArea(multiline=False)
replyContentTextarea = TextArea(
    multiline=True,
    height=8,
    completer=WordCompleter(
        (
            *EMOTICON,
            *(f'${e}$' for e in EMOTICON_MULTILINE),
            "接☆龙☆大☆成☆功", "[h][/h]", "[n,m]", ">>No.", "　",
        ),
        ignore_case=True,
        meta_dict={
            "(　^ω^)": '阴阳酱',
            "(　ˇωˇ)": '安详阴阳酱',
            "(｡◕∀◕｡)": '小殇君',
            "( ﾟ∀。)": '弱智酱',
            "( ・_ゝ・)": '忧郁傻卵',
            "(ノﾟ∀ﾟ)ノ": '举高高',
            "( ´ρ`)": '口水酱',
            "⊂彡☆))д`)": '左打脸',
            "⊂彡☆))д´)": '左打脸',
            "⊂彡☆))∀`)": '左打脸',
            "(´∀((☆ミつ": '右打脸',
            "ᕕ( ᐛ )ᕗ": '嗨呀',
            "σ( ᑒ )": '喂我',
            "(`ヮ´ )σ`∀´) ﾟ∀ﾟ)σ": '齐齐蛤尔',
            "( ﾉд`ﾟ);´д`) ´_ゝ`)": '呼伦悲尔',
            "Σ( ﾟдﾟ)´ﾟДﾟ)　ﾟдﾟ)))": '愕尔多厮',
            "( ﾟ∀。)∀。)∀。)": '智利',
            "(　ˇωˇ )◕∀◕｡)^ω^)": '阴山山脉',
            **{f'${e}$': '大型颜文字' for e in EMOTICON_MULTILINE},
            "[h][/h]": '防剧透',
            "[n,m]": '骰子',
            ">>No.": '引用',
            "　": '全角空格',
        },
    ),
)
replyImageTextarea = TextArea(multiline=False, completer=PathCompleter())
replyWaterCheckbox = Checkbox('水印')
replySendButton = Button('发送', handler=postThread)
for textarea in (
    replyNameTextarea,
    replyTitleTextarea,
    replyContentTextarea,
    replyImageTextarea,
):
    textarea.window.style = functools.partial(
        lambda w: 'class:text-area class:form-textarea' +
        (' bg:#dddddd' if get_app().layout.current_window == w else ''),
        textarea.window,
    )

def forumGroupControlContainer() -> Container:
    return HSplit(
        forumGroups if forumGroups else tuple(),
        width=20,
        style='class:nav',
    )

def forumContentControlContainer() -> Container:
    if showReplyForm:
        children = (
            VSplit((
                Label(text='名称', width=8, style='class:form-label'),
                replyNameTextarea,
            )),
            VSplit((
                Label(text='标题', width=8, style='class:form-label'),
                replyTitleTextarea,
            )),
            VSplit((
                Label(text='正文' + '\n' * 7, width=8, style='class:form-label'),
                replyContentTextarea,
            )),
            VSplit((
                Label(text='附加图片\n', width=8, style='class:form-label'),
                HSplit((
                    replyImageTextarea,
                    replyWaterCheckbox,
                )),
            )),
            replySendButton,
            Label((
                '* 按 Tab 和 Shift+Tab 来将光标指向文本框或发送按钮。\n'
                '* 按 Alt+N 返回版面/串。\n'
                '* 在“正文”中可以使用自动补全输入颜文字，大型颜文字会以“$颜文字名称$”的形式表示，使用时请另起一行，在发送时会被替换为实际的颜文字。\n'
                '* 在“附加图片”处输入的是本地的图片路径，同样可以使用自动补全。\n'
            )),
        )
    elif not forum:
        children = (
            homepageLabel,
        )
    elif not thread:
        children = (
            *forumThreads,
            forumBottomButton.window,
        )
    else:
        children = (
            thread,
            forumBottomButton.window,
        )
    return HSplit(
        children,
        style='class:content',
        width=get_app().renderer.output.get_size().columns - 23,
    )

def titleControlContainer() -> Container:
    title = 'X岛匿名版'
    if thread and threadPage:
        title += f' - {thread.forum.name} - No.{thread.tid} - 第 {threadPage}/{thread.maxPage} 页'
        if showReplyForm:
            title += ' - 回复'
    elif forum and forumPage:
        title += f' - {forum.name} - 第 {forumPage} 页'
        if showReplyForm:
            title += ' - 发串'
    else:
        title += ' - 写作绅士，读作丧尸'
    return Window(content=FormattedTextControl(title), height=1)

titleControl = DynamicContainer(titleControlContainer)
forumGroupControl = ScrollablePane(DynamicContainer(forumGroupControlContainer))
forumContentControl = ScrollablePane(DynamicContainer(forumContentControlContainer))

container = FloatContainer(
    HSplit((
        Frame(DynamicContainer(titleControlContainer), style='class:content'),
        VSplit((
            forumGroupControl,
            Window(width=1, char='|', style='class:divide'),
            forumContentControl,
        )),
        Window(height=1, char='-', style='class:divide'),
        VSplit(tuple(
            Label(text=HTML('<content-rev>[{0}]</content-rev>{1}').format(k, d), style='class:content')
            for k, d in (
                ('Alt+E', '退出'),
                ('↑/↓', '选择版面/串'),
                ('Enter', '查看版面/串'),
                ('PgUp/PgDn', '翻页'),
                ('Alt+P', '串内跳页'),
            )
        )),
        VSplit(tuple(
            Label(text=HTML('<content-rev>[{0}]</content-rev>{1}').format(k, d), style='class:content')
            for k, d in (
                ('Alt+Q', '从串返回版面'),
                ('Alt+N', '发串/回复'),
                ('Alt+M', '查看版规'),
                ('Alt+L', '查看引用'),
                ('Tab', '将光标指向版面/串/悬浮窗按钮'),
            )
        )),
    )),
    [
        Float(
            xcursor=True,
            ycursor=True,
            content=CompletionsMenu(max_height=8, scroll_offset=1),
        )
    ],
)
layout = Layout(container)

keyBinding = KeyBindings()
keyBinding.add('up', filter=Condition(lambda: not (len(container.floats) > 1 or showReplyForm)))(focus_previous)
keyBinding.add('down', filter=Condition(lambda: not (len(container.floats) > 1 or showReplyForm)))(focus_next)

@keyBinding.add('escape', 'e')
def _(e: KeyPressEvent):
    for k in config['Config']:
        config['Config'][k] = config['Config'].get(k)
    config['DEFAULT'] = {}
    with open(os.path.join(APP_PATH, 'config.ini'), 'w', encoding='utf-8') as f:
        config.write(f)
    get_app().exit()

@keyBinding.add('pageup')
def _(e: KeyPressEvent):
    if not forum:
        return
    elif not thread:
        global forumPage
        if forumPage <= 1:
            xdnmb.util.floatAlert('别翻啦', f'这已经是第 1 页了⊂彡☆))∀`)')
            return
        xdnmb.action.loadForum(forum, forumPage - 1)
        xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Thread)
    else:
        global threadPage
        if threadPage <= 1:
            xdnmb.util.floatAlert('别翻啦', f'这已经是第 1 页了⊂彡☆))∀`)')
            return
        xdnmb.action.loadThread(thread, threadPage - 1)
        xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)
    xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

@keyBinding.add('pagedown')
def _(e: KeyPressEvent):
    if not forum:
        return
    elif not thread:
        if (isinstance(forum, xdnmb.model.Timeline)) and forumPage >= forum.maxPage:
            xdnmb.util.floatAlert('我真的……一条都没有了', f'你已经翻到了时间线“{forum.name}”的底部（页数上限为 {forum.maxPage} 页）')
            return
        xdnmb.action.loadForum(forum, forumPage + 1)
    else:
        if threadPage >= thread.maxPage:
            xdnmb.util.floatAlert('我真的……一条都没有了', f'你已经翻到了这个串的最后一页')
            return
        xdnmb.action.loadThread(thread, threadPage + 1)

keyBinding.add('tab', filter=Condition(lambda: len(container.floats) > 1 or showReplyForm))(focus_next)
keyBinding.add('s-tab', filter=Condition(lambda: len(container.floats) > 1 or showReplyForm))(focus_previous)

@keyBinding.add('tab', filter=Condition(lambda: not (len(container.floats) > 1 or showReplyForm)))
def _(e: KeyPressEvent):
    for focusFrom, focusTo in (
        (xdnmb.model.ButtonType.Forum, xdnmb.model.ButtonType.Thread),
        (xdnmb.model.ButtonType.Thread, xdnmb.model.ButtonType.Forum),
        (xdnmb.model.ButtonType.Reply, xdnmb.model.ButtonType.Thread),
    ):
        if xdnmb.util.focusToButton(focusFrom, focusTo):
            return

@keyBinding.add('escape', 'm')
def _(e: KeyPressEvent):
    if not forum:
        return
    xdnmb.util.floatAlert(
        f'{thread.forum.name if thread else forum.name}版规',
        thread.forum.notice if thread else forum.notice,
    )

@keyBinding.add('escape', 'q')
def _(e: KeyPressEvent):
    global thread
    if not thread or len(container.floats) > 1 or showReplyForm:
        return
    thread = None
    forumContentControl.vertical_scroll = 0
    xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

@keyBinding.add('escape', 'p')
def _(e: KeyPressEvent):
    if not thread:
        return
    def callback(s: str):
        try:
            s = int(s)
            if s < 1 or s > thread.maxPage:
                raise ValueError
        except ValueError:
            return
        xdnmb.action.loadThread(thread, s)
    xdnmb.util.floatPrompt('跳转页面', f'请输入页数（共 {thread.maxPage} 页）：', callback)

@keyBinding.add('escape', 'l')
def _(e: KeyPressEvent):
    @xdnmb.util.floatAlertExceptionCatch
    def callback(s: str):
        try:
            s = int(s)
        except ValueError:
            return
        b = Button('确定')
        d = Float(Dialog(
            title='查看引用',
            body=xdnmb.api.getReference(s),
            buttons=(
                b,
            ),
        ))
        b.handler = functools.partial(lambda e: (
            container.floats.remove(e) or
            layout.focus(container)
        ), d)
        container.floats.append(d)
        layout.focus(b.window)

    xdnmb.util.floatPrompt('查看引用', f'请输入串号：\n（不需要输入 No.）', callback)

@keyBinding.add('escape', 'n')
def _(e: KeyPressEvent):
    if (not forum or isinstance(forum, xdnmb.model.Timeline)) and not thread:
        return
    global showReplyForm
    showReplyForm = not showReplyForm
    forumContentControl.vertical_scroll = 0
    if showReplyForm:
        replyNameTextarea.text = ''
        replyTitleTextarea.text = ''
        replyContentTextarea.text = ''
        replyImageTextarea.text = ''
        layout.focus(replyNameTextarea)
    else:
        xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

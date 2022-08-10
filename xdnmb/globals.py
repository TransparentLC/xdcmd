import argparse
import configparser
import functools
import os
import sys
import typing
import xdnmb.action
import xdnmb.api
import xdnmb.model
import xdnmb.util

from concurrent.futures import ThreadPoolExecutor
from prompt_toolkit.application.current import get_app
from prompt_toolkit.completion import Completion
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
XDG_CONFIG_PATH = os.path.join(
    os.environ.get('XDG_CONFIG_HOME', os.path.expanduser(os.path.join('~', '.config'))),
    'xdcmd',
    'config.ini',
)

argparser = argparse.ArgumentParser(
    description='X岛匿名版（https://nmbxd.com/）命令行客户端',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
argparser.add_argument(
    '--config', '-c',
    dest='config',
    default=XDG_CONFIG_PATH,
    help='配置文件路径',
)
args = argparser.parse_args()

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
configLoaded = False
for p in (
    args.config,
    os.path.join(APP_PATH, 'config.ini'),
):
    if os.path.exists(p):
        config.read(p)
        configLoaded = True
        break
if not configLoaded:
    for k in config['Config']:
        config['Config'][k] = config['Config'].get(k)
    config['DEFAULT'] = {}
    os.makedirs(os.path.split(XDG_CONFIG_PATH)[0], exist_ok=True)
    with open(XDG_CONFIG_PATH, 'w', encoding='utf-8') as f:
        config.write(f)

if config['Config'].get('CDNPath'):
    xdnmb.api.CDN_PATH = config['Config'].get('CDNPath')
else:
    xdnmb.api.CDN_PATH = xdnmb.api.getCDNPath()
if config['Config'].get('Cookie'):
    xdnmb.api.session.cookies.set('userhash', config['Config'].get('Cookie'))

class PathCompleterWithWords(PathCompleter):
    def __init__(
        self,
        only_directories: bool = False,
        get_paths: typing.Callable[[], list[str]]|None = None,
        file_filter: typing.Callable[[str], bool]|None = None,
        min_input_len: int = 0,
        expanduser: bool = False,
        words: list[str] = [],
        meta_dict: dict[str, str] = {},
    ) -> None:
        self.words = words
        self.meta_dict = meta_dict
        super().__init__(only_directories, get_paths, file_filter, min_input_len, expanduser)

    def get_completions(
        self,
        document,
        complete_event,
    ):
        for w in self.words:
            wordBeforeCursor = document.get_word_before_cursor()
            if w.startswith(wordBeforeCursor):
                yield Completion(
                    text=w,
                    start_position=-len(wordBeforeCursor),
                    display_meta=self.meta_dict.get(w, ''),
                )
        for c in super().get_completions(document, complete_event):
            yield c

EMOTICON = (
    "|∀ﾟ", "(´ﾟДﾟ`)", "(;´Д`)", "(｀･ω･)", "(=ﾟωﾟ)=", "| ω・´)", "|-` )", "|д` )",
    "|ー` )", "|∀` )", "(つд⊂)", "(ﾟДﾟ≡ﾟДﾟ)", "(＾o＾)ﾉ", "(|||ﾟДﾟ)", "( ﾟ∀ﾟ)", "( ´∀`)",
    "(*´∀`)", "(*ﾟ∇ﾟ)", "(*ﾟーﾟ)", "(　ﾟ 3ﾟ)", "( ´ー`)", "( ・_ゝ・)", "( ´_ゝ`)", "(*´д`)",
    "(・ー・)", "(・∀・)", "(ゝ∀･)", "(〃∀〃)", "(*ﾟ∀ﾟ*)", "( ﾟ∀。)", "( `д´)", "(`ε´ )",
    "(`ヮ´ )", "σ`∀´)", " ﾟ∀ﾟ)σ", "ﾟ ∀ﾟ)ノ", "(╬ﾟдﾟ)", "( ﾟдﾟ)", "Σ( ﾟдﾟ)", "( ;ﾟдﾟ)",
    "( ;´д`)", "(　д ) ﾟ ﾟ", "( ☉д⊙)", "(((　ﾟдﾟ)))", "( ` ・´)", "( ´д`)", "( -д-)", "(>д<)",
    "･ﾟ( ﾉд`ﾟ)", "( TдT)", "(￣∇￣)", "(￣3￣)", "(￣ｰ￣)", "(￣ . ￣)", "(￣皿￣)", "(￣艸￣)",
    "(￣︿￣)", "(￣︶￣)", "ヾ(´ωﾟ｀)", "(*´ω`*)", "(・ω・)", "( ´・ω)", "(｀・ω)", "(´・ω・`)",
    "(`・ω・´)", "( `_っ´)", "( `ー´)", "( ´_っ`)", "( ´ρ`)", "( ﾟωﾟ)", "(oﾟωﾟo)", "(　^ω^)",
    "(｡◕∀◕｡)", "/( ◕‿‿◕ )\\", "ヾ(´ε`ヾ)", "(ノﾟ∀ﾟ)ノ", "(σﾟдﾟ)σ", "(σﾟ∀ﾟ)σ", "|дﾟ )", "┃電柱┃",
    "ﾟ(つд`ﾟ)", "ﾟÅﾟ )", "⊂彡☆))д`)", "⊂彡☆))д´)", "⊂彡☆))∀`)", "(´∀((☆ミつ", "･ﾟ( ﾉヮ´ )", "(ﾉ)`ω´(ヾ)",
    "ᕕ( ᐛ )ᕗ", "(　ˇωˇ)", "( ｣ﾟДﾟ)｣＜", "( ›´ω`‹ )", "(;´ヮ`)7", "(`ゥ´ )", "(`ᝫ´ )",
    "( ᑭ`д´)ᓀ))д´)ᑫ", "σ( ᑒ )", "( ´_ゝ`)旦",
    "(`ヮ´ )σ`∀´) ﾟ∀ﾟ)σ",
    "( ﾉд`ﾟ);´д`) ´_ゝ`)",
    "Σ( ﾟдﾟ)´ﾟДﾟ)　ﾟдﾟ)))",
    "( ﾟ∀。)∀。)∀。)",
    "(　ˇωˇ )◕∀◕｡)^ω^)",
)
EMOTICON_MULTILINE = {
    'F5欧拉': (
        "　σ　σ\n"
        "σ(　´ρ`)σ[F5]\n"
        "　σ　σ"
    ),
    '白羊': (
        "╭◜◝ ͡ ◜◝ J J\n"
        "(　　　　 `д´) 　“咩！”\n"
        "╰◟д ◞ ͜ ◟д◞"
    ),
    '举高高': (
        "　　　　_∧＿∧_ 　　　　\n"
        "            ((∀｀/ 　) 　　\n"
        "　       /⌒　　 ／ 　　\n"
        "         /(__ノ＼_ノ 　　\n"
        "          (_ノ ||| 举高高~~\n"
        "　∧＿∧　∧＿∧\n"
        " (( ・∀・ ))・∀・) )\n"
        " `＼　　 ∧ 　　ノ\n"
        "　/　｜/　　｜\n"
        "（＿ノ＿)_ノL＿)"
    ),
    '举糕糕': (
        "举糕糕~\n"
        "　　☆☆☆☆☆☆☆☆\n"
        " 　╭┻┻┻┻┻┻┻┻╮\n"
        " 　┃╱╲╱╲╱╲╱╲┃\n"
        " ╭┻━━━━━━━━┻╮\n"
        " ┃╱╲╱╲╱╲╱╲╱╲┃\n"
        " ┗━━━━━━━━━━┛\n"
        " 　　　∧＿∧　∧＿∧\n"
        "　　(( ・∀・ ))・∀・) )\n"
        " 　　`＼　　 ∧ 　　ノ\n"
        "　　　/　　｜/　　｜\n"
        " 　　（＿ノ＿)_ノL＿)"
    ),
    '大嘘': (
        "吁~~~~　　rnm，退钱！\n"
        " 　　　/　　　/\n"
        "(　ﾟ 3ﾟ) `ー´) `д´) `д´)"
    ),
    '催更喵': (
        "　　　　　／＞　　フ\n"
        "　　　　　|  　_　 _ l 我是一只催更的\n"
        "　 　　　／` ミ＿xノ 喵喵酱\n"
        "　　 　 /　　　 　 | gkdgkd\n"
        "　　　 /　 ヽ　　 ﾉ\n"
        "　 　 │　　|　|　|\n"
        "　／￣|　　 |　|　|\n"
        "　| (￣ヽ＿_ヽ_)__)\n"
        "　＼二つ "
    ),
    '巴拉巴拉': (
        "    ∧＿∧\n"
        " （｡･ω･｡)つ━☆・*。\n"
        " ⊂　　 ノ 　　　・゜+.\n"
        "　しーＪ　　　°。+ *´¨)\n"
        "　　　 　　.· ´¸.·*´¨) ¸.·*¨)\n"
        "　　　　　　　 　(¸.·´ (¸.·’*"
    ),
}

replyCompleterWords = (
    *EMOTICON,
    *(f'${e}$' for e in EMOTICON_MULTILINE),
    "接☆龙☆大☆成☆功", "[h][/h]", "[n,m]", "　", ">>No.",
)
replyCompleterMeta = {
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
    "　": '全角空格',
    ">>No.": '引用',
}

# 芦苇娘表情包（黑白106p+彩色105p）存档：
# https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/files.txt
# https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/files.txt

STICKERS: dict[str, str] = {f'${k}$': v for k, v in ({
    '芦苇娘:|∀ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/5Twsz4Sf.gif',
    '芦苇娘:(´ﾟДﾟ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/6piF6jJk.gif',
    '芦苇娘:(;´Д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/eUlXZWzc.gif',
    '芦苇娘:| ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/uOtrjJFV.gif',
    '芦苇娘:|-` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/mHHUux1K.gif',
    '芦苇娘:|д` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/H2KpBuay.gif',
    '芦苇娘:|ー` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/5aBUXcND.gif',
    '芦苇娘:|∀` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/AoOQmvNT.gif',
    '芦苇娘:(つд⊂)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/eAiYJdan.gif',
    '芦苇娘:(ﾟДﾟ≡ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/ejUL6m4H.gif',
    '芦苇娘:(|||ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/190zHXKL.gif',
    '芦苇娘:( ﾟ∀ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/WD2DHX1g.gif',
    '芦苇娘:(*´∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/1MlufTch.gif',
    '芦苇娘:(*ﾟ∇ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/FjJzUVDh.gif',
    '芦苇娘:(*ﾟーﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/4tEBZrTt.gif',
    '芦苇娘:(　ﾟ 3ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/kDPenBUd.gif',
    '芦苇娘:( ´ー`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/GScF6yCr.gif',
    '芦苇娘:( ・_ゝ・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/CwCTmRcU.gif',
    '芦苇娘:( ´_ゝ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/5XEjKdOS.gif',
    '芦苇娘:(・ー・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/gtL4cQiM.gif',
    '芦苇娘:(ゝ∀･)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/oMPDGKQO.gif',
    '芦苇娘:(〃∀〃)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/x3CIaoFS.gif',
    '芦苇娘:(*ﾟ∀ﾟ*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/n5pSoXK3.gif',
    '芦苇娘:( ﾟ∀。)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/mQypwgTk.gif',
    '芦苇娘:(`ε´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/YA20ZhgU.gif',
    '芦苇娘:(`ヮ´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/nXvplw3h.gif',
    '芦苇娘:σ`∀´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/BHp8pu2L.gif',
    '芦苇娘:ﾟ ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/cLCF62kQ.gif',
    '芦苇娘:(╬ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/H177FUBQ.gif',
    '芦苇娘:Σ( ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/XAw0V4LD.gif',
    '芦苇娘:(　д ) ﾟ ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/poqMCugl.gif',
    '芦苇娘:( ☉д⊙)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/08KpAqGw.gif',
    '芦苇娘:( -д-)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/d21IWTR5.gif',
    '芦苇娘:(>д<)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/C6XM7qHL.gif',
    '芦苇娘:･ﾟ( ﾉд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/aaW8st7G.gif',
    '芦苇娘:( TдT)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/Jwy6ulXn.gif',
    '芦苇娘:(￣∇￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/gAgCVK94.gif',
    '芦苇娘:(￣3￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/HkTgjCLz.gif',
    '芦苇娘:(￣ｰ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/xiH9pDDy.gif',
    '芦苇娘:(￣ . ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/JjJOb1s5.gif',
    '芦苇娘:(￣皿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/wqQfI113.gif',
    '芦苇娘:(￣艸￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/3o1ZYxAQ.gif',
    '芦苇娘:(￣︿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/rEncLo3C.gif',
    '芦苇娘:(￣︶￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/VEbeKRwz.gif',
    '芦苇娘:ヾ(´ωﾟ｀)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/R9KPPg8M.gif',
    '芦苇娘:(*´ω`*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/HhVqZGjz.gif',
    '芦苇娘:(・ω・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/ug2XqbxO.gif',
    '芦苇娘:(´・ω・`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/ZcEbjiYt.gif',
    '芦苇娘:(`・ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/NuDPEOOD.gif',
    '芦苇娘:( `_っ´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/N5y5nnAN.gif',
    '芦苇娘:( `ー´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/OJQAXG8O.gif',
    '芦苇娘:( ´_っ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/LarNL0Ij.gif',
    '芦苇娘:( ´ρ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/OUINwI0x.gif',
    '芦苇娘:( ﾟωﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/dXufYvhj.gif',
    '芦苇娘:(oﾟωﾟo)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/Sv5bkXw5.gif',
    '芦苇娘:(　^ω^)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/XcsP9dMc.gif',
    '芦苇娘:(｡◕∀◕｡)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/EsuxA0t6.gif',
    '芦苇娘:/( ◕‿‿◕ )\\': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/3yCG3E3J.gif',
    '芦苇娘:ヾ(´ε`ヾ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/XbWktsiq.gif',
    '芦苇娘:(ノﾟ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/Om5NYmeJ.gif',
    '芦苇娘:(σﾟдﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/bBp66X4W.gif',
    '芦苇娘:(σﾟ∀ﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/sD10uAQP.gif',
    '芦苇娘:|дﾟ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/4oy7jXiA.gif',
    '芦苇娘:ﾟ(つд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/7w0Eh3S8.gif',
    '芦苇娘:⊂彡☆))д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/cK4PoeNp.gif',
    '芦苇娘:⊂彡☆))д´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/rZHDS3BH.gif',
    '芦苇娘:⊂彡☆))∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/HAlF8pVo.gif',
    '芦苇娘:(´∀((☆ミつ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/edyYIcdY.gif',
    '芦苇娘:( ´_ゝ`)旦': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/DCob631l.gif',
    '彩色芦苇娘:|∀ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/4ePl1Evw.gif',
    '彩色芦苇娘:(´ﾟДﾟ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/EhRC5ezT.gif',
    '彩色芦苇娘:(;´Д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/YLTEyWxa.gif',
    '彩色芦苇娘:| ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/u8rj7Ux3.gif',
    '彩色芦苇娘:|-` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/wb1TPMu3.gif',
    '彩色芦苇娘:|д` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/GiuGF0Cy.gif',
    '彩色芦苇娘:|ー` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/kBGIOpeE.gif',
    '彩色芦苇娘:|∀` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/eGD1syYn.gif',
    '彩色芦苇娘:(つд⊂)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/wtp0s7xe.gif',
    '彩色芦苇娘:(ﾟДﾟ≡ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/IdVxFmLt.gif',
    '彩色芦苇娘:(|||ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/bF4xSebx.gif',
    '彩色芦苇娘:( ﾟ∀ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/sN5XRVD1.gif',
    '彩色芦苇娘:(*´∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/3YLL7Dhs.gif',
    '彩色芦苇娘:(*ﾟ∇ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/fCWaBmSc.gif',
    '彩色芦苇娘:(*ﾟーﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/QUWXlw2S.gif',
    '彩色芦苇娘:(　ﾟ 3ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/XotCElQp.gif',
    '彩色芦苇娘:( ´ー`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/jhdwMQHl.gif',
    '彩色芦苇娘:( ・_ゝ・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/iEXtKo0z.gif',
    '彩色芦苇娘:( ´_ゝ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ngLxxN7S.gif',
    '彩色芦苇娘:(・ー・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/S1fe8C4G.gif',
    '彩色芦苇娘:(ゝ∀･)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/YLhozhFL.gif',
    '彩色芦苇娘:(〃∀〃)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/VWZm4Bqr.gif',
    '彩色芦苇娘:(*ﾟ∀ﾟ*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/GkD3JLJr.gif',
    '彩色芦苇娘:( ﾟ∀。)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/qG2OMOEU.gif',
    '彩色芦苇娘:(`ε´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/utfJYr0p.gif',
    '彩色芦苇娘:(`ヮ´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/7AUxqrAx.gif',
    '彩色芦苇娘:σ`∀´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/OXkAnCsC.gif',
    '彩色芦苇娘:ﾟ ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/sWTi5aUP.gif',
    '彩色芦苇娘:(╬ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/0Uz48Mos.gif',
    '彩色芦苇娘:Σ( ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/IA1e3zbN.gif',
    '彩色芦苇娘:(　д ) ﾟ ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/gLzaZLip.gif',
    '彩色芦苇娘:( ☉д⊙)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/jbFfWTrR.gif',
    '彩色芦苇娘:( -д-)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/sZtHHLcs.gif',
    '彩色芦苇娘:(>д<)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/llsTSZsy.gif',
    '彩色芦苇娘:･ﾟ( ﾉд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/TGmgFLHS.gif',
    '彩色芦苇娘:( TдT)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/OCqLSnj2.gif',
    '彩色芦苇娘:(￣∇￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/cjiFPvt4.gif',
    '彩色芦苇娘:(￣3￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/e4HMkN9r.gif',
    '彩色芦苇娘:(￣ｰ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/8KCA3i7z.gif',
    '彩色芦苇娘:(￣ . ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/Pu2X1wPw.gif',
    '彩色芦苇娘:(￣皿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/H7QixXk9.gif',
    '彩色芦苇娘:(￣艸￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/G0qV2FB3.gif',
    '彩色芦苇娘:(￣︿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/faCJvnQ0.gif',
    '彩色芦苇娘:(￣︶￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/MmxBuBYi.gif',
    '彩色芦苇娘:ヾ(´ωﾟ｀)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/2Nm8GqLb.gif',
    '彩色芦苇娘:(*´ω`*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/C5cz5ytQ.gif',
    '彩色芦苇娘:(・ω・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/PudoQ12m.gif',
    '彩色芦苇娘:(´・ω・`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/xPtbJ3mX.gif',
    '彩色芦苇娘:(`・ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/o8t76ygC.gif',
    '彩色芦苇娘:( `_っ´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/o8t76ygC.gif',
    '彩色芦苇娘:( `ー´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/zIbXJsRu.gif',
    '彩色芦苇娘:( ´_っ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/6vcm4fIt.gif',
    '彩色芦苇娘:( ´ρ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/G6jf40gb.gif',
    '彩色芦苇娘:( ﾟωﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ZPO8JOgr.gif',
    '彩色芦苇娘:(oﾟωﾟo)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/jXWmzbUX.gif',
    '彩色芦苇娘:(　^ω^)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/rZXUY6uU.gif',
    '彩色芦苇娘:(｡◕∀◕｡)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/6NAM56Bu.gif',
    '彩色芦苇娘:/( ◕‿‿◕ )\\': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/CgAXf91O.gif',
    '彩色芦苇娘:ヾ(´ε`ヾ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/K7mUhdiV.gif',
    '彩色芦苇娘:(ノﾟ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/x911Mciq.gif',
    '彩色芦苇娘:(σﾟдﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/gNpChvcx.gif',
    '彩色芦苇娘:(σﾟ∀ﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/WhOI12ut.gif',
    '彩色芦苇娘:|дﾟ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/gRNeoxTX.gif',
    '彩色芦苇娘:ﾟ(つд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/xIgW7ADh.gif',
    '彩色芦苇娘:⊂彡☆))д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/oZWQCcIU.gif',
    '彩色芦苇娘:⊂彡☆))д´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/13Tt1SBT.gif',
    '彩色芦苇娘:⊂彡☆))∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/OGzbwiQX.gif',
    '彩色芦苇娘:(´∀((☆ミつ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/WHuAbycB.gif',
    '彩色芦苇娘:( ´_ゝ`)旦': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/5i1sD4EH.gif',
}).items()}

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
    if not content and not replyImageTextarea.text:
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
)
replyImageTextarea = TextArea(
    multiline=False,
    completer=PathCompleterWithWords(words=[k for k in STICKERS]),
)
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

imagePreloadExecutor = ThreadPoolExecutor()

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
                '* 在“正文”中可以使用自动补全输入颜文字，大型颜文字会以“$颜文字名称$”的形式表示，'
                  '使用时请另起一行，在发送时会被替换为实际的颜文字。\n'
                '* 在“附加图片”中可以使用：\n'
                '  * 本地的图片路径，同样可以使用自动补全。\n'
                '  * 以 https:// 或 http:// 开头的在线图片 URL。\n'
                '  * 输入“$芦苇娘:...$”或“$彩色芦苇娘:...$”，可以发送与颜文字对应的芦苇娘表情包。'
                    '芦苇娘人物形象原作者为 ddzx1323，表情包由 Anime801 制作。\n'
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

    preload: list[xdnmb.model.Reply|xdnmb.model.Thread] = []
    for c in children:
        if (
            isinstance(c, xdnmb.model.Reply)
            and c.imagePreviewAvailable
            and not getattr(c, 'imagePreviewLoaded', None)
        ):
            preload.append(c)
            if isinstance(c, xdnmb.model.Thread) and c.replies:
                for r in c.replies:
                    if (
                        r.imagePreviewAvailable
                        and not getattr(r, 'imagePreviewLoaded', None)
                    ):
                        preload.append(r)
    preloadIter = imagePreloadExecutor.map(lambda c: c.imagePreviewLabel, preload)
    while True:
        try:
            next(preloadIter)
        except StopIteration:
            break
        except:
            pass

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
keyBinding.add('escape', 'e')(lambda e: get_app().exit())

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
            s = int(s.strip())
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
            s = int(s.strip())
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

    refw = set()
    refm = {}
    if thread:
        refw.update(thread.references)
        refm.update({str(k): f'被“{thread.summary(24)}”引用' for k in thread.references})
        for r in thread.replies:
            refw.update(r.references)
            refm.update({str(k): f'被“{r.summary(24)}”引用' for k in r.references})
    elif forum:
        for t in forumThreads:
            refw.update(t.references)
            refm.update({str(k): f'被“{t.summary(24)}”引用' for k in t.references})
    refw = list(refw)
    refw.sort()
    refw = list(str(x) for x in refw)

    xdnmb.util.floatPrompt(
        '查看引用',
        f'请输入串号：\n（不需要输入 No.）',
        callback,
        WordCompleter(refw, meta_dict=refm),
    )

@keyBinding.add('escape', 'n')
def _(e: KeyPressEvent):
    if (not forum or isinstance(forum, xdnmb.model.Timeline)) and not thread:
        return
    global showReplyForm
    showReplyForm = not showReplyForm
    forumContentControl.vertical_scroll = 0
    if showReplyForm:
        cw = list(replyCompleterWords)
        cm = replyCompleterMeta.copy()
        if thread:
            cw.append(f'>>No.{thread.tid}')
            cm[f'>>No.{thread.tid}'] = f'引用：“{thread.summary(24)}”'
            for r in thread.replies:
                cw.append(f'>>No.{r.tid}')
                cm[f'>>No.{r.tid}'] = f'引用：“{r.summary(24)}”'
        elif forum:
            for t in forumThreads:
                cw.append(f'>>No.{t.tid}')
                cm[f'>>No.{t.tid}'] = f'引用：“{t.summary(24)}”'

        replyContentTextarea.completer = WordCompleter(cw, meta_dict=cm)
        replyNameTextarea.text = ''
        replyTitleTextarea.text = ''
        replyContentTextarea.text = ''
        replyImageTextarea.text = ''
        layout.focus(replyContentTextarea)
    else:
        xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

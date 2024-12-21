import argparse
import configparser
import functools
import os
import platform
import re
import sqlite3
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
from prompt_toolkit.formatted_text import ANSI
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

try:
    from xdnmb.version import COMMIT_HASH
except ImportError:
    COMMIT_HASH = None

is_mac = platform.system() == "Darwin"

BASE_PATH: str = os.path.realpath(sys._MEIPASS if hasattr(sys, '_MEIPASS') else '')
APP_PATH = os.path.dirname(os.path.realpath(sys.executable if hasattr(sys, '_MEIPASS') else sys.argv[0]))
XDG_CONFIG_PATH = os.path.join(
    os.environ.get('XDG_CONFIG_HOME', os.path.expanduser(os.path.join('~', '.config'))),
    'xdcmd',
)
XDG_CACHE_PATH = os.path.join(
    os.environ.get('XDG_CACHE_HOME', os.path.expanduser(os.path.join('~', '.cache'))),
    'xdcmd',
)
os.makedirs(XDG_CONFIG_PATH, exist_ok=True)
os.makedirs(XDG_CACHE_PATH, exist_ok=True)
LRU_CACHE_DB = sqlite3.connect(os.path.join(XDG_CACHE_PATH, 'lru-cache.db'), isolation_level=None)
LRU_CACHE_DB.executescript(''.join(x.strip() for x in '''
PRAGMA journal_mode = wal;
CREATE TABLE IF NOT EXISTS "cache" (
    "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    "timestamp" DATE NOT NULL,
    "key" TEXT NOT NULL,
    "value" BLOB,
    CONSTRAINT "const_key" UNIQUE ("key")
);
CREATE UNIQUE INDEX IF NOT EXISTS "main"."idx_key"
ON "cache" (
    "key"
);
CREATE INDEX IF NOT EXISTS "main"."idx_timestamp"
ON "cache" (
    "timestamp"
);
'''.splitlines()))
LRU_CACHE_DB_CURSOR = LRU_CACHE_DB.cursor()

argparser = argparse.ArgumentParser(
    description='X岛匿名版（https://nmbxd.com/）命令行客户端',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
argparser.add_argument(
    '--config', '-c',
    dest='config',
    default=os.path.join(XDG_CONFIG_PATH, 'config.ini'),
    help='配置文件路径',
)
args = argparser.parse_args()

config = configparser.RawConfigParser()
config['DEFAULT'] = {
    'CDNPath': '',
    'Cookie': '',
    'FeedUUID': '',
    'Monochrome': False,
    'Simplify': False,
    'ImagePreview': True,
    'ImagePreviewWidth': 24,
    'ImagePreviewHeight': 6,
    'HideTips': False,
    'HideCookie': False,
    'PoOnly': False,
    'IgnoreNotice': False,
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
    with open(os.path.join(XDG_CONFIG_PATH, 'config.ini'), 'w', encoding='utf-8') as f:
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

STICKERS: dict[str, str] = {f'${k}$': v for k, v in ({
    '芦苇娘:|∀ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/OIo6BwF2.gif',
    '芦苇娘:(´ﾟДﾟ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/zJ2VBLNr.gif',
    '芦苇娘:(;´Д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/gYFd8hzO.gif',
    '芦苇娘:| ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/6yjpCfuW.gif',
    '芦苇娘:|-` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/jGZoNu72.gif',
    '芦苇娘:|д` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/H0XS4xKg.gif',
    '芦苇娘:|ー` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/Uw9rHGOM.gif',
    '芦苇娘:|∀` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/BcQGSOjM.gif',
    '芦苇娘:(つд⊂)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/mlVsqBqG.gif',
    '芦苇娘:(ﾟДﾟ≡ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/HJ03MHo7.gif',
    '芦苇娘:(|||ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/22QGSFRo.gif',
    '芦苇娘:( ﾟ∀ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/BuwYhhgs.gif',
    '芦苇娘:(*´∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/AFrDv7s1.gif',
    '芦苇娘:(*ﾟ∇ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/bvpjLOZs.gif',
    '芦苇娘:(*ﾟーﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/HUl3CrN5.gif',
    '芦苇娘:(　ﾟ 3ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/EzaVNiH1.gif',
    '芦苇娘:( ´ー`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/Q97m8faD.gif',
    '芦苇娘:( ・_ゝ・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/AnIMoln8.gif',
    '芦苇娘:( ´_ゝ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/lLomyjOe.gif',
    '芦苇娘:(・ー・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/S4z0FI2S.gif',
    '芦苇娘:(ゝ∀･)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/MerKB8wZ.gif',
    '芦苇娘:(〃∀〃)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/xLqG3YUe.gif',
    '芦苇娘:(*ﾟ∀ﾟ*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/RIa9WJfk.gif',
    '芦苇娘:( ﾟ∀。)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/zr0zupgR.gif',
    '芦苇娘:(`ε´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/PG5cetkD.gif',
    '芦苇娘:(`ヮ´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/WyjE0WCT.gif',
    '芦苇娘:σ`∀´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/5OTo7fS1.gif',
    '芦苇娘:ﾟ ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/mA0f0LI3.gif',
    '芦苇娘:(╬ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/5GKwNafU.gif',
    '芦苇娘:Σ( ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/kVQQbE5t.gif',
    '芦苇娘:(　д ) ﾟ ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/4e5D7Axr.gif',
    '芦苇娘:( ☉д⊙)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/WwyIGqTx.gif',
    '芦苇娘:( -д-)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/xJvuFQhc.gif',
    '芦苇娘:(>д<)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/3WwmfzNp.gif',
    '芦苇娘:･ﾟ( ﾉд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/BaRBhlLa.gif',
    '芦苇娘:( TдT)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/11pGQwG6.gif',
    '芦苇娘:(￣∇￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/jvM7ikeI.gif',
    '芦苇娘:(￣3￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/hH0BV4xu.gif',
    '芦苇娘:(￣ｰ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/3pbJubeh.gif',
    '芦苇娘:(￣ . ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/C9LlPBGL.gif',
    '芦苇娘:(￣皿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/NEMl1OUB.gif',
    '芦苇娘:(￣艸￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/Kx4pJFj5.gif',
    '芦苇娘:(￣︿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/moYSheAq.gif',
    '芦苇娘:(￣︶￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/bHwIYBpD.gif',
    '芦苇娘:ヾ(´ωﾟ｀)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/VcAH98BR.gif',
    '芦苇娘:(*´ω`*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/SuMIp2Lp.gif',
    '芦苇娘:(・ω・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/gY1xXZs2.gif',
    '芦苇娘:(´・ω・`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/ELXTd15O.gif',
    '芦苇娘:(`・ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/WQ7fyV1J.gif',
    '芦苇娘:( `_っ´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/jfllrm6p.gif',
    '芦苇娘:( `ー´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/2D3zKYve.gif',
    '芦苇娘:( ´_っ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/08S3E6no.gif',
    '芦苇娘:( ´ρ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/6MIHKQZf.gif',
    '芦苇娘:( ﾟωﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/UY6bVQb2.gif',
    '芦苇娘:(oﾟωﾟo)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/3rfuBwLB.gif',
    '芦苇娘:(　^ω^)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/cob7auXW.gif',
    '芦苇娘:(｡◕∀◕｡)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/ROqHB3qY.gif',
    '芦苇娘:/( ◕‿‿◕ )\\': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/jLAesszl.gif',
    '芦苇娘:ヾ(´ε`ヾ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/fOfRqaNd.gif',
    '芦苇娘:(ノﾟ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/TDRimesn.gif',
    '芦苇娘:(σﾟдﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/gCQdsfKT.gif',
    '芦苇娘:(σﾟ∀ﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/KolmeabD.gif',
    '芦苇娘:|дﾟ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/1RVVWlSn.gif',
    '芦苇娘:ﾟ(つд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/UAf8qoxT.gif',
    '芦苇娘:⊂彡☆))д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/D843xJel.gif',
    '芦苇娘:⊂彡☆))д´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/y3Rsvft0.gif',
    '芦苇娘:⊂彡☆))∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/sMoYPthz.gif',
    '芦苇娘:(´∀((☆ミつ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/PfP72zhe.gif',
    '芦苇娘:( ´_ゝ`)旦': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-mono/UI8ucctq.gif',
    '彩色芦苇娘:|∀ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/s7W4pZgl.gif',
    '彩色芦苇娘:(´ﾟДﾟ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/HaH5TJrb.gif',
    '彩色芦苇娘:(;´Д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/QSGll9g0.gif',
    '彩色芦苇娘:| ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/VHc7uegd.gif',
    '彩色芦苇娘:|-` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/11mUi3r4.gif',
    '彩色芦苇娘:|д` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/BZiRJfea.gif',
    '彩色芦苇娘:|ー` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/pOPXBwc6.gif',
    '彩色芦苇娘:|∀` )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/soGEp5N0.gif',
    '彩色芦苇娘:(つд⊂)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/cOA6Lgqv.gif',
    '彩色芦苇娘:(ﾟДﾟ≡ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/RoJ2TeJg.gif',
    '彩色芦苇娘:(|||ﾟДﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ZQacBv45.gif',
    '彩色芦苇娘:( ﾟ∀ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/2BXNZNNR.gif',
    '彩色芦苇娘:(*´∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/EETBvaOK.gif',
    '彩色芦苇娘:(*ﾟ∇ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/6Iusk4uH.gif',
    '彩色芦苇娘:(*ﾟーﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/uTiG7tZ4.gif',
    '彩色芦苇娘:(　ﾟ 3ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/1MrVZPzj.gif',
    '彩色芦苇娘:( ´ー`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/PdPWtMYc.gif',
    '彩色芦苇娘:( ・_ゝ・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/VSHQ4vJT.gif',
    '彩色芦苇娘:( ´_ゝ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/r97WoHzi.gif',
    '彩色芦苇娘:(・ー・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/wDDErF74.gif',
    '彩色芦苇娘:(ゝ∀･)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/MxLR10I2.gif',
    '彩色芦苇娘:(〃∀〃)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/FZAp110e.gif',
    '彩色芦苇娘:(*ﾟ∀ﾟ*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/Tnj6weib.gif',
    '彩色芦苇娘:( ﾟ∀。)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/5CPXsbmL.gif',
    '彩色芦苇娘:(`ε´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/POMfvbsB.gif',
    '彩色芦苇娘:(`ヮ´ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/8mpYg5Qm.gif',
    '彩色芦苇娘:σ`∀´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/AP9JMtjT.gif',
    '彩色芦苇娘:ﾟ ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/LQoKojWc.gif',
    '彩色芦苇娘:(╬ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/6l55x3F8.gif',
    '彩色芦苇娘:Σ( ﾟдﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ijWBOZlH.gif',
    '彩色芦苇娘:(　д ) ﾟ ﾟ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/S4WNNHsJ.gif',
    '彩色芦苇娘:( ☉д⊙)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/PpbfDSXf.gif',
    '彩色芦苇娘:( -д-)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/rbexiyQV.gif',
    '彩色芦苇娘:(>д<)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/Z4NZRIpS.gif',
    '彩色芦苇娘:･ﾟ( ﾉд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/Ao6Mr16X.gif',
    '彩色芦苇娘:( TдT)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/kl7l2qiQ.gif',
    '彩色芦苇娘:(￣∇￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/2tUvinGK.gif',
    '彩色芦苇娘:(￣3￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/m3s82FfY.gif',
    '彩色芦苇娘:(￣ｰ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/gVMJYp60.gif',
    '彩色芦苇娘:(￣ . ￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/1J3Z84s8.gif',
    '彩色芦苇娘:(￣皿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/bt4lMyCS.gif',
    '彩色芦苇娘:(￣艸￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/kJV4IT3L.gif',
    '彩色芦苇娘:(￣︿￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/hUr4UQxA.gif',
    '彩色芦苇娘:(￣︶￣)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/wH3kEtf2.gif',
    '彩色芦苇娘:ヾ(´ωﾟ｀)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ZcwTry9q.gif',
    '彩色芦苇娘:(*´ω`*)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/Z6ImUqF8.gif',
    '彩色芦苇娘:(・ω・)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/BNG4sUdH.gif',
    '彩色芦苇娘:(´・ω・`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/EFbgMTDa.gif',
    '彩色芦苇娘:(`・ω・´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ClQjgHGc.gif',
    '彩色芦苇娘:( `_っ´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ClQjgHGc.gif',
    '彩色芦苇娘:( `ー´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/PRedgOEQ.gif',
    '彩色芦苇娘:( ´_っ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/9hDdAA3g.gif',
    '彩色芦苇娘:( ´ρ`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/dOOlQQLZ.gif',
    '彩色芦苇娘:( ﾟωﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ckqyDVlF.gif',
    '彩色芦苇娘:(oﾟωﾟo)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/MUJv8znv.gif',
    '彩色芦苇娘:(　^ω^)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/8uMxFOhH.gif',
    '彩色芦苇娘:(｡◕∀◕｡)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/aZHObKln.gif',
    '彩色芦苇娘:/( ◕‿‿◕ )\\': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/OYuaNsP1.gif',
    '彩色芦苇娘:ヾ(´ε`ヾ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/XHSpVten.gif',
    '彩色芦苇娘:(ノﾟ∀ﾟ)ノ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/mX9PEo7y.gif',
    '彩色芦苇娘:(σﾟдﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/E9RbjSGk.gif',
    '彩色芦苇娘:(σﾟ∀ﾟ)σ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/QralakyG.gif',
    '彩色芦苇娘:|дﾟ )': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/ECyA3CR7.gif',
    '彩色芦苇娘:ﾟ(つд`ﾟ)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/rPVDUbBv.gif',
    '彩色芦苇娘:⊂彡☆))д`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/raBYZDQp.gif',
    '彩色芦苇娘:⊂彡☆))д´)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/vCFKVDLA.gif',
    '彩色芦苇娘:⊂彡☆))∀`)': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/aIUu872T.gif',
    '彩色芦苇娘:(´∀((☆ミつ': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/GlfdxYg3.gif',
    '彩色芦苇娘:( ´_ゝ`)旦': 'https://gcore.jsdelivr.net/gh/TransparentLC/xdcmd@reedgirl-colored/Bj7189TU.gif',
    '凉宫Tips娘:害羞': xdnmb.api.CDN_PATH + 'image/2022-08-21/6302122aac4a1.png',
    '凉宫Tips娘:怒': xdnmb.api.CDN_PATH + 'image/2022-08-21/6302126774399.png',
    '凉宫Tips娘:无语': xdnmb.api.CDN_PATH + 'image/2022-08-21/63021285e5e32.png',
    '凉宫Tips娘:kira': xdnmb.api.CDN_PATH + 'image/2022-08-21/6302129d68127.png',
    '凉宫Tips娘:尴尬': xdnmb.api.CDN_PATH + 'image/2022-08-21/630212b85961f.png',
    '凉宫Tips娘:晕': xdnmb.api.CDN_PATH + 'image/2022-08-21/630212d5c3b84.png',
    '凉宫Tips娘:汗': xdnmb.api.CDN_PATH + 'image/2022-08-21/630212ed9616d.png',
    '凉宫Tips娘:咋回事': xdnmb.api.CDN_PATH + 'image/2022-08-21/6302130783f36.png',
    '凉宫Tips娘:笑': xdnmb.api.CDN_PATH + 'image/2022-08-21/63021334de5bb.png',
    '凉宫Tips娘:弱智': xdnmb.api.CDN_PATH + 'image/2022-08-21/63021352a351f.png',
    '凉宫Tips娘:指责': xdnmb.api.CDN_PATH + 'image/2022-08-21/6302137130c0b.png',
    '凉宫Tips娘:右看': xdnmb.api.CDN_PATH + 'image/2022-08-21/6302138e9718c.png',
    '凉宫Tips娘:囧': xdnmb.api.CDN_PATH + 'image/2022-08-21/630213a9d0aa7.png',
    '凉宫Tips娘:小哭': xdnmb.api.CDN_PATH + 'image/2022-08-21/630213c95e30d.png',
    '凉宫Tips娘:大哭': xdnmb.api.CDN_PATH + 'image/2022-08-21/630212010be9d.png',
    '凉宫Tips娘:睡': xdnmb.api.CDN_PATH + 'image/2022-08-21/63021212bebe9.png',
}).items()}

forumGroups: list[xdnmb.model.ForumGroup] = []
forums: list[xdnmb.model.Forum] = []
forum: xdnmb.model.Forum = None
forumPage: int = None
forumThreads: list[xdnmb.model.Thread] = []
thread: xdnmb.model.Thread = None
threadPage: int = None
showReplyForm = False

homepageLabelText = '\n'.join((
    '',
    '久等了，欢迎回来',
    '',
    (
        '|耶|\n|▒▒|\n|复|\n|活|\n|了|'
        if config['Config'].getboolean('Monochrome') else
        '\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;200;74m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;200;74m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;238m▀\x1b[38;2;0;208;239m\x1b[48;2;178;237;248m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;200;74m\x1b[48;2;255;255;238m▀\x1b[38;2;255;200;74m\x1b[48;2;255;200;74m▀\x1b[38;2;255;200;74m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;178;237;248m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;200;74m\x1b[48;2;255;200;74m▀\x1b[38;2;255;255;238m\x1b[48;2;255;200;74m▀\x1b[38;2;255;200;74m\x1b[48;2;255;200;74m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[38;2;255;200;74m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;178;237;248m\x1b[48;2;255;255;255m▀\x1b[38;2;178;237;248m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;255m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;178;237;248m\x1b[48;2;255;255;255m▀\x1b[38;2;178;237;248m\x1b[48;2;255;255;255m▀\x1b[38;2;178;237;248m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;255m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;200;0;0m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;238;234m\x1b[48;2;255;238;234m▀\x1b[38;2;0;208;239m\x1b[48;2;255;0;0m▀\x1b[38;2;255;255;255m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;255;0;0m▀\x1b[38;2;200;0;0m\x1b[48;2;0;208;239m▀\x1b[38;2;200;0;0m\x1b[48;2;200;0;0m▀\x1b[38;2;200;0;0m\x1b[48;2;178;237;248m▀\x1b[38;2;0;208;239m\x1b[48;2;200;0;0m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;238;234m\x1b[48;2;255;210;199m▀\x1b[38;2;255;0;0m\x1b[48;2;255;0;0m▀\x1b[38;2;255;238;234m\x1b[48;2;255;238;234m▀\x1b[38;2;0;208;239m\x1b[48;2;255;238;234m▀\x1b[38;2;255;238;234m\x1b[48;2;255;238;234m▀\x1b[38;2;255;0;0m\x1b[48;2;255;0;0m▀\x1b[38;2;0;208;239m\x1b[48;2;255;210;199m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;200;0;0m\x1b[48;2;255;255;255m▀\x1b[38;2;200;0;0m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;210;199m\x1b[48;2;0;208;239m▀\x1b[38;2;255;238;234m\x1b[48;2;0;208;239m▀\x1b[38;2;255;238;234m\x1b[48;2;200;0;0m▀\x1b[38;2;255;238;234m\x1b[48;2;0;208;239m▀\x1b[38;2;255;210;199m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[0m\n\x1b[38;2;255;255;238m\x1b[48;2;255;255;238m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;255;255;255m▀\x1b[38;2;178;237;248m\x1b[48;2;178;237;248m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;200;0;0m\x1b[48;2;178;237;248m▀\x1b[38;2;39;147;199m\x1b[48;2;200;0;0m▀\x1b[38;2;200;0;0m\x1b[48;2;39;147;199m▀\x1b[38;2;178;237;248m\x1b[48;2;39;147;199m▀\x1b[38;2;39;147;199m\x1b[48;2;200;0;0m▀\x1b[38;2;200;0;0m\x1b[48;2;178;237;248m▀\x1b[38;2;0;208;239m\x1b[48;2;0;208;239m▀\x1b[38;2;255;255;255m\x1b[48;2;178;237;248m▀\x1b[38;2;178;237;248m\x1b[48;2;0;208;239m▀\x1b[38;2;0;208;239m\x1b[48;2;255;255;255m▀\x1b[38;2;255;255;238m\x1b[48;2;0;208;239m▀\x1b[0m'
    ),
    '',
    '“人，是会思考的芦苇。” ——帕斯卡，《思想录》',
    '“开放包容 理性客观 有事说事 就事论事 顺猴者昌 逆猴者亡”',
    '免责声明：本站无法保证用户张贴内容的可靠性，投资有风险，健康问题请遵医嘱。',
    '',
    f'X岛匿名版命令行客户端 XDCMD by TransparentLC{f" (Commit: {COMMIT_HASH[:7]})" if COMMIT_HASH else ""}',
    'https://github.com/TransparentLC/xdcmd',
    '',
))
try:
    if not config['Config'].getboolean('IgnoreNotice'):
        notice = xdnmb.api.session.get('https://nmb.ovear.info/nmb-notice.json').json()
        if notice['enable']:
            homepageLabelText += f'\n== 公告 ==\n{str(notice["date"])[0:4]}-{str(notice["date"])[4:6]}-{str(notice["date"])[6:8]}\n\n{xdnmb.util.stripHTML(notice["content"])}'
except:
    pass
homepageLabel = Label(text=ANSI(homepageLabelText), align=WindowAlign.CENTER)
forumBottomButton = Button('按 PgUp(h)/PgDn(l) 翻页')

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
    replyNameTextarea.text = ''
    replyTitleTextarea.text = ''
    replyContentTextarea.text = ''
    replyImageTextarea.text = ''
    xdnmb.util.floatAlert('发串', '发表成功')

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
                '  * 输入“$芦苇娘:...$”、“$彩色芦苇娘:...$”或“$凉宫Tips娘:...$”，可以发送对应的表情包。'
                    '芦苇娘人物形象原作者为 ddzx1323，表情包由 Anime801 制作。'
                    '凉宫 Tips 娘人物形象原作者为饼干为“iVUmXcE”的肥肥（No.50666176），表情包由饼干为“9QybryU”的肥肥制作（No.51412777）。\n'
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
        *(() if config['Config'].getboolean('Simplify') else (
            Frame(DynamicContainer(titleControlContainer), style='class:content'),
        )),
        VSplit((
            forumGroupControl,
            Window(width=1, char='|', style='class:divide'),
            forumContentControl,
        )),
        *(() if config['Config'].getboolean('Simplify') else (
            Window(height=1, char='-', style='class:divide'),
            VSplit(tuple(
                Label(text=HTML('<content-rev>[{0}]</content-rev>{1}').format(k, d), style='class:content')
                for k, d in (
                    ('Ctrl+E' if is_mac else 'Alt+E', '退出'),
                    ('↑(k)/↓(j)', '选择版面/串'),
                    ('Enter', '查看版面/串'),
                    ('PgUp(h)/PgDn(l)', '翻页'),
                    ('Ctrl+P' if is_mac else 'Alt+P', '串内跳页'),
                    ('Ctrl+S/U' if is_mac else 'Alt+=/-', '添加/删除订阅'),
                )
            )),
            VSplit(tuple(
                Label(text=HTML('<content-rev>[{0}]</content-rev>{1}').format(k, d), style='class:content')
                for k, d in (
                    ('Ctrl+Q' if is_mac else 'Alt+Q', '从串返回版面'),
                    ('Ctrl+N' if is_mac else 'Alt+N', '发串/回复'),
                    ('Ctrl+R' if is_mac else 'Alt+M', '查看版规'),
                    ('Ctrl+L' if is_mac else 'Alt+L', '查看引用'),
                    ('Ctrl+K' if is_mac else 'Alt+K', '举报'),
                    ('Tab', '将光标指向版面/串/悬浮窗按钮'),
                )
            )),
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

condition = Condition(lambda: not (len(container.floats) > 1 or showReplyForm))
@keyBinding.add('up', filter=condition)
@keyBinding.add('k', filter=condition)
def _(e):
    focus_previous(e)

@keyBinding.add('down', filter=condition)
@keyBinding.add('j', filter=condition)
def _(e):
    focus_next(e)

@ (keyBinding.add('c-e') if is_mac else keyBinding.add('escape', 'e'))
def _(e): 
    LRU_CACHE_DB.close(),
    get_app().exit(),

@keyBinding.add('pageup')
@keyBinding.add('h')
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

@keyBinding.add('l')
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

keyBinding.add('tab', filter=Condition(lambda: not condition()))(focus_next)
keyBinding.add('s-tab', filter=Condition(lambda: not condition()))(focus_previous)

@keyBinding.add('tab', filter=condition)
def _(e: KeyPressEvent):
    for focusFrom, focusTo in (
        (xdnmb.model.ButtonType.Forum, xdnmb.model.ButtonType.Thread),
        (xdnmb.model.ButtonType.Thread, xdnmb.model.ButtonType.Forum),
        (xdnmb.model.ButtonType.Reply, xdnmb.model.ButtonType.Thread),
    ):
        if xdnmb.util.focusToButton(focusFrom, focusTo):
            return

# c-m represents enter
@ (keyBinding.add('c-r') if is_mac else keyBinding.add('escape', 'm'))
def _(e: KeyPressEvent):
    if not forum:
        return
    xdnmb.util.floatAlert(
        f'{thread.forum.name if thread else forum.name}版规',
        thread.forum.notice if thread else forum.notice,
    )

@ (keyBinding.add('c-q') if is_mac else keyBinding.add('escape', 'q'))
def _(e: KeyPressEvent):
    global thread
    if not thread or len(container.floats) > 1 or showReplyForm:
        return
    thread = None
    forumContentControl.vertical_scroll = 0
    xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

@ (keyBinding.add('c-p') if is_mac else keyBinding.add('escape', 'p'))
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

@ (keyBinding.add('c-l') if is_mac else keyBinding.add('escape', 'l'))
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

@ (keyBinding.add('c-n') if is_mac else keyBinding.add('escape', 'n'))
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
        layout.focus(replyContentTextarea)
    else:
        xdnmb.util.focusToButton(None, xdnmb.model.ButtonType.Forum)

@ (keyBinding.add('c-k') if is_mac else keyBinding.add('escape', 'k'))
@xdnmb.util.floatAlertExceptionCatch
def _(e: KeyPressEvent):
    if showReplyForm:
        return
    tid: int = None
    for c in e.app.layout.current_window.content.text():
        if c[0] == 'class:button.text' and re.match(r'^No\.\d+$', c[1]):
            tid = int(re.match(r'^No\.(\d+)$', c[1]).group(1))
            break
    if tid is None:
        return

    watchroom: xdnmb.model.Forum = None
    for f in forums:
        if f.name == '值班室':
            watchroom = f
            break
    if watchroom is None:
        xdnmb.util.floatAlert('错误', '找不到值班室 (*ﾟーﾟ)')
        return

    @xdnmb.util.floatAlertExceptionCatch
    def callback(s: str):
        s = s.strip()
        if not s:
            xdnmb.util.floatAlert('举报', '举报理由不能为空')
            return
        xdnmb.api.postThread(
            watchroom,
            '',
            '',
            f'>>No.{tid}\n{s}',
            None,
            False,
        )
        xdnmb.util.floatAlert('举报', '举报成功，请等待红名处理')

    xdnmb.util.floatPrompt(
        '举报',
        f'请输入对No.{tid}的举报理由：\n（输入“举报理由”可以使用自动补全）',
        callback,
        WordCompleter((
            '举报理由：黄赌毒',
            '举报理由：政治敏感',
            '举报理由：谣言欺诈',
            '举报理由：广告Q群',
            '举报理由：引战辱骂',
            '举报理由：串版',
            '举报理由：风怒自删',
            '举报理由：错字自删',
            '举报理由：错饼自删',
        )),
    )

# Ctrl can't be used with =, so use c-s instead
@ (keyBinding.add('c-s') if is_mac else keyBinding.add('escape', '='))
@xdnmb.util.floatAlertExceptionCatch
def _(e: KeyPressEvent):
    if not thread:
        return
    xdnmb.api.addFeed(thread)
    xdnmb.util.floatAlert('订阅', '订阅大成功→_→')

@ (keyBinding.add('c-u') if is_mac else keyBinding.add('escape', '-'))
@xdnmb.util.floatAlertExceptionCatch
def _(e: KeyPressEvent):
    if not thread:
        return
    xdnmb.api.delFeed(thread)
    xdnmb.util.floatAlert('订阅', '取消订阅大成功←_←')

import configparser
import functools
import os
import sys
import typing
import xdnmb.action
import xdnmb.api
import xdnmb.model
import xdnmb.util

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
    '芦苇娘:|∀ﾟ': 'https://wkphoto.cdn.bcebos.com/9f510fb30f2442a76e8fe9c2c143ad4bd01302d7.jpg',
    '芦苇娘:(´ﾟДﾟ`)': 'https://wkphoto.cdn.bcebos.com/77094b36acaf2edde60d5e8e9d1001e9380193dc.jpg',
    '芦苇娘:(;´Д`)': 'https://wkphoto.cdn.bcebos.com/80cb39dbb6fd52667af62b73bb18972bd50736f3.jpg',
    '芦苇娘:| ω・´)': 'https://wkphoto.cdn.bcebos.com/a08b87d6277f9e2fe2b50a6f0f30e924b999f3d1.jpg',
    '芦苇娘:|-` )': 'https://wkphoto.cdn.bcebos.com/63d0f703918fa0ecf618706a369759ee3c6ddbfe.jpg',
    '芦苇娘:|д` )': 'https://wkphoto.cdn.bcebos.com/f7246b600c338744f2123b1b410fd9f9d62aa085.jpg',
    '芦苇娘:|ー` )': 'https://wkphoto.cdn.bcebos.com/a1ec08fa513d269758131c3a45fbb2fb4216d890.jpg',
    '芦苇娘:|∀` )': 'https://wkphoto.cdn.bcebos.com/21a4462309f79052949f53591cf3d7ca7acbd5d0.jpg',
    '芦苇娘:(つд⊂)': 'https://wkphoto.cdn.bcebos.com/dcc451da81cb39db1f5e7331c0160924ab18303e.jpg',
    '芦苇娘:(ﾟДﾟ≡ﾟДﾟ)': 'https://wkphoto.cdn.bcebos.com/09fa513d269759ee3f9374aca2fb43166c22df91.jpg',
    '芦苇娘:(|||ﾟДﾟ)': 'https://wkphoto.cdn.bcebos.com/279759ee3d6d55fbb11961417d224f4a21a4ddfd.jpg',
    '芦苇娘:( ﾟ∀ﾟ)': 'https://wkphoto.cdn.bcebos.com/4034970a304e251f11c6f29fb786c9177f3e53a7.jpg',
    '芦苇娘:(*´∀`)': 'https://wkphoto.cdn.bcebos.com/dcc451da81cb39db1e4c7031c0160924aa1830cc.jpg',
    '芦苇娘:(*ﾟ∇ﾟ)': 'https://wkphoto.cdn.bcebos.com/242dd42a2834349b21fe79e2d9ea15ce37d3bed8.jpg',
    '芦苇娘:(*ﾟーﾟ)': 'https://wkphoto.cdn.bcebos.com/d1a20cf431adcbef36026861bcaf2edda3cc9fa6.jpg',
    '芦苇娘:(　ﾟ 3ﾟ)': 'https://wkphoto.cdn.bcebos.com/00e93901213fb80e374276b026d12f2eb83894c1.jpg',
    '芦苇娘:( ´ー`)': 'https://wkphoto.cdn.bcebos.com/d1a20cf431adcbef34af6a61bcaf2edda3cc9f39.jpg',
    '芦苇娘:( ・_ゝ・)': 'https://wkphoto.cdn.bcebos.com/a8773912b31bb05120b7a44f267adab44bede0c2.jpg',
    '芦苇娘:( ´_ゝ`)': 'https://wkphoto.cdn.bcebos.com/e824b899a9014c0883e53cc21a7b02087af4f4ff.jpg',
    '芦苇娘:(・ー・)': 'https://wkphoto.cdn.bcebos.com/3801213fb80e7bec1a7917863f2eb9389b506b31.jpg',
    '芦苇娘:(ゝ∀･)': 'https://wkphoto.cdn.bcebos.com/b7fd5266d01609240738b57cc40735fae6cd34b3.jpg',
    '芦苇娘:(〃∀〃)': 'https://wkphoto.cdn.bcebos.com/242dd42a2834349b20ca7ae2d9ea15ce37d3be8c.jpg',
    '芦苇娘:(*ﾟ∀ﾟ*)': 'https://wkphoto.cdn.bcebos.com/728da9773912b31b675ada4e9618367adab4e1a7.jpg',
    '芦苇娘:( ﾟ∀。)': 'https://wkphoto.cdn.bcebos.com/b3b7d0a20cf431ad8a13575e5b36acaf2fdd9897.jpg',
    '芦苇娘:(`ε´ )': 'https://wkphoto.cdn.bcebos.com/902397dda144ad34628e90e0c0a20cf431ad85a7.jpg',
    '芦苇娘:(`ヮ´ )': 'https://wkphoto.cdn.bcebos.com/9825bc315c6034a83437afe6db134954082376fb.jpg',
    '芦苇娘:σ`∀´)': 'https://wkphoto.cdn.bcebos.com/bd315c6034a85edfe679e94459540923dc5475db.jpg',
    '芦苇娘:ﾟ ∀ﾟ)ノ': 'https://wkphoto.cdn.bcebos.com/060828381f30e92450948a565c086e061d95f7a1.jpg',
    '芦苇娘:(╬ﾟдﾟ)': 'https://wkphoto.cdn.bcebos.com/e4dde71190ef76c6fee9ec4c8d16fdfaaf516799.jpg',
    '芦苇娘:Σ( ﾟдﾟ)': 'https://wkphoto.cdn.bcebos.com/8c1001e93901213ff3b159bb44e736d12e2e95d2.jpg',
    '芦苇娘:(　д ) ﾟ ﾟ': 'https://wkphoto.cdn.bcebos.com/d1a20cf431adcbef34e66a61bcaf2edda2cc9f82.jpg',
    '芦苇娘:( ☉д⊙)': 'https://wkphoto.cdn.bcebos.com/b3119313b07eca8053f42d80812397dda04483e7.jpg',
    '芦苇娘:( -д-)': 'https://wkphoto.cdn.bcebos.com/c8177f3e6709c93dfcd119908f3df8dcd10054b1.jpg',
    '芦苇娘:(>д<)': 'https://wkphoto.cdn.bcebos.com/960a304e251f95ca57ca85d1d9177f3e6709529d.jpg',
    '芦苇娘:･ﾟ( ﾉд`ﾟ)': 'https://wkphoto.cdn.bcebos.com/91529822720e0cf3d8245a9c1a46f21fbf09aa81.jpg',
    '芦苇娘:( TдT)': 'https://wkphoto.cdn.bcebos.com/203fb80e7bec54e7793f0e79a9389b504ec26a81.jpg',
    '芦苇娘:(￣∇￣)': 'https://wkphoto.cdn.bcebos.com/dbb44aed2e738bd453fba656b18b87d6267ff9fb.jpg',
    '芦苇娘:(￣3￣)': 'https://wkphoto.cdn.bcebos.com/622762d0f703918f5d2529ad413d269758eec4e5.jpg',
    '芦苇娘:(￣ｰ￣)': 'https://wkphoto.cdn.bcebos.com/9213b07eca8065383ac8b37487dda144ad3482b2.jpg',
    '芦苇娘:(￣ . ￣)': 'https://wkphoto.cdn.bcebos.com/4e4a20a4462309f79b98b975620e0cf3d6cad6e5.jpg',
    '芦苇娘:(￣皿￣)': 'https://wkphoto.cdn.bcebos.com/3ac79f3df8dcd100284eec46628b4710b8122f82.jpg',
    '芦苇娘:(￣艸￣)': 'https://wkphoto.cdn.bcebos.com/b7003af33a87e950199ee40b00385343faf2b4cf.jpg',
    '芦苇娘:(￣︿￣)': 'https://wkphoto.cdn.bcebos.com/b3b7d0a20cf431ad8a09575e5b36acaf2fdd98f9.jpg',
    '芦苇娘:(￣︶￣)': 'https://wkphoto.cdn.bcebos.com/2934349b033b5bb5ec4a349926d3d539b600bc33.jpg',
    '芦苇娘:ヾ(´ωﾟ｀)': 'https://wkphoto.cdn.bcebos.com/4afbfbedab64034fbb43d561bfc379310b551dce.jpg',
    '芦苇娘:(*´ω`*)': 'https://wkphoto.cdn.bcebos.com/0ff41bd5ad6eddc4f433a39c29dbb6fd53663384.jpg',
    '芦苇娘:(・ω・)': 'https://wkphoto.cdn.bcebos.com/b64543a98226cffcd1d3abd5a9014a90f703ead8.jpg',
    '芦苇娘:(´・ω・`)': 'https://wkphoto.cdn.bcebos.com/b999a9014c086e06f091282c12087bf40ad1cb98.jpg',
    '芦苇娘:(`・ω・´)': 'https://wkphoto.cdn.bcebos.com/0b46f21fbe096b63e3e14a371c338744eaf8acd8.jpg',
    '芦苇娘:( `_っ´)': 'https://wkphoto.cdn.bcebos.com/472309f7905298227e0b2ea4c7ca7bcb0a46d498.jpg',
    '芦苇娘:( `ー´)': 'https://wkphoto.cdn.bcebos.com/cc11728b4710b9125ef9e199d3fdfc0392452298.jpg',
    '芦苇娘:( ´_っ`)': 'https://wkphoto.cdn.bcebos.com/203fb80e7bec54e779740e79a9389b504fc26a38.jpg',
    '芦苇娘:( ´ρ`)': 'https://wkphoto.cdn.bcebos.com/3812b31bb051f8195cf3172dcab44aed2f73e787.jpg',
    '芦苇娘:( ﾟωﾟ)': 'https://wkphoto.cdn.bcebos.com/7dd98d1001e939016afa99596bec54e737d196d8.jpg',
    '芦苇娘:(oﾟωﾟo)': 'https://wkphoto.cdn.bcebos.com/faedab64034f78f032f58e9469310a55b2191cde.jpg',
    '芦苇娘:(　^ω^)': 'https://wkphoto.cdn.bcebos.com/faedab64034f78f032968e9469310a55b3191c33.jpg',
    '芦苇娘:(｡◕∀◕｡)': 'https://wkphoto.cdn.bcebos.com/0b55b319ebc4b7458f43a371dffc1e178b821585.jpg',
    '芦苇娘:/( ◕‿‿◕ )\\': 'https://wkphoto.cdn.bcebos.com/faedab64034f78f0339f8d9469310a55b2191cc4.jpg',
    '芦苇娘:ヾ(´ε`ヾ)': 'https://wkphoto.cdn.bcebos.com/2cf5e0fe9925bc31346b16ff4edf8db1cb1370a6.jpg',
    '芦苇娘:(ノﾟ∀ﾟ)ノ': 'https://wkphoto.cdn.bcebos.com/3812b31bb051f8195cdf172dcab44aed2f73e7db.jpg',
    '芦苇娘:(σﾟдﾟ)σ': 'https://wkphoto.cdn.bcebos.com/34fae6cd7b899e51bcb42d7352a7d933c8950d9a.jpg',
    '芦苇娘:(σﾟ∀ﾟ)σ': 'https://wkphoto.cdn.bcebos.com/71cf3bc79f3df8dc410798f6dd11728b4710289a.jpg',
    '芦苇娘:|дﾟ )': 'https://wkphoto.cdn.bcebos.com/c75c10385343fbf280acb244a07eca8064388fd0.jpg',
    '芦苇娘:ﾟ(つд`ﾟ)': 'https://wkphoto.cdn.bcebos.com/adaf2edda3cc7cd9ca0e23be2901213fb80e91b1.jpg',
    '芦苇娘:⊂彡☆))д`)': 'https://wkphoto.cdn.bcebos.com/b3b7d0a20cf431ad8a08575e5b36acaf2fdd98fa.jpg',
    '芦苇娘:⊂彡☆))д´)': 'https://wkphoto.cdn.bcebos.com/6a600c338744ebf800ed7058c9f9d72a6059a73c.jpg',
    '芦苇娘:⊂彡☆))∀`)': 'https://wkphoto.cdn.bcebos.com/f603918fa0ec08faafd504c049ee3d6d54fbda84.jpg',
    '芦苇娘:(´∀((☆ミつ': 'https://wkphoto.cdn.bcebos.com/7af40ad162d9f2d3a2ca3088b9ec8a136227ccfa.jpg',
    '芦苇娘:( ´_ゝ`)旦': 'https://wkphoto.cdn.bcebos.com/8c1001e93901213ff4f35abb44e736d12e2e9590.jpg',
    # '彩色芦苇娘:': '',
    '彩色芦苇娘:|∀ﾟ': 'https://wkphoto.cdn.bcebos.com/4610b912c8fcc3ce5753da548245d688d53f20c1.jpg',
    '彩色芦苇娘:(´ﾟДﾟ`)': 'https://wkphoto.cdn.bcebos.com/b3119313b07eca8054ee2a80812397dda04483e9.jpg',
    '彩色芦苇娘:(;´Д`)': 'https://wkphoto.cdn.bcebos.com/f603918fa0ec08faa83801c049ee3d6d55fbda99.jpg',
    '彩色芦苇娘:| ω・´)': 'https://wkphoto.cdn.bcebos.com/d000baa1cd11728bd7e09f45d8fcc3cec2fd2c83.jpg',
    '彩色芦苇娘:|-` )': 'https://wkphoto.cdn.bcebos.com/1f178a82b9014a9038d555dab9773912b21beeea.jpg',
    '彩色芦苇娘:|д` )': 'https://wkphoto.cdn.bcebos.com/00e93901213fb80e3cea73b026d12f2eb9389499.jpg',
    '彩色芦苇娘:|ー` )': 'https://wkphoto.cdn.bcebos.com/4610b912c8fcc3ce570dda548245d688d53f2083.jpg',
    '彩色芦苇娘:|∀` )': 'https://wkphoto.cdn.bcebos.com/5fdf8db1cb134954638cfb03464e9258d0094ac2.jpg',
    '彩色芦苇娘:(つд⊂)': 'https://wkphoto.cdn.bcebos.com/b7fd5266d01609240c1eb07cc40735fae6cd3499.jpg',
    '彩色芦苇娘:(ﾟДﾟ≡ﾟДﾟ)': 'https://wkphoto.cdn.bcebos.com/faf2b2119313b07efa71436f1cd7912396dd8c8c.jpg',
    '彩色芦苇娘:(|||ﾟДﾟ)': 'https://wkphoto.cdn.bcebos.com/0df3d7ca7bcb0a46ffaf985e7b63f6246a60afc3.jpg',
    '彩色芦苇娘:( ﾟ∀ﾟ)': 'https://wkphoto.cdn.bcebos.com/d1a20cf431adcbef4bf86d61bcaf2edda2cc9f8c.jpg',
    '彩色芦苇娘:(*´∀`)': 'https://wkphoto.cdn.bcebos.com/f11f3a292df5e0fef8009b664c6034a85edf72b8.jpg',
    '彩色芦苇娘:(*ﾟ∇ﾟ)': 'https://wkphoto.cdn.bcebos.com/060828381f30e9245cd58e565c086e061d95f760.jpg',
    '彩色芦苇娘:(*ﾟーﾟ)': 'https://wkphoto.cdn.bcebos.com/d53f8794a4c27d1e4eea28a30bd5ad6edcc4388c.jpg',
    '彩色芦苇娘:(　ﾟ 3ﾟ)': 'https://wkphoto.cdn.bcebos.com/a8773912b31bb0512b3ca14f267adab44aede0b9.jpg',
    '彩色芦苇娘:( ´ー`)': 'https://wkphoto.cdn.bcebos.com/908fa0ec08fa513ddc907eb92d6d55fbb2fbd99b.jpg',
    '彩色芦苇娘:( ・_ゝ・)': 'https://wkphoto.cdn.bcebos.com/0b7b02087bf40ad18fffd584472c11dfa9ecceba.jpg',
    '彩色芦苇娘:( ´_ゝ`)': 'https://wkphoto.cdn.bcebos.com/dbb44aed2e738bd46914a056b18b87d6277ff9a4.jpg',
    '彩色芦苇娘:(・ー・)': 'https://wkphoto.cdn.bcebos.com/377adab44aed2e735127954b9701a18b86d6fa8f.jpg',
    '彩色芦苇娘:(ゝ∀･)': 'https://wkphoto.cdn.bcebos.com/91529822720e0cf3dee25c9c1a46f21fbe09aabb.jpg',
    '彩色芦苇娘:(〃∀〃)': 'https://wkphoto.cdn.bcebos.com/77094b36acaf2edde2385a8e9d1001e93801938f.jpg',
    '彩色芦苇娘:(*ﾟ∀ﾟ*)': 'https://wkphoto.cdn.bcebos.com/f636afc379310a557031cc93a74543a9822610bb.jpg',
    '彩色芦苇娘:( ﾟ∀。)': 'https://wkphoto.cdn.bcebos.com/37d3d539b6003af31c72cf07252ac65c1138b688.jpg',
    '彩色芦苇娘:(`ε´ )': 'https://wkphoto.cdn.bcebos.com/00e93901213fb80e3ce773b026d12f2eb93894a6.jpg',
    '彩色芦苇娘:(`ヮ´ )': 'https://wkphoto.cdn.bcebos.com/e4dde71190ef76c6f219e84c8d16fdfaae516789.jpg',
    '彩色芦苇娘:σ`∀´)': 'https://wkphoto.cdn.bcebos.com/838ba61ea8d3fd1f3cc2b15d204e251f94ca5f89.jpg',
    '彩色芦苇娘:ﾟ ∀ﾟ)ノ': 'https://wkphoto.cdn.bcebos.com/728da9773912b31b63a7de4e9618367adbb4e18a.jpg',
    '彩色芦苇娘:(╬ﾟдﾟ)': 'https://wkphoto.cdn.bcebos.com/0bd162d9f2d3572ce18d8ebb9a13632762d0c36e.jpg',
    '彩色芦苇娘:Σ( ﾟдﾟ)': 'https://wkphoto.cdn.bcebos.com/dcc451da81cb39db15ae7531c0160924ab18306e.jpg',
    '彩色芦苇娘:(　д ) ﾟ ﾟ': 'https://wkphoto.cdn.bcebos.com/b58f8c5494eef01f64050aa2f0fe9925bc317d47.jpg',
    '彩色芦苇娘:( ☉д⊙)': 'https://wkphoto.cdn.bcebos.com/2cf5e0fe9925bc313f6e13ff4edf8db1cb1370a1.jpg',
    '彩色芦苇娘:( -д-)': 'https://wkphoto.cdn.bcebos.com/fc1f4134970a304e5a4bb29dc1c8a786c9175c6f.jpg',
    '彩色芦苇娘:(>д<)': 'https://wkphoto.cdn.bcebos.com/f636afc379310a55704dcc93a74543a98226106f.jpg',
    '彩色芦苇娘:･ﾟ( ﾉд`ﾟ)': 'https://wkphoto.cdn.bcebos.com/37d12f2eb9389b5002cdf2359535e5dde7116ea2.jpg',
    '彩色芦苇娘:( TдT)': 'https://wkphoto.cdn.bcebos.com/a6efce1b9d16fdfaf75ed489a48f8c5494ee7ba2.jpg',
    '彩色芦苇娘:(￣∇￣)': 'https://wkphoto.cdn.bcebos.com/4b90f603738da977e8e8954ca051f8198718e396.jpg',
    '彩色芦苇娘:(￣3￣)': 'https://wkphoto.cdn.bcebos.com/94cad1c8a786c917fb2e405ed93d70cf3bc757a3.jpg',
    '彩色芦苇娘:(￣ｰ￣)': 'https://wkphoto.cdn.bcebos.com/2fdda3cc7cd98d1045121f56313fb80e7aec9096.jpg',
    '彩色芦苇娘:(￣ . ￣)': 'https://wkphoto.cdn.bcebos.com/0b7b02087bf40ad18fc9d584472c11dfa9ecceac.jpg',
    '彩色芦苇娘:(￣皿￣)': 'https://wkphoto.cdn.bcebos.com/64380cd7912397dd95558a634982b2b7d0a287ac.jpg',
    '彩色芦苇娘:(￣艸￣)': 'https://wkphoto.cdn.bcebos.com/30adcbef76094b36929f098ab3cc7cd98d109d43.jpg',
    '彩色芦苇娘:(￣︿￣)': 'https://wkphoto.cdn.bcebos.com/738b4710b912c8fc5196e4aaec039245d688216b.jpg',
    '彩色芦苇娘:(￣︶￣)': 'https://wkphoto.cdn.bcebos.com/e850352ac65c10387972dca5a2119313b07e894c.jpg',
    '彩色芦苇娘:ヾ(´ωﾟ｀)': 'https://wkphoto.cdn.bcebos.com/7aec54e736d12f2ef242bc075fc2d56285356815.jpg',
    '彩色芦苇娘:(*´ω`*)': 'https://wkphoto.cdn.bcebos.com/00e93901213fb80e3cf673b026d12f2eb93894b5.jpg',
    '彩色芦苇娘:(・ω・)': 'https://wkphoto.cdn.bcebos.com/eac4b74543a98226079c39409a82b9014a90eb7c.jpg',
    '彩色芦苇娘:(´・ω・`)': 'https://wkphoto.cdn.bcebos.com/4034970a304e251f15f2f69fb786c9177f3e534b.jpg',
    '彩色芦苇娘:(`・ω・´)': 'https://wkphoto.cdn.bcebos.com/83025aafa40f4bfb40978c33134f78f0f7361815.jpg',
    '彩色芦苇娘:( `_っ´)': 'https://wkphoto.cdn.bcebos.com/83025aafa40f4bfb40978c33134f78f0f7361815.jpg',
    '彩色芦苇娘:( `ー´)': 'https://wkphoto.cdn.bcebos.com/08f790529822720e04caf09d6bcb0a46f21fab54.jpg',
    '彩色芦苇娘:( ´_っ`)': 'https://wkphoto.cdn.bcebos.com/8c1001e93901213ffe755cbb44e736d12f2e9516.jpg',
    '彩色芦苇娘:( ´ρ`)': 'https://wkphoto.cdn.bcebos.com/eaf81a4c510fd9f9c031470e352dd42a2834a4b6.jpg',
    '彩色芦苇娘:( ﾟωﾟ)': 'https://wkphoto.cdn.bcebos.com/5d6034a85edf8db1ac0f6e031923dd54564e74b7.jpg',
    '彩色芦苇娘:(oﾟωﾟo)': 'https://wkphoto.cdn.bcebos.com/a8773912b31bb0512b05a14f267adab44aede0b0.jpg',
    '彩色芦苇娘:(　^ω^)': 'https://wkphoto.cdn.bcebos.com/cb8065380cd79123a4e68613bd345982b2b78056.jpg',
    '彩色芦苇娘:(｡◕∀◕｡)': 'https://wkphoto.cdn.bcebos.com/35a85edf8db1cb1321292e74cd54564e92584b10.jpg',
    '彩色芦苇娘:/( ◕‿‿◕ )\\': 'https://wkphoto.cdn.bcebos.com/7e3e6709c93d70cfb3bab86ae8dcd100baa12b10.jpg',
    '彩色芦苇娘:ヾ(´ε`ヾ)': 'https://wkphoto.cdn.bcebos.com/810a19d8bc3eb13544e7a5dcb61ea8d3fd1f44b0.jpg',
    '彩色芦苇娘:(ノﾟ∀ﾟ)ノ': 'https://wkphoto.cdn.bcebos.com/a686c9177f3e67094f2057982bc79f3df8dc55b0.jpg',
    '彩色芦苇娘:(σﾟдﾟ)σ': 'https://wkphoto.cdn.bcebos.com/86d6277f9e2f0708c9453867f924b899a901f211.jpg',
    '彩色芦苇娘:(σﾟ∀ﾟ)σ': 'https://wkphoto.cdn.bcebos.com/d788d43f8794a4c2e703f54c1ef41bd5ad6e39b0.jpg',
    '彩色芦苇娘:|дﾟ )': 'https://wkphoto.cdn.bcebos.com/1c950a7b02087bf4e6ea458ee2d3572c11dfcf57.jpg',
    '彩色芦苇娘:ﾟ(つд`ﾟ)': 'https://wkphoto.cdn.bcebos.com/09fa513d269759eec10e72aca2fb43166d22df7f.jpg',
    '彩色芦苇娘:⊂彡☆))д`)': 'https://wkphoto.cdn.bcebos.com/b7003af33a87e9501214e10b00385343fbf2b451.jpg',
    '彩色芦苇娘:⊂彡☆))д´)': 'https://wkphoto.cdn.bcebos.com/f9dcd100baa1cd11fcf46047a912c8fcc3ce2d12.jpg',
    '彩色芦苇娘:⊂彡☆))∀`)': 'https://wkphoto.cdn.bcebos.com/8718367adab44aedf60cac83a31c8701a18bfb13.jpg',
    '彩色芦苇娘:(´∀((☆ミつ': 'https://wkphoto.cdn.bcebos.com/8718367adab44aedf66cac83a31c8701a18bfbb3.jpg',
    '彩色芦苇娘:( ´_ゝ`)旦': 'https://wkphoto.cdn.bcebos.com/ae51f3deb48f8c54c86ed7482a292df5e0fe7f13.jpg',
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

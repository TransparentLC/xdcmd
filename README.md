# xdcmd

[![AUR version](https://img.shields.io/aur/version/xdao)](https://aur.archlinux.org/packages/xdao) [![build](https://github.com/TransparentLC/xdcmd/actions/workflows/build.yml/badge.svg)](https://github.com/TransparentLC/xdcmd/actions/workflows/build.yml)

[X 岛匿名版](https://nmbxd.com/)命令行客户端。

用户反馈和技术支持集中串：[No.50750950](https://nmbxd.com/t/50750950)

快速安装：

* ![Arch Linux](https://img.shields.io/badge/Arch%20Linux-333?logo=archlinux) `yay -S xdao`
  * 感谢饼干为“ygaCgTJ”的肥肥提供[打包](https://aur.archlinux.org/packages/xdao)～(ノﾟ∀ﾟ)ノ
* ![Windows 10+](https://img.shields.io/badge/Windows-10+-06b?logo=windows) 使用 GitHub Actions 自动打包成可执行文件，可以从[这里](https://nightly.link/TransparentLC/xdcmd/workflows/build/master)下载。
  * `xdcmd-windows` 原始的打包产物。
  * `xdcmd-windows-onefile` 单文件版，实际上是在运行的时候将主程序什么的自解压到临时目录。
  * `xdcmd-windows-upx` 将打包产物使用 [UPX](https://upx.github.io/) 压缩后的版本，**不知道该下载哪个的话就选这个吧**。
* ![Ubuntu 22.04+](https://img.shields.io/badge/Ubuntu-22.04+-e52?logo=ubuntu) 使用 GitHub Actions 自动打包成可执行文件，可以从[这里](https://nightly.link/TransparentLC/xdcmd/workflows/build/master)下载。
    * `xdcmd-ubuntu` 原始的打包产物，**不知道该下载哪个的话就选这个吧**。
    * `xdcmd-ubuntu-onefile` 单文件版，实际上是在运行的时候将主程序什么的自解压到临时目录。

![](https://user-images.githubusercontent.com/47057319/182030427-6c75ec92-f808-4cbc-8102-2c868db33093.png)

## 基本介绍

“在命令行的环境下重现 X 岛网页版的刷岛体验”，原本只是这么一个很简单的想法，在做出初步的原型然后发到岛上之后意外地很受肥肥们的欢迎，于是就继续把完整版做出来了 (\*´ω`\*)

由于技术和精力所限，这个客户端只能实现看串、发串、查看引用和订阅管理这些比较基本的功能，没有实现历史记录和饼干切换等高级功能，在功能丰富程度和使用体验上均与 X 岛的网页版以及已有的手机客户端相差甚远。在这些基本功能完成后，**除非存在严重影响使用的恶性 BUG 需要修复，我可能不会继续实现更多的功能需求**。当然如果你愿意贡献代码，那就再好不过啦！(ゝ∀･)

不管怎么说，在命令行里刷岛这件事本身已经非常炫酷了 ᕕ( ᐛ )ᕗ

* 执行 `python main.py` 就可以启动了，在此之前不要忘了 `pip install -r requirements.txt`，需要使用 Python 3.10 或以上的版本。
* 你也可以手动在 `PATH` 下创建一个用于快速启动的脚本。例如，想要在终端输入 `xdcmd` 直接启动此项目：
  * Windows：`(echo @echo off & echo python /path/to/xdcmd/main.py %*) > %SystemRoot%\xdcmd.cmd`
  * Linux：`(echo '#!/bin/sh\npython3 /path/to/xdcmd/main.py "$@"' > /usr/local/bin/xdcmd) && chmod +x /usr/local/bin/xdcmd`
* 建议搭配等宽字体使用。对于 Windows 用户，建议通过 [Windows Terminal](https://apps.microsoft.com/store/detail/windows-terminal/9N0DX20HK701) 使用这个客户端，在传统的终端下使用可能会存在一些问题。

## 使用截图

| 查看版面 | 查看串 | 发串 |
| --- | --- | --- |
| ![](https://user-images.githubusercontent.com/47057319/182030800-f2d3fce9-5581-433c-8cb5-ed04acd2fe7b.png) | ![](https://user-images.githubusercontent.com/47057319/182030803-62d1259f-f7af-4c68-a015-81711f41493d.png) | ![](https://user-images.githubusercontent.com/47057319/182030805-cfb44b6d-09dc-48cf-af52-fe4de2abd6e3.png) |

| 用 VSCode 刷岛 | [用哔哔小子刷岛（？）](https://m.weibo.cn/detail/4797497303630002) |
| --- | --- |
| ![](https://user-images.githubusercontent.com/47057319/185427750-ffa91eb4-0e93-4afe-bfdb-34ce8df430d3.png) | ![](https://user-images.githubusercontent.com/47057319/182030806-dbe8943c-931b-4adf-8776-4628f63ad38e.png) |

> 在配置文件中启用单色模式，并按照[“怀旧式命令提示符”](https://docs.microsoft.com/zh-cn/windows/terminal/custom-terminal-gallery/retro-command-prompt)的教程设置 Windows Terminal 主题，即可体验“用哔哔小子刷岛”的效果。

## 配置文件

在启动时，会按照以下顺序查找配置文件：

* 使用命令行参数 `--config` 或 `-c` 指定的配置文件路径。
* `$XDG_CONFIG_HOME/xdcmd/config.ini`，其中 `$XDG_CONFIG_HOME` 的默认值为 `~/.config`，在 Windows 下 `~` 相当于 `%HOMEPATH%`。
* `main.py` 所在目录的 `config.ini`。

如果没有找到配置文件，则会在 `$XDG_CONFIG_HOME/xdcmd/config.ini` 写入默认的配置文件。

配置文件的内容如下：

```ini
[Config]
# 图片CDN地址
# 如果留空，则运行时会通过X岛API自动获取
# 一般不需要手动设定
cdnpath = https://image.nmb.best/
# 饼干
# 自行在用户系统中扫描饼干二维码，可以得到形如{"cookie":"...","name":"..."}的JSON数据
# 将cookie字段的值填到这里就可以了（这个饼干是随机生成的示例，并不能实际使用）
cookie = Y%85m%E5J5%F4%7D%98%DB%98%0Cm%08%11%9DV%1EIi%956W%10
# 订阅ID
# 可以通过python -c "import secrets;print(secrets.token_urlsafe(24))"随机生成一个
# 虽然API里用的参数名称都是UUID，但是实际上可以使用包括空字符串在内的任意字符串
# 也可以将在其他客户端使用的订阅ID填到这里
feeduuid = C7hswJmRY1eHo6FfCqJbmWgva8D3vAI6
# 使用单色模式
monochrome = False
# 显示缩略图
# 此功能依赖于chafa（https://hpjansson.org/chafa/），需要自行使用包管理器安装，或下载可执行文件并放在PATH环境变量包含的路径下
# 在单色模式下也不会显示缩略图
# 需要额外的时间加载图片，如果介意拖慢速度的话可以关闭此功能
imagepreview = True
# 缩略图的最大宽度
imagepreviewwidth = 24
# 缩略图的最大高度
imagepreviewheight = 6
# 隐藏Tips
hidetips = False
# 隐藏饼干
# 红名的名字和PO主的标记不会被隐藏
hidecookie = False
# 只看PO
# 不会影响Tips的出现
poonly = False
# 不在主页上显示公告
ignorenotice = False
```

## 其他

* 本项目包含了“芦苇娘表情包”（[黑白版](https://www.acfun.cn/a/ac10200508)、[彩色版](https://www.acfun.cn/a/ac15661021)）的下载链接。芦苇娘人物形象原作者为 ddzx1323，表情包由 Anime801 制作。
* 本项目包含了“凉宫 Tips 娘表情包”的下载链接。凉宫 Tips 娘人物形象原作者为饼干为“iVUmXcE”的肥肥（[No.50666176](https://nmbxd.com/t/50666176)），表情包由饼干为“9QybryU”的肥肥制作（[No.51412777](https://nmbxd.com/t/51412777)）。
* 虽然本项目的开源性质决定了任何人都可以自由地使用、修改和分发本项目的源代码，但原作者个人仍然会强烈反对和谴责尝试将本项目的源代码用于适配“阿苇岛匿名版”的行为。
* 加载过的缩略图缓存保存位置为 `$XDG_CACHE_HOME/xdcmd/lru-cache.db`，其中 `$XDG_CACHE_HOME` 的默认值为 `~/.cache`。
* 如果你有兴趣的话，可以在 [Wiki](https://github.com/TransparentLC/xdcmd/wiki/%E8%87%AA%E5%B7%B1%E6%95%B4%E7%90%86%E7%9A%84-X-%E5%B2%9B%E5%8C%BF%E5%90%8D%E7%89%88-API-%E6%96%87%E6%A1%A3) 中查看原作者自己整理的 X 岛匿名版 API 文档。
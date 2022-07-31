# xdcmd

[X 岛匿名版](https://nmbxd.com/)命令行客户端。

![](https://user-images.githubusercontent.com/47057319/182030427-6c75ec92-f808-4cbc-8102-2c868db33093.png)

## 基本介绍

“在命令行的环境下重现 X 岛网页版的刷岛体验”，原本只是这么一个很简单的想法，在做出初步的原型然后发到岛上之后意外地[很受肥肥们的欢迎](https://nmbxd.com/t/50750950)，于是就继续把完整版做出来了 (*´ω`*)

<details>

<summary>实际使用截图</summary>

![](https://user-images.githubusercontent.com/47057319/182030800-f2d3fce9-5581-433c-8cb5-ed04acd2fe7b.png)

![](https://user-images.githubusercontent.com/47057319/182030803-62d1259f-f7af-4c68-a015-81711f41493d.png)

![](https://user-images.githubusercontent.com/47057319/182030805-cfb44b6d-09dc-48cf-af52-fe4de2abd6e3.png)

![](https://user-images.githubusercontent.com/47057319/182030806-dbe8943c-931b-4adf-8776-4628f63ad38e.png)

> 上图的效果为启用单色模式后，与 Windows Terminal 的[“怀旧式命令提示符”](https://docs.microsoft.com/zh-cn/windows/terminal/custom-terminal-gallery/retro-command-prompt)一起使用的效果。

</details>

由于技术和精力所限，这个客户端只能实现看串、发串和查看引用这些比较基本的功能，没有实现订阅管理、历史记录、饼干切换等高级功能，在功能丰富程度和使用体验上均与 X 岛的网页版以及已有的手机客户端相差甚远。在这些基本功能完成后，**除非存在严重影响使用的恶性 BUG 需要修复，我可能不会继续实现更多的功能需求**。当然如果你愿意贡献代码，那就再好不过啦！(ゝ∀･)

不管怎么说，在命令行里刷岛这件事本身已经非常炫酷了 ᕕ( ᐛ )ᕗ

* 执行 `python main.py` 就可以启动了，在此之前不要忘了 `pip install -r requirements.txt`。
* 开发时使用的是 Python 3.10，使用更低的大版本也可能可以运行，不过我没有测试过。
* 建议搭配等宽字体使用。对于 Windows 用户，建议通过 [Windows Terminal](https://apps.microsoft.com/store/detail/windows-terminal/9N0DX20HK701) 使用这个客户端，在传统的终端下使用可能会存在一些问题。

## 配置文件

在第一次按 <kbd>Alt+E</kbd> 正常退出后，会在 `main.py` 所在的目录下写入配置文件 `config.ini`，内容如下：

```ini
[Config]
# 图片CDN地址
# 如果留空则运行时会通过https://api.nmb.best/api/getCDNPath自动获取
# 一般不需要手动设定
cdnpath = https://image.nmb.best/
# 饼干
# 自行在用户系统中扫描饼干二维码，可以得到形如{"cookie":"...","name":"..."}的JSON数据
# 将cookie字段的值填到这里就可以了（这个饼干是随机生成的示例，并不能实际使用）
cookie = Y%85m%E5J5%F4%7D%98%DB%98%0Cm%08%11%9DV%1EIi%956W%10
# 使用单色模式
monochrome = False
# 显示缩略图
# 此功能依赖于chafa（https://hpjansson.org/chafa/），需要自行使用包管理器安装，或下载可执行文件并放在PATH环境变量包含的路径下
# 在单色模式下也不会显示缩略图
imagepreview = True
# 缩略图的最大宽度
imagepreviewwidth = 24
# 缩略图的最大高度
imagepreviewheight = 6
```

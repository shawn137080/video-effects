# Video Effects：25个可复用视频特效

给 Codex / Claude Code 一段自己的素材，用自然语言说想要什么效果。
Agent 根据内容、手势和构图选效果，写参数，再输出1080×1920、30fps MP4。

这是**25类特效的独立技能包**，包含整场景抖动/回弹、特效图层、参数化标题、
Three.js 手机模型，以及可选的本机人物去背与手部坐标工具。
完整剪辑规划、转录、音乐库、轮播图、发布功能不在本次开源范围内。

## 安装

```sh
git clone https://github.com/shawn137080/video-effects.git
cd video-effects
python3 install.py --agent codex
# Claude Code 用户：python3 install.py --agent claude
```

需要另外已有 Python 3.10+、Node 20+、FFmpeg、Chrome、GSAP、HyperFrames。
[配置方法](video-effects/references/setup.md)。安装器不自动下载运行环境；
不会覆盖已有技能，明确使用 `--upgrade` 才会备份并升级。
当前渲染验证环境是 macOS，人物去背和追踪使用 Apple Vision。

## 怎么用

> 用 video-effects，给这段口播加镜头缩放。手伸出去时推近，收指时拉回，
> 不要截断说话，保留原声，输出新文件让我看。

> 给这段视频做人物出框，先检查人物去背边缘。不要用别人的演示素材。

> 计时器放在我食指下面，跟随同一根手指。没检测清楚的帧不要猜位置。

Agent 编写参数，你不用填写JSON。
[25类效果中英文清单](video-effects/references/catalog.md) ·
[完整参数](video-effects/references/parameters.md) ·
[动作对齐](video-effects/references/gestures.md)。

每个效果都有独立描述文件，复用同一份渲染实现。编号有间隔是因为重复模式
已合并，不是缺了效果。人物去背、图片、B-roll、真实图表数据由使用者提供。
默认没有演示编号和宣传标题，内容标题可以自己改或关闭。

## 许可与边界

自有代码使用 **MIT**：允许商用、修改及再分发，须保留许可声明。
字体和Three.js保留各自许可；外部运行环境遵守它们自己的条款。
不含私人录像、模型缓存、付费作者模板或账号密钥。

这是参数化工具，不保证任意素材自动变好看。需要看实际输出，检查人脸、
文字、手势、声音和转场。每次重渲染使用新文件名，旧版保留。

[验证范围与复现方法](VALIDATION.md)。

# B站直播录播姬 &nbsp; By: Red_lnn

## 注意事项
- 不允许将本项目运用于非法以及违反[哔哩哔哩弹幕网用户协议](https://www.bilibili.com/blackboard/topic/activity-cn8bxPLzz.html)的用途
- 运行时如要停止录制并退出，请按键盘的 `Ctrl-C` 组合键
- 如要修改录制设置，请以纯文本方式打开 `config.py` 文件
- 有新功能需求请直接提 `Pull requests` ，提 `issue` 可能会被无视
- 建议使用 `flv` 格式进行录制（默认），以防止意外中断导致录制文件损坏，若要进行剪辑可使用 FFmpeg 转换为 mp4 文件后再倒入到剪辑软件  
```
使用 FFmpeg 转换 flv 为 mp4:
(以下方式均不涉及重新编码，仅更换一种封装格式)
1. 直接使用命令进行转换: "ffmpeg -i {input}.flv -c copy {output}.mp4"
2. Windows系统下运行 "flv2mp4.bat" 可直接将 "download" 目录下的所有flv文件（不会遍历子目录）转换为mp4文件并放在 "convert" 文件夹中
```

## 特点（大雾）
- __非常非常非常简陋简单__，不支持多个直播间，不支持自动投稿，不支持录制弹幕和礼物，不支持其他直播平台，不支持Docker部署
- 利用 FFmpeg 直接抓取主播推送的音视频流，无需打开浏览器，CPU与GPU占用率低
- 仅支持检测与录制单个直播间（需要录制多个直播间请复制多份实例并分开单独配置与启动）
- 不支持自动投稿（若有相关需求请使用其他类似项目）
- 没有使用 `ffmpegpy` 或 `ffmpeg-python` 库（~~其实是因为懒得看文档，等哪天心血来潮可能就会用了~~）
- ~~因为是自己写的，可以随便改~~ （其实主要还是想练练手）

## 使用方式
1. 安装 Python(>=3.7) 并设置环境变量
2. 打开终端或命令行进入本脚本所在目录
3. 通过 pip 安装必须的第三方库
```
Windows: pip install -r requirements.txt
Linux: python3 -m pip install -r requirements.txt
```
4. 下载 FFmpeg 并正确设置环境变量（[下载地址](http://www.ffmpeg.org/download.html)）
6. Windows 环境请直接双击运行`start.bat`
7. Linux 环境请先执行 `chmod +x start.sh` 后，再执行 `./start.sh`

## 使用提醒
- 若开启了`verbose`或`debug`模式，请注意及时清理日志以避免因录制时间长导致日志文件过大
- 本程序并非完美无缺，虽然我本人有在使用并维护，但仍有可能会存在漏录、断流等情况，如果介意请寻找其他更好的替代项目
- 本人并没有深入学过Python（~~但是Python是我最擅长的~~），所以本程序可能会存在很多bug或者可优化的地方，欢迎指出
- 此处推荐几个录播项目：
  1. [BililiveRecorder录播姬](https://github.com/Bililive/BililiveRecorder) - 支持多个直播间（基于C#）
  2. [B站录播机](http://live.weibo333.com) - 支持多个直播间（非开源项目）
  3. [auto-bilibili-recorder](https://github.com/valkjsaaa/auto-bilibili-recorder) - 支持自动投稿（基于Python）
  4. [DDRecorder](https://github.com/AsaChiri/DDRecorder) - 支持自动投稿与多个直播间（基于Python）
  4. [StreamerHelper](https://github.com/ZhangMingZhao1/StreamerHelper) - 支持除B站以外的其他平台，支持自动投稿与多个直播间（基于node.js）

#### 关键词
哔哩哔哩 bilibili bili bli 录播 直播 录直播 录播姬 录播机 B站 live blive 直播录制

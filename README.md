#  B站直播录播姬
- 作者: Red_lnn
- 不允许将本项目运用于非法以及违反[哔哩哔哩弹幕网用户协议](https://www.bilibili.com/blackboard/topic/activity-cn8bxPLzz.html)的用途
- 仅支持单个主播，多个主播请复制多份实例并分开单独启动
- 运行时如要停止录制并退出，请按键盘 Ctrl-C
- 如要修改录制设置，请以纯文本方式打开`config.py`文件
- 利用 FFmpeg 直接抓取主播推送的音视频流，无需打开浏览器，CPU与GPU占用率非常低
- 有新功能需求请直接提 `Pull requests`，提`issue`可能会被无视
- 建议使用 `flv` 格式进行录制（默认），以防止意外中断导致录制文件损坏，若要进行剪辑可使用 FFmpeg 转换为 mp4 文件后再倒入到剪辑软件  
```
使用 FFmpeg 转换 flv 为 mp4:
1. 直接使用命令进行转换: "ffmpeg -i {input}.flv -c copy {output}.mp4"
2. Windows系统下可双击 "flv2mp4.bat" 可将 "download" 目录下的flv文件转换为mp4文件并放在 "convert" 文件夹中
```

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

#### 关键词
哔哩哔哩 bilibili 录播 直播 录直播 录播姬 录播机 B站 live blive 直播录制

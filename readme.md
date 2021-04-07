#  B站直播录播姬
- 作者: Red_lnn
- 仅支持单个主播，多个主播请复制多份并分开单独启动
- 运行时如要停止录制并退出，请按键盘 Ctrl+C
- 如要修改录制设置，请以纯文本方式打开.py文件
- 利用ffmpeg直接抓取主播推送的流，无需打开浏览器

## 使用方式
1. 安装 Python(>=3.7) 并设置环境变量
2. 打开终端或命令行进入本脚本所在目录
3. 通过 pip 安装必须的第三方库
```
Windows: pip install -r requirements.txt
Linux: python3 -m pip install -r requirements.txt
```
4. 下载ffmpeg并设置环境变量（(下载地址)[http://www.ffmpeg.org/download.html]）
5. Windows 直接双击运行`start.bat`
6. Linux 先运行 `chmod +x start.sh` 再运行 `./start.sh`
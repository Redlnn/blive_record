#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
*---------------------------------------------------------------*
 * B站直播录播姬 By: Red_lnn
 * 项目地址: https://github.com/Redlnn/blive_record
 * 仅支持单个主播，多个主播请复制多份实例并分开单独启动
 * 运行时如要停止录制并退出，请按键盘 Ctrl-C
 * 如要修改录制设置，请以纯文本方式打开 "config.py" 文件
 * 利用 FFmpeg 直接抓取主播推送的音视频流，无需打开浏览器，CPU与GPU占用率非常低
*---------------------------------------------------------------*
"""

"""
*-------------------------------------以下为可配置项--------------------------------------*
"""
room_id = 1151716  # 要录制的B站直播间的直播间ID
segment_time = 3600  # 录播分段时长（单位：秒）
check_time = 60  # 开播检测间隔（单位：秒）
file_extensions = 'flv'  # 录制文件后缀名（文件格式）
verbose = True  # 是否打印ffmpeg输出信息到控制台
debug = False  # 是否显示并保存调试信息（优先级高于 verbose）
save_log = True  # 是否保存日志信息为文件，同一天多次启动本脚本会共用同一个日志文件，每天凌晨分割一次日志文件
"""
*-------------------------------------以上为可配置项--------------------------------------*
"""

# 几个up的直播间ID（备用）
# Red_lnn: 1857249
# 莴苣某人: 1151716

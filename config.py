#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
*------------以下为可配置项-------------*
"""
# room_id = 1151716  # 莴苣某人
# room_id = 1857249  # Red_lnn
room_id = 1151716  # 要录制的B站直播间的直播间ID
segment_time = 3600  # 录播分段时长（单位：秒）
check_time = 60  # 开播检测间隔（单位：秒）
file_extensions = 'flv'  # 录制文件后缀名（文件格式）
verbose = True  # 是否打印ffmpeg输出信息到控制台
debug = False  # 是否显示并保存调试信息（优先级高于 verbose）
save_log = True  # 是否保存日志信息为文件，同一天多次启动本脚本会共用同一个日志文件，每天凌晨分割一次日志文件
"""
*------------以上为可配置项-------------*
"""

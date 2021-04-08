#!/usr/bin/env python3
# -*- coding:utf-8 -*-

'''
*--------------------------------------*
 B站直播录播姬 By: Red_lnn
 仅支持单个主播，多个主播请复制多份并分开单独启动
 运行时如要停止录制并退出，请按键盘 Ctrl+C
 如要修改录制设置，请以纯文本方式打开.py文件
 利用ffmpeg直接抓取主播推送的流，不需要打开浏览器
*--------------------------------------*
'''

# import ffmpy3  # noqa
import logging
import os
import sys
import threading
import time
import traceback
from json import loads
from subprocess import PIPE, Popen, STDOUT

import requests
from regex import match

'''
*------------以下为可配置项-------------*
'''
# room_id = 1151716  # 莴苣某人
# room_id = 1857249  # Red_lnn
room_id = 1151716  # 要录制的B站直播的直播ID
segment_time = 3600  # 录播分段时长（单位：秒）
check_time = 120  # 开播检测间隔（单位：秒）
debug = False  # 是否打印ffmpeg输出信息到控制台
save_log = True  # 是否保存日志信息
'''
*------------以上为可配置项-------------*
'''

record_status = False

logger = logging.getLogger('Record')
fms = '[%(asctime)s %(levelname)s] %(message)s'
# datefmt = "%Y-%m-%d %H:%M:%S"
datefmt = "%H:%M:%S"

logger.setLevel(logging.DEBUG)

default_handler = logging.StreamHandler(sys.stdout)
if debug:
    default_handler.setLevel(logging.DEBUG)
else:
    default_handler.setLevel(logging.INFO)
default_handler.setFormatter(logging.Formatter(fms, datefmt=datefmt))
logger.addHandler(default_handler)

if save_log:
    file_handler = logging.FileHandler("debug.log", mode='w+', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fms, datefmt=datefmt))
    logger.addHandler(file_handler)


def get_time() -> str:
    """
    :return: 当前时间，格式1970-01-01_12-00-00
    """
    time_now = int(time.time())
    time_local = time.localtime(time_now)
    dt = time.strftime("%Y%m%d_%H%M%S", time_local)
    return dt


def record():
    global p, record_status  # noqa
    while True:
        line = p.stdout.readline().decode()
        logger.debug(line.rstrip())
        if match('video:[0-9kmgB]* audio:[0-9kmgB]* subtitle:[0-9kmgB]*', line):
            record_status = True
            break
        if p.poll() is not None:
            logger.error('ffmpeg未正常退出，请检测日志文件')
            break


def main():
    global p, room_id, record_status  # noqa
    while True:
        record_status = False
        while True:
            logger.info('------------------------------')
            logger.info(f'正在检测直播间：{room_id}')
            room_info = requests.get(f'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}')
            live_status = loads(room_info.text)['data']['live_status']
            if live_status == 1:
                break
            elif live_status == 0:
                logger.info(f'没有开播，等待{check_time}s重新开始检测')
            time.sleep(check_time)
        if not os.path.exists(os.path.join('download')):
            try:
                os.mkdir(os.path.join('download'))
            except:  # noqa
                logger.error(f'无法创建下载文件夹 ↓\n{traceback.format_exc()}')
                sys.exit(1)
        if os.path.isfile(os.path.join('download')):
            logger.error('存在与下载文件夹同名的文件')
            sys.exit(1)
        logger.info('正在直播，开始录制')
        m3u8_list = requests.get(
            f'https://api.live.bilibili.com/xlive/web-room/v1/playUrl/playUrl?cid={room_id}&platform=h5&qn=10000')
        m3u8_address = loads(m3u8_list.text)['data']['durl'][0]['url']
        command = ['ffmpeg', '-headers',
                   '"Accept: */*? Accept-Encoding: gzip, deflate, br? Accept-Language: zh,zh-TW;q=0.9,en-US;q=0.8,en;'
                   'q=0.7,zh-CN;q=0.6,ru;q=0.5? Origin: https://www.bilibili.com? '
                   'User-Agent: Mozilla/5.0 (Windows NT 10.0;Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36?"', '-i',
                   m3u8_address, '-c:v', 'copy', '-c:a', 'copy',
                   '-f', 'segment', '-segment_time', str(segment_time), '-segment_start_number', '1',
                   os.path.join('download', f'[Room_{room_id}] {get_time()}_part%03d.mp4'), '-y']
        p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=False)
        start_time = int(time.time())
        try:
            t = threading.Thread(target=record)
            t.start()
            while True:
                if record_status:
                    break
                time.sleep(30)
                if record_status:
                    break
                logger.info(f'--==>>> 已录制 {round((int(time.time()) - start_time) / 60, 2)} 分钟 <<<==--')
        except KeyboardInterrupt:
            logger.info('结束录制，等待ffmpeg退出后自动退出本程序')
            logger.info('Bye!')
            sys.exit(0)
        logger.info(f'录制结束，等待{check_time}s后重新开始检测直播间')
        time.sleep(check_time)


if __name__ == '__main__':
    logger.info('B站直播录播姬 By: Red_lnn')
    logger.info('如要停止录制并退出，请按键盘 Ctrl+C')
    logger.info('如要修改录制设置，请以纯文本方式打开.py文件')
    logger.info('准备开始录制...')
    time.sleep(0.3)
    main()

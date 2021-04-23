#!/usr/bin/env python3
# -*- coding:utf-8 -*-

"""
*--------------------------------------*
 B站直播录播姬 By: Red_lnn
 仅支持单个主播，多个主播请复制多份并分开单独启动
 运行时如要停止录制并退出，请按键盘 Ctrl+C
 如要修改录制设置，请以纯文本方式打开.py文件
 利用ffmpeg直接抓取主播推送的流，不需要打开浏览器
*--------------------------------------*
"""

# import ffmpy3  # noqa
import logging
import os
import signal
import sys
import threading
import time
import traceback
from json import loads
from logging import handlers
from subprocess import PIPE, Popen, STDOUT

import requests
from regex import match

# 导入配置
from config import *   # noqa

record_status = False  # 录制状态，True为录制中
kill_times = 0  # 尝试强制结束FFmpeg的次数

logging.addLevelName(15, 'FFmpeg')  # 自定义FFmpeg的日志级别
logger = logging.getLogger('Record')
logger.setLevel(logging.DEBUG)

fms = '[%(asctime)s %(levelname)s] %(message)s'
# datefmt = "%Y-%m-%d %H:%M:%S"
datefmt = "%H:%M:%S"

default_handler = logging.StreamHandler(sys.stdout)
if debug:
    default_handler.setLevel(logging.DEBUG)
elif verbose:
    default_handler.setLevel(15)
else:
    default_handler.setLevel(logging.INFO)
default_handler.setFormatter(logging.Formatter(fms, datefmt=datefmt))
logger.addHandler(default_handler)

if save_log:
    # file_handler = logging.FileHandler("debug.log", mode='w+', encoding='utf-8')
    if not os.path.exists(os.path.join('logs')):
        os.mkdir(os.path.join('logs'))
    file_handler = handlers.TimedRotatingFileHandler(os.path.join('logs', 'debug.log'), 'midnight', encoding='utf-8')
    if debug:
        default_handler.setLevel(logging.DEBUG)
    else:
        default_handler.setLevel(15)
    file_handler.setFormatter(logging.Formatter(fms, datefmt=datefmt))
    logger.addHandler(file_handler)


def get_timestamp() -> int:
    """
    获取当前时间戳
    """
    return int(time.time())


def get_time() -> str:
    """
    获取格式化后的时间
    """
    time_now = get_timestamp()
    time_local = time.localtime(time_now)
    dt = time.strftime("%Y%m%d_%H%M%S", time_local)
    return dt


def record():
    """
    录制过程中要执行的检测与判断
    """
    global p, record_status, last_record_time, kill_times  # noqa
    while True:
        line = p.stdout.readline().decode()
        p.stdout.flush()
        logger.log(15, line.rstrip())
        if match('video:[0-9kmgB]* audio:[0-9kmgB]* subtitle:[0-9kmgB]*', line) or 'Exiting normally' in line:
            record_status = False  # 如果FFmpeg正常结束录制则退出本循环
            break
        elif match('frame=[0-9]', line) or 'Opening' in line:
            last_record_time = get_timestamp()  # 获取最后录制的时间
        elif 'Failed to read handshake response' in line:
            time.sleep(5)  # FFmpeg读取m3u8流失败，等个5s康康会不会恢复
            continue
        time_diff = get_timestamp() - last_record_time  # 计算上次录制到目前的时间差
        if time_diff >= 65:
            logger.error('最后一次录制到目前已超65s，将尝试发送终止信号')
            logger.debug(f'间隔时间：{time_diff}s')
            kill_times += 1
            p.send_signal(signal.SIGTERM)  # 若最后一次录制到目前已超过65s，则认为FFmpeg卡死，尝试发送终止信号
            time.sleep(0.5)
            if kill_times >= 3:
                logger.critical('由于无法结束FFmpeg进程，将尝试自我了结')
                sys.exit(1)
        if 'Immediate exit requested' in line:
            logger.info('FFmpeg已被强制结束')
            break
        if p.poll() is not None:  # 如果FFmpeg已退出但没有被上一个判断和本循环第一个判断捕捉到，则当作异常退出
            logger.error('ffmpeg未正常退出，请检查日志文件！')
            record_status = False
            break


def main():
    global p, room_id, record_status, last_record_time, kill_times  # noqa
    while True:
        record_status = False
        while True:
            logger.info('------------------------------')
            logger.info(f'正在检测直播间：{room_id}')
            try:
                room_info = requests.get(f'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}',
                                         timeout=5)
            except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
                logger.error(f'无法连接至B站API，等待{check_time}s后重新开始检测')
                time.sleep(check_time)
                continue
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
        logger.info('正在直播，准备开始录制')
        m3u8_list = requests.get(
            f'https://api.live.bilibili.com/xlive/web-room/v1/playUrl/playUrl?cid={room_id}&platform=h5&qn=10000')
        m3u8_address = loads(m3u8_list.text)['data']['durl'][0]['url']
        # 下面命令中的timeout单位为微秒，10000000us为10s（https://www.cnblogs.com/zhifa/p/12345376.html）
        command = ['ffmpeg', '-rw_timeout', '10000000', '-timeout', '10000000', '-listen_timeout', '10000000',
                   '-headers',
                   '"Accept: */*? Accept-Encoding: gzip, deflate, br? Accept-Language: zh,zh-TW;q=0.9,en-US;q=0.8,en;'
                   f'q=0.7,zh-CN;q=0.6,ru;q=0.5? Origin: https://live.bilibili.com/{room_id}? '
                   'User-Agent: Mozilla/5.0 (Windows NT 10.0;Win64; x64) '
                   'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.106 Safari/537.36?"', '-i',
                   m3u8_address, '-c:v', 'copy', '-c:a', 'copy', '-bsf:a', 'aac_adtstoasc',
                   '-f', 'segment', '-segment_time', str(segment_time), '-segment_start_number', '1',
                   os.path.join('download', f'[{room_id}]_{get_time()}_part%03d.{file_extensions}'), '-y']
        if debug:
            logger.debug('FFmpeg命令如下 ↓')
            command_str = ''
            for _ in command:
                command_str += _
            logger.debug(command_str)
        p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=False)
        record_status = True
        start_time = last_record_time = get_timestamp()
        try:
            t = threading.Thread(target=record)
            t.start()
            while True:
                if not record_status:
                    break
                if verbose or debug:
                    time.sleep(20)
                    logger.info(f'--==>>> 已录制 {round((get_timestamp() - start_time) / 60, 2)} 分钟 <<<==--')
                else:
                    time.sleep(60)
                    logger.info(f'--==>>> 已录制 {int((get_timestamp() - start_time) / 60)} 分钟 <<<==--')
                if not record_status:
                    break
        except KeyboardInterrupt:
            # p.send_signal(signal.CTRL_C_EVENT)
            logger.info('停止录制，等待ffmpeg退出后本程序会自动退出')
            logger.info('若长时间卡住，请再次按下ctrl+c (可能会损坏视频文件)')
            logger.info('Bye!')
            sys.exit(0)
        kill_times = 0
        logger.info('FFmpeg已退出，重新开始检测直播间')
        # time.sleep(check_time)


if __name__ == '__main__':
    logger.info('B站直播录播姬 By: Red_lnn')
    logger.info('如要停止录制并退出，请按键盘 Ctrl+C')
    logger.info('如要修改录制设置，请以纯文本方式打开.py文件')
    logger.info('准备开始录制...')
    time.sleep(0.3)
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Bye!')
        sys.exit(0)

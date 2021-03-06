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
import urllib3
from colorlog import ColoredFormatter
from regex import match

# 导入配置
from config import (check_time, debug, file_extensions, room_id, save_log, segment_time, verbose)  # noqa
from windowsInhibitor import WindowsInhibitor

# 提前定义要用到的变量
last_record_time = 0  # 上次录制成功的时间
last_stop_time = 0  # 上次停止录制的时间
stop_times = 0  # 退出次数（仅在异常退出时增加）
record_status = False  # 录制状态，True为录制中
exit_in_seconds = False  # FFmpeg是否是在短时间内异常退出
os_sleep = None

logging.addLevelName(15, 'FFmpeg')  # 自定义FFmpeg的日志级别
logging.addLevelName(31, 'FFmpeg WARNING')
logging.addLevelName(41, 'FFmpeg ERROR')

logging.addLevelName(21, 'NOTICE')  # 自定义部分通知的级别

logger = logging.getLogger('Record')
logger.setLevel(logging.DEBUG)

if debug:
    console_fmt = "%(log_color)s[%(asctime)s,%(msecs)03d %(levelname)s] %(message)s"
    file_fmt = "[%(asctime)s,%(msecs)03d %(levelname)s] %(message)s"
else:
    console_fmt = "%(log_color)s[%(asctime)s %(levelname)s] %(message)s"
    file_fmt = "[%(asctime)s %(levelname)s] %(message)s"

# 设置控制台log输出
console_handler = logging.StreamHandler(sys.stdout)
if debug:
    console_handler.setLevel(logging.DEBUG)
elif verbose:
    console_handler.setLevel(15)
else:
    console_handler.setLevel(logging.INFO)
console_handler.setFormatter(ColoredFormatter(console_fmt,
                                              datefmt="%H:%M:%S",
                                              reset=True,
                                              log_colors={
                                                  'DEBUG': 'cyan',
                                                  'INFO': 'bold_white',
                                                  'WARNING': 'yellow',
                                                  'ERROR': 'red',
                                                  'CRITICAL': 'red,bg_white',
                                                  'FFmpeg': 'white',
                                                  'FFmpeg WARNING': 'yellow',
                                                  'FFmpeg ERROR': 'red',
                                                  'NOTICE': 'bold_green'
                                              },
                                              secondary_log_colors={},
                                              style='%'))
logger.addHandler(console_handler)

# 设置log文件输出
if save_log:
    if not os.path.exists(os.path.join('logs')):
        os.mkdir(os.path.join('logs'))
    file_handler = handlers.TimedRotatingFileHandler(os.path.join('logs', 'debug.log'), 'midnight', encoding='utf-8')
    if debug:
        file_handler.setLevel(logging.DEBUG)
    else:
        file_handler.setLevel(15)
    file_handler.setFormatter(logging.Formatter(file_fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)


def get_timestamp() -> int:
    """
    获取当前时间戳
    """
    return int(time.time())


def record_control():
    """
    录制过程中要执行的检测与判断
    """
    global exit_in_seconds, last_record_time, last_stop_time, ffmpeg_process, record_status, start_time, stop_times
    while True:
        line = ffmpeg_process.stdout.readline().decode().strip()
        ffmpeg_process.stdout.flush()

        if line != '':
            line_lower = line.lower()
            if 'warn' in line_lower:
                logger.log(31, line)
            elif 'error' in line_lower or 'fail' in line_lower or 'fatal' in line_lower:
                logger.log(41, line)
            else:
                logger.log(15, line)

            if match('video:[0-9kmgB]* audio:[0-9kmgB]* subtitle:[0-9kmgB]*', line) or 'Exiting normally' in line:
                last_stop_time = get_timestamp()  # 获取录制结束的时间
                stop_times += 1
                record_status = False  # 如果FFmpeg正常结束录制则退出本循环
                ffmpeg_process.wait()
                break
            elif match('frame=[0-9]', line) or 'Opening' in line:
                last_record_time = get_timestamp()  # 获取最后录制的时间
            elif 'Failed to read handshake response' in line:
                # FFmpeg读取m3u8流失败，等个5s康康会不会恢复，如果一直失败，FFmpeg会自行退出并被下方的`ffmpeg_process.poll() is not None`捕捉
                # 此处假设`ffmpeg_process.stdout.flush()`会清除缓冲区，则5s后line应该为空而跳过此处的判断，并在65s后被下方超时的判断捕捉尝试结束FFmpeg
                logger.warning('FFmpeg读取m3u8流失败，请留意')
                time.sleep(5)
                continue
            elif 'Immediate exit requested' in line:
                logger.warning('FFmpeg已被强制停止，请检查日志与录像文件！')
                last_stop_time = get_timestamp()  # 获取录制结束的时间
                stop_times += 1
                record_status = False
                ffmpeg_process.wait()
                break

        if (get_timestamp() - last_record_time) >= 65:
            logger.warning('最后一次录制到目前已超65s，将尝试发送终止信号并持续等待FFmpeg退出')
            if ffmpeg_process.poll() is None:
                ffmpeg_process.send_signal(signal.CTRL_C_EVENT)  # 若最后一次录制到目前已超过65s，则认为FFmpeg卡死，尝试发送终止信号
                time.sleep(10)
            if ffmpeg_process.poll() is None:
                ffmpeg_process.send_signal(signal.SIGTERM)
                time.sleep(1)
            if ffmpeg_process.poll() is None:
                ffmpeg_process.send_signal(signal.SIGKILL)
                time.sleep(1)
            if ffmpeg_process.poll() is None:
                ffmpeg_process.kill()
                ffmpeg_process.wait()
            logger.warning('FFmpeg已被强制停止，请检查日志与录像文件！')
            last_stop_time = get_timestamp()  # 获取录制结束的时间
            stop_times += 1
            record_status = False
            break

        exit_code = ffmpeg_process.poll()
        if exit_code is not None and exit_code != 0:  # 如果FFmpeg已退出但没有被上面的if捕捉到，则当作异常退出
            logger.warning('FFmpeg未正常退出，请检查日志与录像文件！')
            last_stop_time = get_timestamp()  # 获取录制结束的时间
            stop_times += 1
            record_status = False
            if (last_stop_time - start_time) <= 10:
                exit_in_seconds = True
            ffmpeg_process.wait()
            break
        elif exit_code == 0:  # FFmpeg正常退出
            last_stop_time = get_timestamp()  # 获取录制结束的时间
            stop_times += 1
            record_status = False  # 如果FFmpeg正常结束录制则退出本循环
            ffmpeg_process.wait()
            break


def time_countdown(sec: int):
    """
    倒数计时+录制状态判断

    :param sec: 要倒数的时长（秒）
    """
    time.sleep(sec)


def main():
    global exit_in_seconds, last_record_time, last_stop_time, os_sleep, ffmpeg_process, record_status, room_id, start_time, stop_times
    if os.name == 'nt':
        os_sleep = WindowsInhibitor()
        os_sleep.inhibit()
    while True:
        record_status = False
        while True:
            logger.info('------------------------------')
            logger.info(f'正在检测直播间 {room_id} 是否开播')
            try:
                room_info = requests.get(f'https://api.live.bilibili.com/room/v1/Room/get_info?room_id={room_id}',
                                         timeout=(5, 5))
            except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
                logger.error(f'尝试连接至B站API时网络超时，请检查网络连接，将在等待{check_time}s后重新检测')
                time.sleep(check_time)
                continue
            except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError,
                    requests.exceptions.ConnectionError):
                logger.error(f'无法连接至B站API，请检查网络连接，将在等待{check_time}s后重新检测')
                time.sleep(check_time)
                continue
            live_status = loads(room_info.text)['data']['live_status']
            real_room_id = loads(room_info.text)['data']['room_id']
            if real_room_id != room_id:
                logger.info(f'直播间 {room_id} 的真实直播间ID为： {real_room_id}')

            if live_status == 1:
                break
            elif live_status == 0:
                logger.info(f'直播间 {room_id} 没有开播，将在等待 {check_time} s后重新检测')
            time.sleep(check_time)

        if not os.path.exists(os.path.join('download')):
            try:
                os.mkdir(os.path.join('download'))
            except:  # noqa
                logger.error(f'无法创建下载文件夹 ↓\n{traceback.format_exc()}')
                sys.exit(1)
        if os.path.isfile(os.path.join('download')):
            logger.error('存在与下载文件夹同名的文件，请删除后重试')
            sys.exit(1)

        logger.info(f'检测到直播间 {room_id} 正在直播，开始录制')

        # 如果上次录制停止到本次开始录制的时间差小于30s，则认为上次录制时FFmpeg可能异常断开或停止
        if 0 < (get_timestamp() - last_stop_time) < 30:
            logger.warning('>>> 检测到上次录制时FFmpeg可能异常断开或停止，请检查录制文件是否存在问题')
        if (get_timestamp() - last_stop_time) > 60:
            stop_times = 0
        last_stop_time = 0

        try:
            m3u8_list = requests.get(f'https://api.live.bilibili.com/room/v1/Room/playUrl?cid={real_room_id}'
                                     '&platform=h5&qn=10000', timeout=(5, 5))
        except (requests.exceptions.ReadTimeout, requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            logger.error(f'从B站API获取直播媒体流链接时网络超时，请检查网络连接，将在等待{check_time}s后重新开始检测')
            time.sleep(check_time)
            continue
        except (urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError,
                requests.exceptions.ConnectionError):
            logger.error(f'无法连接至B站API获取以直播媒体流链接，请检查网络连接，将在等待{check_time}s后重新开始检测')
            time.sleep(check_time)
            continue
        m3u8_address = loads(m3u8_list.text)['data']['durl'][0]['url']  # noqa
        # 下面命令中的timeout单位为微秒，5000000us为5s（https://www.cnblogs.com/zhifa/p/12345376.html）
        if debug:
            command = ['ffmpeg', '-loglevel', 'repeat+level+debug']
        else:
            command = ['ffmpeg', '-loglevel', '+level+info']
        command += ['-rw_timeout', '5000000', '-timeout', '5000000', '-listen_timeout', '5000000',
                    '-headers', '"Accept: */*? Accept-Encoding: gzip, deflate, br? Accept-Language: zh;q=0.9,zh-CN;'
                                f'q=0.8,en-US;q=0.7,en;? Origin: https://live.bilibili.com/{room_id}? '
                                'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                                '(KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.66 Edge/18.19041"\r\n',
                    '-i', m3u8_address, '-c', 'copy', '-bsf:a', 'aac_adtstoasc', '-f', 'segment',
                    '-segment_time', str(segment_time), '-strftime', '1',
                    os.path.join('download', f'{room_id}_%Y%m%d_%H%M%S.{file_extensions}'), '-y']
        if debug:
            logger.debug('FFmpeg命令如下 ↓')
            command_str = ''.join(f'{_} ' for _ in command)
            logger.debug(command_str.rstrip())
        ffmpeg_process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=False)
        start_time = last_record_time = get_timestamp()
        record_status = True
        try:
            record_control_thread = threading.Thread(target=record_control)
            record_control_thread.setDaemon(True)
            record_control_thread.start()
            while True:
                if debug:
                    time_countdown_thread = threading.Thread(target=time_countdown, args=[5])
                elif verbose:
                    time_countdown_thread = threading.Thread(target=time_countdown, args=[20])
                else:
                    time_countdown_thread = threading.Thread(target=time_countdown, args=[40])
                time_countdown_thread.setDaemon(True)
                time_countdown_thread.start()
                # 使用子线程的方法计时会导致下面的计时出现误差
                # 之所以使用子线程计时，是因为要在倒计时的同时判断录制状态（就下面这个while循环）
                # 如果单纯使用time.sleep()来计时，可能会导致FFmpeg在sleep时退出后出现程序卡死的假象
                while record_status and not (
                    record_status and not time_countdown_thread.is_alive()
                ):
                    # 暴力解决CPU占用高的问题，也会导致下面的计时有误差。也许时间短一点也行，不过没必要这么短
                    time.sleep(1)
                if not record_status:
                    break
                # 上面两处注释提到的问题会导致这里出现一点误差（大概多十几到几百毫秒？），没有解决的想法和思路
                # 注：计时误差不会对录制产生影响，此处显示的时间也是正确的，误差仅指计时不是整秒而已
                logger.log(21, f'>>> 本次已录制 {time.strftime("%H:%M:%S", time.gmtime(get_timestamp() - start_time))}')
                if stop_times > 0:
                    logger.warning(f'>>> 累计已异常断开 {stop_times} 次')
            record_control_thread.join()
        except KeyboardInterrupt:
            # ffmpeg_process.send_signal(signal.CTRL_C_EVENT)  # 貌似FFmpeg可以捕捉到控制台中按下的ctrl-c，因此注释掉
            logger.log(21, '正在停止录制并等待FFmpeg退出...')
            logger.log(21, '若长时间卡住，请尝试再次按下ctrl-c (可能会损坏视频文件)')
            ffmpeg_process.wait()  # 等待FFmpeg退出
            logger.info('FFmpeg已退出，程序即将退出')
            if os_sleep:
                os_sleep.uninhibit()
            logger.info('Bye!')
            sys.exit(0)

        if exit_in_seconds:
            exit_in_seconds = False
            logger.warning(f'因FFmpeg在短时间内异常退出，为防止反复退出刷屏，将在等待{check_time}s后再检测')
            time.sleep(check_time)
        else:
            logger.info('FFmpeg已退出，重新开始检测直播间')
        # time.sleep(check_time)


if __name__ == '__main__':
    logger.info('B站直播录播姬 By: Red_lnn')
    logger.info('如要停止录制并退出，请按键盘 Ctrl+C')
    logger.info('如要修改录制设置，请以纯文本方式打开.py文件')
    logger.info('准备开始录制...')
    try:
        main()
    except KeyboardInterrupt:
        logger.info('Bye!')
        sys.exit(0)

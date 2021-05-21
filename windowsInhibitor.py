#!/usr/bin/env python3
# -*- coding:utf-8 -*-

class WindowsInhibitor:
    """
    阻止Windows进入睡眠/休眠状态

    code from: https://github.com/h3llrais3r/Deluge-PreventSuspendPlus/blob/master/deluge_preventsuspendplus/core.py#L116

    https://docs.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate
    """
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001

    def __init__(self):
        pass

    def inhibit(self):  # noqa
        import ctypes
        # log.info('Inhibit (prevent) suspend mode')
        ctypes.windll.kernel32.SetThreadExecutionState(
            WindowsInhibitor.ES_CONTINUOUS | WindowsInhibitor.ES_SYSTEM_REQUIRED)

    def uninhibit(self):  # noqa
        import ctypes
        # log.info('Uninhibit (allow) suspend mode')
        ctypes.windll.kernel32.SetThreadExecutionState(WindowsInhibitor.ES_CONTINUOUS)


__all__ = [WindowsInhibitor]

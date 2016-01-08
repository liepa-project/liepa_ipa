# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8

import os
import errno
import win32api
import win32con
import pythoncom
import win32process
import win32security
import win32com.client
from win32com.shell import shell, shellcon
from pywinauto import win32functions, win32defines

pythoncom.CoInitialize()

def COMDispatch(progid):
    return win32com.client.Dispatch(progid)

def GetAssocExe(aspect):
    """ Get association (file extension or protocol) executable """
    # PyIQueryAssociations 
    assoc = shell.AssocCreate()
    # 0 - ASSOCF_NONE
    assoc.Init(0, aspect)
    return assoc.GetString(0, shellcon.ASSOCSTR_EXECUTABLE)
    

def GetProcessInfo(pid):
    "WMI method; a little bit slow: tens of ms per call"
    WMI = win32com.client.GetObject('winmgmts:')
    #processes = WMI.InstancesOf('Win32_Process')
    process = WMI.ExecQuery(
        'SELECT * FROM Win32_Process WHERE ProcessId = {0}'.format(pid))
    info = {p.Name: p.Value for p in process.ItemIndex(0).Properties_}

    owner = process.ItemIndex(0).ExecMethod_('GetOwner')
    info.update({p.Name: p.Value
                 for p in owner.Properties_
                 if p.Name in ('User', 'Domain')})

    owner_sid = process.ItemIndex(0).ExecMethod_('GetOwnerSid')
    info.update({p.Name: p.Value
                 for p in owner_sid.Properties_
                 if p.Name in ('Sid')})
    return info    

def GetUserName(sid):
    win32security.LookupAccountSid(None, sid)[0]
    
def GetUserSID(user):
    win32security.LookupAccountName(None, user)[0]

def GetProcessUser(pid):
    return GetUserName(GetProcessSID(pid))

def GetProcessSID(pid):
    ph = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, 0, pid)
    th = win32security.OpenProcessToken(ph, win32security.TOKEN_QUERY)
    return win32security.GetTokenInformation(th, win32security.TokenUser)[0]

def GetWindowPID(hwnd):
    return win32process.GetWindowThreadProcessId(hwnd)[1]

def SetForegroundWindow(window):
    if window.HasStyle(win32defines.WS_MINIMIZE):
        win32functions.ShowWindow(window.handle, win32defines.SW_RESTORE)
    win32functions.SetForegroundWindow(window.handle)


def get_dir(_file):
    return os.path.abspath(os.path.dirname(_file))
    
def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

def make_file_dirs(path):
    makedirs(os.path.dirname(path))


# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8
import time
import logger
import subprocess

import pythoncom
from utils import GetAssocExe, GetWindowPID, SetForegroundWindow, COMDispatch

import pywinauto.application

SUPPORTED_BROWSERS = ('iexplore', 'firefox', 'chrome', 'opera', 'seamonkey')


log = logger.get(__name__)


def GetDefaultBrowser():
    try:
        exe = GetAssocExe('http')
    except Exception as e:
        log.error("Failed to get http protocol association: '%s'. Choosing IE.", e)
        return InternetExplorer()

    #exe = r'C:\Documents and Settings\Laimis\Desktop\FirefoxPortable\FirefoxPortable.exe'
    #exe = r'C:\Documents and Settings\Laimis\Desktop\GoogleChromePortable\GoogleChromePortable.exe'
    #exe = r'C:\Documents and Settings\Laimis\Desktop\OperaPortable\OperaPortable.exe'
    #exe = r'C:\Documents and Settings\Laimis\AppData\Local\SeaMonkey\seamonkey.exe' 

    for browser in SUPPORTED_BROWSERS:
        if browser in exe.lower():
            if browser == 'iexplore':
                return InternetExplorer()
            else:
                return BaseBrowser(path=exe)

    log.error("Unsupported browser: %s. Choosing IE.", exe)    
    return InternetExplorer()
     


class InternetExplorer():

    class BrowserNavConstants():
        """
        InternetExplorer.Navigate() Flags constants (BrowserNavConstants):
        https://msdn.microsoft.com/en-us/library/dd565688%28v=vs.85%29.aspx
        ----------------------------------------------------------------------
        navOpenInNewWindow
            Open the resource or file in a new window.
        navNoHistory
            Do not add the resource or file to the history list. The new page
            replaces the current page in the list.
        navNoReadFromCache
            Not implemented.
        navNoWriteToCache
            Not implemented.
        navAllowAutosearch
            If the navigation fails, the autosearch functionality attempts to
            navigate common root domains (.com, .edu, and so on). If this also
            fails, the URL is passed to a search engine.
        navBrowserBar
            Causes the current Explorer Bar to navigate to the given item, if
            possible. 
        navHyperlink
            Microsoft Internet Explorer 6 for Windows XP Service Pack 2 (SP2)
            and later. If the navigation fails when a hyperlink is being
            followed, this constant specifies that the resource should then be
            bound to the moniker using the BINDF_HYPERLINK flag.
        navEnforceRestricted
            Internet Explorer 6 for Windows XP SP2 and later. Force the URL
            into the restricted zone.
        navNewWindowsManaged
            Internet Explorer 6 for Windows XP SP2 and later. Use the default
            Popup Manager to block pop-up windows. 
        navUntrustedForDownload
            Internet Explorer 6 for Windows XP SP2 and later. Block files that
            normally trigger a file download dialog box. 
        navTrustedForActiveX
            Internet Explorer 6 for Windows XP SP2 and later. Prompt for the
            installation of Microsoft ActiveX controls. 
        navOpenInNewTab
            Windows Internet Explorer 7. Open the resource or file in a new
            tab. Allow the destination window to come to the foreground, if
            necessary. 
        navOpenInBackgroundTab
            Internet Explorer 7. Open the resource or file in a new background
            tab; the currently active window and/or tab remains open on top. 
        navKeepWordWheelText
            Internet Explorer 7. Maintain state for dynamic navigation based on
            the filter string entered in the search band text box (wordwheel).
            Restore the wordwheel text when the navigation completes. 
        navVirtualTab
            Internet Explorer 8. Open the resource as a replacement for the
            current or target tab. The existing tab is closed while the new tab
            takes its place in the tab bar and replaces it in the tab group, if
            any. Browser history is copied forward to the new tab. On Windows
            Vista, this flag is implied if the navigation would cross integrity
            levels and navOpenInNewTab, navOpenInBackgroundTab, or
            navOpenInNewWindow is not specified. 
        navBlockRedirectsXDomain
            Internet Explorer 8. Block cross-domain redirect requests. The
            navigation triggers the RedirectXDomainBlocked event if blocked. 
        navOpenNewForegroundTab
            Internet Explorer 8 and later. Open the resource in a new tab that
            becomes the foreground tab.
        """
        navOpenInNewWindow = 1
        navNoHistory = 2
        navNoReadFromCache = 4
        navNoWriteToCache = 8
        navAllowAutosearch = 16
        navBrowserBar = 32
        navHyperlink = 64
        navEnforceRestricted = 128
        navNewWindowsManaged = 256
        navUntrustedForDownload = 512
        navTrustedForActiveX = 1024
        navOpenInNewTab = 2048
        navOpenInBackgroundTab = 4096
        navKeepWordWheelText = 8192
        navVirtualTab = 16384
        navBlockRedirectsXDomain = 32768
        navOpenNewForegroundTab = 65536
    
    def __init__(self, *args, **kwargs):
        self.reinit()

    def reinit(self):
        self._ie = self._get_ie()
        self._ie.Visible = True

        self._pywin = pywinauto.application.Application()
        self._pywin.connect_(handle=self._ie.HWND)
        self._window = self._pywin.window_(handle=self._ie.HWND)

        # XXX: Windows 7+ steal focus workaround (press Alt):
        # http://msdn.microsoft.com/en-us/library/ms633532%28v=vs.85%29.aspx
        # The system automatically enables calls to SetForegroundWindow if 
        # the user presses the ALT key[..] 
        self._window.TypeKeys('%+')


    def _get_ie(self):
        shell = COMDispatch("Shell.Application")

        log.debug("shell.Windows().Count: %i", shell.Windows().Count)
        for i in range(shell.Windows().Count):
            # XXX: shell.Windows() returns all IE instances.
            # (should attach to IE instance of the current user only)
            try:
                w = shell.Windows().Item(i)
            except pythoncom.com_error as e:
                log.error("COM error: %s; skipping shell window.", e)
                continue

            if w is None:
                continue

            # XXX: IWebBrowser2 for Windows Explorer (and possibly in other cases)
            # returns window.HWND of unicode type, not int.
            hwnd = int(w.HWND)
            pid = GetWindowPID(hwnd)
            log.debug("Shell window %i: hwnd: %i, pid: %i, ['%s', '%s']",
                      i+1, hwnd, pid, w, w.FullName)
            if 'iexplore.exe' in w.FullName.lower():
                log.debug("Attaching to IE instance (pid): %i.", pid)
                return w

        log.debug("Launching new IE COM.")
        try:
            ie = COMDispatch("InternetExplorer.Application")
            log.debug("IE hwnd: %i, pid: %i", ie.HWND, GetWindowPID(ie.HWND))
            return ie
        except Exception as e:
            log.error("Failed to dispatch IE COM: %s", e)
            raise
        
    def set_foreground(self):
        SetForegroundWindow(self._window)
        
    def windows(self):
        """ Debug sub """
        for w in self._pywin.windows_():
            print w.handle, w.GetProperties()
        
    def _open(self, url, flag=0, autoraise=True):
        _flags = {
            1: self.BrowserNavConstants.navOpenInNewWindow,
            2: self.BrowserNavConstants.navOpenInNewTab,
            3: self.BrowserNavConstants.navVirtualTab
            }
        if flag in _flags:
            flags = _flags[flag]
        else:
            flags = None
            
        try:
            self._ie.Navigate(url, flags)
        except Exception as e:
            log.error("Can't navigate %s", e)
            return

        self.set_foreground()

    def open_new_window(self, url):
        return self._open(url, 1)

    def open_new_tab(self, url):
        return self._open(url, 2)

    def open_current_tab(self, url):
        return self._open(url, 3)
    
    def __del__(self):
        if self._ie:
            #self._ie.Quit()
            pass
            

class BaseBrowser():
    """
    Base commaptible browser class.
    As of 2015, Mozilla Firefox, Seamonkey, Google Chromium, Opera
    (and portable versions) are fully compatible in terms of command
    line option support: --new-tab, --new-window
    """
    def __init__(self, *args, **kwargs):
        self._pywin = pywinauto.application.Application()
        self._exe = kwargs['path']

    def _open(self, options=None, url=None):
        try:
            p = subprocess.Popen([self._exe, options, url])
            return p.poll()
        except OSError as e:
            log.error('Failed to open: %s', e)
            return False

    def open_new_window(self, url):
        return self._open('--new-window', url)

    def open_new_tab(self, url):
        return self._open('--new-tab', url)

    def open_current_tab(self, url):
        log.warn("Can't open url in the current tab.")
        return self._open(url=url)

        

#moz.TypeKeys('%+')
#app = application.Application()

#moz = app.connect_(path = 'seamonkey.exe')
#ie = InternetExplorer()
#ie.windows()
#ie.open_new_tab('delfi.lt')
#del ie
#browser = GetDefaultBrowser()

    

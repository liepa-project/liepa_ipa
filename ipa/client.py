#!env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8
import os
import sys
import json
import subprocess
import utils, logger, browser

from twisted.python import log
from twisted.internet import tksupport, reactor
from twisted.internet.protocol import ReconnectingClientFactory

from autobahn.websocket.protocol import parseWsUrl
from autobahn.twisted.websocket import \
     WebSocketClientFactory, WebSocketClientProtocol, connectWS

from gui import ipa


log = logger.get(__name__)


class LiepaRootClientProtocol(WebSocketClientProtocol):

    def onOpen(self):
        self.recording = False
        gui.register(self)
        gui.chkRecord.configure(state='normal')
 
    def onClose(self, wasClean, code, reason):
        #log.debug("Connection close: %s", reason)
        pass

    def onMessage(self, payload, isBinary):
        if not isBinary:
            log.debug("Text message received: %s", payload.decode('utf-8'))
            msg = json.loads(payload)
            event = msg.keys()[0].lower()
            data = msg[event]
            
            if event == 'recognition':
                text = data['text']
                command = data['command']
                cmd_arg = data['cmd-arg']

                log.debug("text: %s, command: %s, cmd-arg: %s", text, command, cmd_arg)
                reactor.callInThread(gui.evt_Recognition, data)

                if command == 'cmd-open-url':
                    global urls
                    url = urls[cmd_arg] 
                    browser.open_new_tab(url)
                else:
                    log.warn("Unsupported command yet: %s", command)

            elif event == 'recognizer':
                reactor.callInThread(gui.evt_RecognizerState, data['status'])
                #reactor.callFromThread(gui.evt_RecognizerState, data['status'])
                #gui.evt_RecognizerState(data['status'])

    def startRecognizer(self, loop=False):
        log.debug("starting recognizer; loop: %s", loop)
        msg = {'start-recognizer': {'loop': bool(loop) }}
        self.sendMessage(json.dumps(msg))
        self.recording = True

    def stopRecognizer(self):
        log.debug("stopping recognizer.")
        self.sendMessage('{"stop-recognizer": {}}')
        self.recording = False


        
class LiepaRootClientFactory(WebSocketClientFactory, ReconnectingClientFactory):

    ReconnectingClientFactory.maxDelay = 1
    ReconnectingClientFactory.initialDelay = 3
    ReconnectingClientFactory.maxRetries = 5
    
    def clientConnectionLost(self, connector, reason):
        log.error("Lost connection: %s. Terminating.", reason)
        terminate()

    def clientConnectionFailed(self, connector, reason):
        log.error("Failed connecting: %s. Retrying.", reason)
        self.retry(connector)


def start_server():
    root = utils.get_dir(sys.executable)
    py_cmd = os.path.join(root, 'pythonw.exe') 
    server_py = os.path.join(root, 'Lib', 'site-packages', 'liepa_root', 'server.py')
    
    return subprocess.Popen([py_cmd, server_py],
                            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

def load_urls():
    global urls

    with open(os.path.join(utils.get_dir(__file__), 'config', 'ipa.urls'), 'r') as f:
        urls = json.load(f)

def terminate():
    if server.poll() is None:
        server.terminate()
    if reactor.running:
        reactor.stop()

def on_gui_close():
    terminate()

if __name__ == '__main__':

    global server, browser, root, gui
	
    server = start_server()
    load_urls()

    browser = browser.GetDefaultBrowser()

    root, gui = ipa.create_GUI()
    root.protocol("WM_DELETE_WINDOW", on_gui_close)
    tksupport.install(root)
    
    # default url
    wsurl = "ws://localhost:9000/ipa?master=1"

    if len(sys.argv) > 1:
        wsurl = sys.argv[1]

    parseWsUrl(wsurl)

    factory = LiepaRootClientFactory(wsurl)
    factory.protocol = LiepaRootClientProtocol
    connectWS(factory)

    reactor.run()

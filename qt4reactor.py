# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.


"""
This module provides support for Twisted to be driven by the Qt mainloop.

In order to use this support, simply do the following::

    |  import qt4reactor
    |  qt4reactor.install()

Then use twisted.internet APIs as usual.  The other methods here are not
intended to be called directly.

API Stability: stable

Maintainer: U{Glenn H Tarbox, PhD<mailto:glenn@tarbox.org>}

Previous maintainer: U{Itamar Shtull-Trauring<mailto:twisted@itamarst.org>}
Original port to QT4: U{Gabe Rudy<mailto:rudy@goldenhelix.com>}
Subsequent port by therve
"""

__all__ = ['install']


import sys, time

from zope.interface import implements

from PyQt4.QtCore import QSocketNotifier, QObject, SIGNAL, QTimer, QCoreApplication
from PyQt4.QtCore import QEventLoop

from twisted.internet.interfaces import IReactorFDSet
from twisted.python import log
from twisted.internet.posixbase import PosixReactorBase

class TwistedSocketNotifier(QSocketNotifier):
    """
    Connection between an fd event and reader/writer callbacks.
    """

    def __init__(self, reactor, watcher, type):
        QSocketNotifier.__init__(self, watcher.fileno(), type)
        self.reactor = reactor
        self.watcher = watcher
        self.fn = None
        if type == QSocketNotifier.Read:
            self.fn = self.read
        elif type == QSocketNotifier.Write:
            self.fn = self.write
        QObject.connect(self, SIGNAL("activated(int)"), self.fn)


    def shutdown(self):
        QObject.disconnect(self, SIGNAL("activated(int)"), self.fn)
        self.setEnabled(False)
        self.fn = self.watcher = None


    def read(self, sock):
        w = self.watcher
        #self.setEnabled(False)    # ??? do I need this?            
        def _read():
            why = None
            try:
                why = w.doRead()
            except:
                log.err()
                why = sys.exc_info()[1]
            if why:
                self.reactor._disconnectSelectable(w, why, True)
            elif self.watcher:
                pass
                #self.setEnabled(True)
        log.callWithLogger(w, _read)
        self.reactor.qApp.emit(SIGNAL("twistedEvent"),'c')

    def write(self, sock):
        w = self.watcher
        self.setEnabled(False)
        def _write():
            why = None
            try:
                why = w.doWrite()
            except:
                log.err()
                why = sys.exc_info()[1]
            if why:
                self.reactor._disconnectSelectable(w, why, False)
            elif self.watcher:
                self.setEnabled(True)
        log.callWithLogger(w, _write)
        self.reactor.qApp.emit(SIGNAL("twistedEvent"),'c')

class fakeApplication(QEventLoop):
    def __init__(self):
        QEventLoop.__init__(self)
        
    def exec_(self):
        QEventLoop.exec_(self)
        
class QTReactor(PosixReactorBase):
    """
    Qt based reactor.
    """
    implements(IReactorFDSet)

    _timer = None

    def __init__(self):
        self._reads = {}
        self._writes = {}
        self._timer=QTimer()
        self._timer.setSingleShot(True)
        if QCoreApplication.startingUp():
            self.qApp=QCoreApplication([])
            self._ownApp=True
        else:
            self.qApp = QCoreApplication.instance()
            self._ownApp=False
        self._blockApp = None
        self._readWriteQ=[]
        
        """ some debugging instrumentation """
        self._doSomethingCount=0
        
        PosixReactorBase.__init__(self)

    def addReader(self, reader):
        if not reader in self._reads:
            self._reads[reader] = TwistedSocketNotifier(self, reader,
                                                       QSocketNotifier.Read)


    def addWriter(self, writer):
        if not writer in self._writes:
            self._writes[writer] = TwistedSocketNotifier(self, writer,
                                                        QSocketNotifier.Write)


    def removeReader(self, reader):
        if reader in self._reads:
            self._reads[reader].shutdown()
            del self._reads[reader]


    def removeWriter(self, writer):
        if writer in self._writes:
            self._writes[writer].shutdown()
            del self._writes[writer]


    def removeAll(self):
        return self._removeAll(self._reads, self._writes)


    def getReaders(self):
        return self._reads.keys()


    def getWriters(self):
        return self._writes.keys()
    
    def callLater(self,howlong, *args, **kargs):
        rval = super(QTReactor,self).callLater(howlong, *args, **kargs)
        self.qApp.emit(SIGNAL("twistedEvent"),'c')
        return rval
    
    def crash(self):
        super(QTReactor,self).crash()
        
    def cleanup(self):
        self.iterate(0.1) # cleanup pending events?
        self.running=False
        self.qApp.emit(SIGNAL("twistedEvent"),'shutdown')

    def iterate(self,delay=0.0):
        endTime = delay + time.time()
        self._timer.start(0) # locked?
        self.qApp.processEvents() # gotta do at least one
        while True:
            t = endTime - time.time()
            if t <= 0.0: return
            self.qApp.processEvents(QEventLoop.AllEvents | 
                              QEventLoop.WaitForMoreEvents,t*1010)
            
    def addReadWrite(self,t):
        self._readWriteQ.append(t)
        self.qApp.emit(SIGNAL("twistedEvent"),'fileIO')
        
    def runReturn(self, installSignalHandlers=True):
        QObject.connect(self.qApp,SIGNAL("twistedEvent"),
                        self.reactorInvocation)
        QObject.connect(self._timer, SIGNAL("timeout()"), 
                        self.reactorInvoke)
        self.startRunning(installSignalHandlers=installSignalHandlers)
        self.addSystemEventTrigger('after', 'shutdown', self.cleanup)
        self.qApp.emit(SIGNAL("twistedEvent"),'startup')
        QTimer.singleShot(101,self.slowPoll)
        self._timer.start(0)
        
    def run(self, installSignalHandlers=True):
        try:
            if self._ownApp:
                self._blockApp=self.qApp
            else:
                self._blockApp = fakeApplication()
            self.runReturn(installSignalHandlers)
            self._blockApp.exec_()
        finally:
            self._blockApp=None

    def slowPoll(self):
        self.qApp.emit(SIGNAL("twistedEvent"),'slowpoll')
        if self.running:
            QTimer.singleShot(101,self.slowPoll)
    
    def reactorInvocation(self):
        self._timer.setInterval(0)
        
    def reactorInvoke(self):
        self._doSomethingCount += 1
        if self.running:
            self.runUntilCurrent()
            t2 = self.timeout()
            t = self.running and t2
            if t is None: t=1.0
            self._timer.start(t*1010)
        else:
            if self._blockApp is not None:
                self._blockApp.quit()
                
    def doIteration(self):
        assert False, "doiteration is invalid call"
            
def install():
    """
    Configure the twisted mainloop to be run inside the qt mainloop.
    """
    from twisted.internet import main
    reactor = QTReactor()
    main.installReactor(reactor)

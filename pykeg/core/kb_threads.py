import asyncore
import logging
import Queue
import threading
import time

from pykeg.core import event
from pykeg.core import Interfaces
from pykeg.core import kb_common
from pykeg.core import timer
from pykeg.core.net import net
from pykeg.external.gflags import gflags

FLAGS = gflags.FLAGS

gflags.DEFINE_string('kegnet_server_bind_addr',
    kb_common.KEGNET_SERVER_BIND_ADDR,
    'Address that the kegnet server should bind to')

gflags.DEFINE_integer('kegnet_server_bind_port',
    kb_common.KEGNET_SERVER_BIND_PORT,
    'Port that the kegnet server should bind to',
    lower_bound=1,
    upper_bound=2**16 - 1)


### Base kegbot thread class

class KegbotThread(threading.Thread, Interfaces.IEventListener):
  """ Convenience wrapper around a threading.Thread """
  def __init__(self, kb_env, name):
    threading.Thread.__init__(self)
    self._kb_env = kb_env
    self.setName(name)
    self.setDaemon(True)
    self._quit = False
    self._logger = logging.getLogger(self.getName())
    self._started = False

  def hasStarted(self):
    return self._started

  def Quit(self):
    self._quit = True

  def start(self):
    self._started = True
    threading.Thread.start(self)

  ### Interfaces.IEventListener methods
  def PostEvent(self, ev):
    if ev.name() == kb_common.KB_EVENT.QUIT:
      self._logger.info('got quit event, quitting')
      self.Quit()


class WatchdogThread(KegbotThread):
  """Monitors all threads in _kb_env for crashes."""

  def run(self):
    fault_detected = False
    while not self._quit:
      if not fault_detected:
        for thr in self._kb_env.GetThreads():
          if not thr.hasStarted():
            continue
          if not self._quit and not thr.isAlive():
            self._logger.error('Thread %s died unexpectedly' % thr.getName())
            self._kb_env.GetEventHub().CreateAndPublishEvent(kb_common.KB_EVENT.QUIT)
            fault_detected = True
            break
      time.sleep(1.0)


class EventHubServiceThread(KegbotThread):
  """Handles all event dispatches for the event hub."""

  def run(self):
    hub = self._kb_env.GetEventHub()
    while not self._quit:
      hub.DispatchNextEvent(timeout=0.5)


class AlarmManagerThread(KegbotThread):

  def run(self):
    am = self._kb_env.GetAlarmManager()
    while not self._quit:
      alarm = am.WaitForNextAlarm(1.0)
      if alarm is not None:
        self._logger.info('firing alarm: %s' % alarm)
        alarm.Fire()


class EventHandlerThread(KegbotThread, Interfaces.IEventListener):
  """ Basic event handling thread. """
  def __init__(self, kb_env, name):
    KegbotThread.__init__(self, kb_env, name)
    self._event_queue = Queue.Queue()
    self._services = set()
    self._all_event_map = {}

  def AddService(self, service):
    self._services.add(service)
    self._RefreshEventMap()

  def _RefreshEventMap(self):
    for svc in self._services:
      for event, cmd in svc.EventMap().iteritems():
        if self._all_event_map.get(event) is None:
          self._all_event_map[event] = set()
        self._all_event_map[event].add(cmd)

  def run(self):
    while not self._quit:
      self._Step(timeout=0.5)

  def _Step(self, timeout=0.5):
    event = self._WaitForEvent(timeout)
    if event is not None:
      self._ProcessEvent(event)
    return event

  def PostEvent(self, event):
    self._event_queue.put(event)

  def _GetCallbacksForEvent(self, event):
    name = event.name()
    return self._all_event_map.get(name, tuple())

  def _WaitForEvent(self, timeout=0.5):
    """ Block until an event is posted, then process it """
    try:
      ev = self._event_queue.get(timeout=timeout)
      return ev
    except Queue.Empty:
      return None

  def _ProcessEvent(self, event):
    """ Execute the event callback associated with the event, if present. """
    if event.name() == kb_common.KB_EVENT.QUIT:
      self._logger.info('got quit event, quitting')
      self.Quit()
      return
    callbacks = self._GetCallbacksForEvent(event)
    for cb in callbacks:
      cb(event)

  def _FlushEvents(self):
    """ Process all events in the Queue immediately """
    while True:
      ev = self._Step(timeout=0.5)
      if ev is None:
        break


### Service threads

class NetProtocolThread(KegbotThread):
  def __init__(self, kb_env, name):
    KegbotThread.__init__(self, kb_env, name)
    self._server = net.KegnetServer(name='kegnet',
                                    kb_env=self._kb_env,
                                    addr=FLAGS.kegnet_server_bind_addr,
                                    port=FLAGS.kegnet_server_bind_port)

  def run(self):
    self._logger.info("network thread started")
    self._server.StartServer()
    while not self._quit:
      asyncore.loop(timeout=0.5, count=1)
    self._server.StopServer()
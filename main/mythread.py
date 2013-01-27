from threading import Thread
import logging

class LogExceptionThread(Thread):
    def __init__(self):
        super(LogExceptionThread, self).__init__()
        self._real_run = self.run
        self.run = self._wrap_run
    def _wrap_run(self):
        try:
            self._real_run()
        except Exception, e:
            logging.exception(e)


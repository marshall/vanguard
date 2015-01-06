import logging
import time

class Looper(object):
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__.lower())
        self.running = False

    def on_iteration(self):
        pass

    def on_interrupt(self):
        pass

    def on_stopped(self):
        pass

    def on_cleanup(self):
        pass

    def main(self):
        self.running = True
        while self.running:
            try:
                self.on_iteration()
            except KeyboardInterrupt:
                self.log.info('interrupt')
                self.running = self.on_interrupt() is True
            except StopIteration:
                self.log.info('stopped')
                self.running = self.on_stopped() is True

        self.on_cleanup()

class Interval(Looper):
    def __init__(self, interval=60):
        super(Interval, self).__init__()
        self.interval = interval

    def on_interval(self):
        pass

    def on_iteration(self):
        self.on_interval()
        time.sleep(self.interval)

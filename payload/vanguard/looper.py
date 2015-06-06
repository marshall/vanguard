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

    def on_started(self):
        pass

    def on_stopped(self):
        pass

    def on_cleanup(self):
        pass

    def main(self):
        self.running = True
        self.on_started()

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

class MultiInterval(Interval):
    def __init__(self, interval=1):
        super(MultiInterval, self).__init__(interval=interval)
        self.intervals = {}
        self.start_fn = None

    def interval(self, n, name=None):
        def wrapper(fn):
            self.add_interval(fn, n, name=name)
            return fn
        return wrapper

    def add_interval(self, fn, n, name=None):
        name = name or fn.__name__
        self.intervals[name] = dict(name=name, fn=fn, n=n, last_run=0)

    def on_started(self):
        last_run = time.time()
        for interval in self.intervals.values():
            interval['last_run'] = last_run

    def on_interval(self):
        for name, interval in self.intervals.iteritems():
            time_since = interval['last_run'] - time.time()
            if time_since >= interval['n']:
                self._exec(last=time_since, **interval)

    def _exec(self, **kwargs):
        try:
            self.log.info('Running \'{name}\', last={last:.1}s ago'.format(**kwargs))
            kwargs['fn']()
        except:
            self.log.exception('Exception running {name}'.format(**interval))
        finally:
            self.intervals[kwargs['name']]['last_run'] = time.time()


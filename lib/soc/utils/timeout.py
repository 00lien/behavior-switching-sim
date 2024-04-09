import time

class Timeout():
    def __init__(self, timeout) -> None:
        self.timeout = timeout
        self.timer = time.process_time() +timeout

    def __call__(self, callback, args=None):
        if time.process_time() >= self.timer:
            callback(args)
            self.timer = time.process_time() + self.timeout
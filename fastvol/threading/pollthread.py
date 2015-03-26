"""Thread specialized for polling."""

__all__ = ['PollThread', 'run_on_thread']

from functools import wraps
import logging
import os
import select
import threading

_log = logging.getLogger("threading")


def run_on_thread(thread_attr_name):
    """
    Decorator to run a method on the PollThread.

    :param str thread_attr_name: attribute name on self of the thread to run on
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            self = args[0]
            thread = getattr(self, thread_attr_name)
            thread.queue_operation(f, args, kwargs)
        return wrapper
    return decorator


class PollThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, daemon=None):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self._break_r, self._break_w = os.pipe()
        self._should_stop = False
        self._operations = []

    def poll(self, handler, *fds):
        """
        Poll these fds until the handler returns False or the thread is stopped.

        :param handler: function that takes a list of (fd, event) tuples, as returned by poll.  If this function returns
                        False, the polling loop will stop.
        :param fds: the fds to monitor
        """
        # Register all the given fds, as well as our special break fd.
        poll = select.poll()
        for fd in fds:
            poll.register(fd, select.POLLIN)
        poll.register(self._break_r, select.POLLIN)

        # Loop until _should_stop is set, or the handler returns False.
        while True:
            responses = poll.poll()

            # Handle break events.
            if self._break_r in [fd for (fd, event) in responses]:
                _log.debug("Break from polling on %s", self.name)
                os.read(self._break_r, 1024)
                # Stop if we were asked to.
                if self._should_stop:
                    _log.debug("Ending %s due to stop()", self.name)
                    break
                # Run all the operations queued for this thread.
                for operation, args, kwargs in self._operations:
                    _log.debug("Executing %r on %s", operation, self.name)
                    operation(*args, **kwargs)
                self._operations.clear()

            # Handle the rest of the responses.
            remaining_responses = [r for r in responses if r[0] != self._break_r]
            if len(remaining_responses) > 0:
                result = handler(remaining_responses)
                # Stop if the handler wants to.
                if result is False:
                    break

    def stop(self):
        """Cancel the poll operation, and block until the thread is stopped."""
        # Do nothing if already stopped.
        if not self.is_alive():
            return

        # Set the stop flag, and wake up the poll.
        self._should_stop = True
        os.write(self._break_w, b'1')

        # Wait for the thread to finish.
        self.join()

    def queue_operation(self, target, args, kwargs):
        """
        Queue an operation to run on the thread, and wake up the thread to run it.

        :param target: the function to call
        :param args: the positional arguments
        :param kwargs: the keyword arguments
        """
        self._operations.append((target, args, kwargs))
        os.write(self._break_w, b'1')

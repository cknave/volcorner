"""Test utilities."""

import smokesignal


class SignalReceiver:
    """Simple signal receiver that records if it was called once."""
    def __init__(self, signal):
        self.received = False
        self.args = None
        self.kwargs = None
        smokesignal.on(signal, self, max_calls=1)

    def __call__(self, *args, **kwargs):
        self.received = True
        self.args = args
        self.kwargs = kwargs
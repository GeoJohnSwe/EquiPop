# -*- coding: utf-8 -*-
"""
report.py - one voice, whichever door you came in through.

The engines talk by printing. That is deliberate: one voice for
every door, and it works in a plain Python session with nothing
attached. But a printed line goes nowhere in ArcGIS Pro, which shows
only what passes through its messages object, and nowhere in QGIS,
which shows only what passes through its feedback object.

Field finding behind this (v1.16.4): a 475,000-row run took 94
minutes with a completely silent pane. Every progress line the
package printed was thrown away, so nobody could see where the time
went - or that anything was happening at all.

So: a Channel is a door's three ways of speaking, Reporter catches
printed output line by line and sends it there, and stage() times a
step and says how long it took. A door supplies the three functions
once; everything above this line stays door-blind.
"""

import contextlib
import sys
import time


class Channel:
    """A door's three ways of speaking: info, warning, error.

    Doors differ only in which functions to call, so they hand them
    over once. A missing warning or error function falls back to
    info, which is always better than silence.
    """

    def __init__(self, info, warning=None, error=None):
        self._info = info
        self._warning = warning or info
        self._error = error or self._warning

    # -- speaking ------------------------------------------------
    def info(self, text):
        self._say(self._info, text)

    def warning(self, text):
        self._say(self._warning, text)

    def error(self, text):
        self._say(self._error, text)

    @staticmethod
    def _say(fn, text):
        try:
            fn(str(text))
        except Exception:
            # A pane that refuses a line must never end the run.
            pass

    # -- doors ---------------------------------------------------
    @classmethod
    def from_arcpy(cls, messages):
        """ArcGIS Pro: the messages object handed to execute()."""
        return cls(messages.addMessage,
                   getattr(messages, "addWarningMessage", None),
                   getattr(messages, "addErrorMessage", None))

    @classmethod
    def from_qgis(cls, feedback):
        """QGIS Processing: the feedback object handed to
        processAlgorithm(). pushWarning exists from 3.16 on, so it is
        looked up rather than assumed."""
        return cls(feedback.pushInfo,
                   getattr(feedback, "pushWarning", None),
                   getattr(feedback, "reportError", None))

    @classmethod
    def console(cls, prefix=""):
        """Plain Python, R via reticulate, a notebook: just print."""
        return cls(lambda t: print(f"{prefix}{t}"),
                   lambda t: print(f"{prefix}[warning] {t}"),
                   lambda t: print(f"{prefix}[error] {t}"))

    @classmethod
    def silent(cls):
        """For tests and batch runs that want no chatter."""
        return cls(lambda t: None)


class Reporter:
    """Catches what the package PRINTS and forwards it line by line.

    Buffers until a newline arrives, so a progress line written in
    pieces reaches the pane as one line rather than as fragments.
    """

    def __init__(self, channel):
        self.channel = channel
        self.buf = ""

    def write(self, text):
        self.buf += str(text)
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            if line.strip():
                self.channel.info(line.rstrip())

    def flush(self):
        if self.buf.strip():
            self.channel.info(self.buf.rstrip())
        self.buf = ""


@contextlib.contextmanager
def speaking(channel):
    """Everything printed inside this block reaches the door's pane."""
    old = sys.stdout
    rep = Reporter(channel)
    sys.stdout = rep
    try:
        yield
    finally:
        rep.flush()
        sys.stdout = old


def hms(sec):
    """Seconds as something a person reads at a glance."""
    sec = float(sec)
    if sec < 60:
        return f"{sec:.1f} s"
    m, s = divmod(int(round(sec)), 60)
    h, m = divmod(m, 60)
    return f"{h} h {m:02d} min {s:02d} s" if h else f"{m} min {s:02d} s"


@contextlib.contextmanager
def stage(channel, label, store=None):
    """Time one step and report it, so a long run says WHERE the
    time went instead of only how long it took in total."""
    t0 = time.time()
    yield
    dt = time.time() - t0
    if store is not None:
        store.append((label, dt))
    channel.info(f"[time] {label}: {hms(dt)}")

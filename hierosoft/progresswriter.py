# -*- coding: utf-8 -*-
import sys

class ProgressWriter:
    cli_print_delta = 1024 * 400  # 1024 * 400 is 400K

    def __init__(self):
        self.prev_bytes = None
        self.prev_percent = None
        self.prev_hr = None  # rounded
        self.prev_ratio = None  # precise
        self.hr_fn = None

    def write(self, size, total, force=False):
        min_d = ProgressWriter.cli_print_delta
        if self.prev_bytes and (size - self.prev_bytes < min_d):
            if not force:
                return
        percent = None
        ratio = None
        if total:
            ratio = size / total
            percent = round(size * 100 / total, 1)
        hr = None
        if self.hr_fn:
            hr = self.hr_fn(size)
        if (self.prev_hr and (hr == self.prev_hr)
                and (percent is None or percent == self.prev_percent)):
            if not force:
                return
        self.prev_bytes = size
        self.prev_percent = percent
        self.prev_ratio = ratio

        if total:
            # overwrite 4 with spaces ("." and digit, or neither if ".0" x2)
            sys.stderr.write(
                "\rprogress={}% size={}    "
                .format(percent, hr)
            )
        else:
            # overwrite 2 with spaces ("." and digit, or neither if ".0")
            sys.stderr.write(
                "\rsize={}  ".format(hr)
            )
        sys.stderr.flush()

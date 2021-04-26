#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import sys

sys.path.append(".")
from lib.checkbase import CheckIn


CI = os.environ.get("CI")
COOKIE = os.environ.get("cookie_sample")


class SampleCheckIn(CheckIn):
    def _checkin(self, get, post, info, error):
        pass


if __name__ == "__main__":
    SampleCheckIn("SAMPLE", COOKIE, CI).main()

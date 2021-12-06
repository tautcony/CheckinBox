#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import sys
from genshin import Sign
from lib.notify import notify

sys.path.append(".")
from lib.checkbase import CheckIn


COOKIE = os.environ.get("COOKIE_GENSHIN")


class GenshinCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error, cookie=None):
        message = Sign(session, cookie, info, error).run()
        notify("米游社签到完成", message)


if __name__ == "__main__":
    GenshinCheckIn("Genshin", COOKIE).main()

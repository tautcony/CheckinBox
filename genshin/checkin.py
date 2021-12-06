#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import sys
sys.path.append(".")

from lib.notify import notify
from lib.checkbase import CheckIn
from genshin import Sign


COOKIE = os.environ.get("COOKIE_GENSHIN")


class GenshinCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error, cookie=None):
        message = Sign(session, cookie, info, error).run()
        if "已经签到" not in message:
            notify("米游社签到完成", message)


if __name__ == "__main__":
    GenshinCheckIn("Genshin", COOKIE).main()

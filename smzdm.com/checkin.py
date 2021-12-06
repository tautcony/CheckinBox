#!/usr/bin/env python3
# -*- coding: utf8 -*-
import json
import os
import sys
import time

sys.path.append(".")
from lib.checkbase import CheckIn
from lib.logger import app_logger as logger
from lib.notify import notify


SIGN_URL = "https://zhiyou.smzdm.com/user/checkin/jsonp_checkin?_={0}"

COOKIE = os.environ.get("COOKIE_SMZDM")


class SMZDMCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error, cookie=None):
        t = round(int(time.time() * 1000))

        r = get(SIGN_URL.format(t))
        content = str(r.content, "utf-8")
        response = json.loads(content)
        logger.debug(response)
        if response.get("error_code", 99) != 0:
            error(response.get("error_msg", None) or f"未知错误[{r.status_code}]", content)
            return 1
        else:
            add_point = response.get("data", {}).get("add_point", 0)
            continue_checkin_days = response.get(
                "data", {}).get("continue_checkin_days", 1)
            info(f"签到成功，获得积分{add_point}，本周期已连续签到{continue_checkin_days}天")
            if continue_checkin_days == 3 or continue_checkin_days == 7:
                notify(f"{self.prefix()} 本周期已连续签到{continue_checkin_days}天，可在APP中领取额外奖励")
        return 0


if __name__ == "__main__":
    SMZDMCheckIn("SMZDM", COOKIE, {
        "Referer": "https://www.smzdm.com/"
    }).main()

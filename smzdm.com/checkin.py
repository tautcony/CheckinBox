#!/usr/bin/env python3
# -*- coding: utf8 -*-
import json
import os
import sys
import time

sys.path.append(".")
from lib.checkbase import CheckIn
from lib.logger import app_logger as logger


SIGN_URL = "https://zhiyou.smzdm.com/user/checkin/jsonp_checkin?_={0}"

CI = os.environ.get("CI")
COOKIE = os.environ.get("cookie_smzdm")


class SMZDMCheckIn(CheckIn):
    def _checkin(self, get, post, info, error):
        t = round(int(time.time() * 1000))

        r = get(SIGN_URL.format(t))
        response = json.loads(str(r.content, "utf-8"))
        logger.debug(response)
        if response.get("error_code", 99) != 0:
            error(response.get("error_msg", "未知错误") or "未知错误", json.dumps(response))
        else:
            add_point = response.get("data", {}).get("add_point", 0)
            continue_checkin_days = response.get(
                "data", {}).get("continue_checkin_days", 1)
            info(f"签到成功，获得积分{add_point}，已连续签到{continue_checkin_days}天")


if __name__ == "__main__":
    SMZDMCheckIn("SMZDM", COOKIE, CI, {
        "Referer": "https://www.smzdm.com/"
    }).main()

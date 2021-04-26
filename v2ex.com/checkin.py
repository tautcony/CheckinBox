#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import re
import sys

sys.path.append(".")
from lib.checkbase import CheckIn

RE_USER = re.compile(r"/member/([^\"]+)")
RE_ONCE = re.compile(r"\?once=(\d+)")
RE_BALANCE = re.compile(r"\d+?\s+的每日登录奖励\s+\d+\s+铜币")

DAILY_URL = "https://www.v2ex.com/mission/daily"
SIGN_URL = "https://www.v2ex.com/mission/daily/redeem?once={0}"
BALANCE_URL = "https://www.v2ex.com/balance"

COOKIE = os.environ.get("COOKIE_V2EX")


class V2EXCheckIn(CheckIn):
    def _checkin(self, get, post, info, error):
        # 获取 once
        r = get(DAILY_URL)
        result = RE_USER.search(r.text)
        if result:
            self.member = result[1]
        if "需要先登录" in r.text:
            error("Cookie失效")
            return 1
        elif "每日登录奖励已领取" in r.text:
            info("每日登录奖励已领取")
            return 0
        once = RE_ONCE.search(r.text)
        if once:
            once = once[1]
        else:
            error("无法获取once")
            return 1

        # 签到
        get(SIGN_URL.format(once))
        # 获取签到情况
        r = get(DAILY_URL)
        if "每日登录奖励已领取" in r.text:
            info("签到成功")
            # 查看获取到的数量
            r = get(BALANCE_URL)
            balance = RE_BALANCE.search(r.text)
            info(balance[0] if balance else "请检查`RE_BALANCE`")
        else:
            error("签到失败")
        return


if __name__ == "__main__":
    V2EXCheckIn("V2EX", COOKIE).main()

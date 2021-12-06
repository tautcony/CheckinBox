#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import re
import sys
from bs4 import BeautifulSoup

sys.path.append(".")
from lib.checkbase import CheckIn


COOKIE = os.environ.get("COOKIE_TSDM")


DAILY_URL = "https://www.tsdm39.net/plugin.php?id=dsu_paulsign:sign"
SIGN_URL = "https://www.tsdm39.net/plugin.php?id=dsu_paulsign:sign&operation=qiandao&infloat=1&inajax=1"

R_RET = re.compile(r"天使币\s*\d+")


class TSDMCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error, cookie=None):
        r = get(DAILY_URL)
        if "需要先登录" in r.text:
            error("Cookie失效")
            return 1
        if "已经签到" in r.text:
            info("您今天已经签到过了或者签到时间还未开始")
            return 0
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", {"id": "qiandao"})
        formhash = form.find("input", {"name": "formhash"}, recursive=False).get("value")
        data = {
            "formhash": formhash,
            "qdxq": "kx",
            "qdmode": "1",
            "todaysay": "限制最少3个,最多50个中文字数",
            "fastreply": "1"
        }
        r = post(SIGN_URL, data=data)
        if "签到成功" in r.text:
            ret = R_RET.search(r.text)
            info("签到成功" + (f"，获取{ret[0]}" if ret else ""))
        elif "已经签到" in r.text:
            info("您今日已经签到，请明天再来！")
        else:
            info(r.text)


if __name__ == "__main__":
    TSDMCheckIn("TSDM", COOKIE).main()

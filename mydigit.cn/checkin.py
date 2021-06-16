#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import re
import sys
from bs4 import BeautifulSoup

sys.path.append(".")
from lib.checkbase import CheckIn


COOKIE = os.environ.get("COOKIE_MYDIGIT")


DAILY_URL = "https://www.mydigit.cn/plugin.php?id=k_misign:sign"

R_RET = re.compile(r"\d+\s*M币")


class MYDIGITCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error):
        r = get(DAILY_URL)
        if "需要先登录" in r.text:
            error("Cookie失效")
            return 1
        if "btnvisteds" in r.text:
            info("您今天已经签到过了或者签到时间还未开始")
            return 0
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", {"id": "scbar_form"})
        formhash = form.find("input", {"name": "formhash"}, recursive=False).get("value")
        data = {
            "formhash": formhash,
            "operation": "qiandao",
            "format": "empty",
            "inajax": "1",
            "ajaxtarget": "JD_sign",
        }
        r = post(DAILY_URL, data=data)
        if "今日已签" in r.text:
            ret = R_RET.search(r.text)
            if ret:
                info("今日已签" + (f"，获取{ret[0]}" if ret else ""))
            else:
                info(r.text)
        elif "今日已签" in r.text:
            info("您今日已经签到，请明天再来！")
        else:
            info(r.text)


if __name__ == "__main__":
    MYDIGITCheckIn("MYDIGIT", COOKIE).main()

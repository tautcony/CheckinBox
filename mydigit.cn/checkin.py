#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import sys
from bs4 import BeautifulSoup

sys.path.append(".")
from lib.checkbase import CheckIn


COOKIE = os.environ.get("COOKIE_MYDIGIT")


DAILY_URL = "https://www.mydigit.cn/plugin.php?id=k_misign:sign"
CHECKIN_HISTORY_URL = "https://www.mydigit.cn/home.php?mod=spacecp&ac=credit&showcredit=1"


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
        if "<![CDATA[]]>" in r.text:
            info("签到成功")
        elif "今日已签" in r.text:
            info("您今日已经签到，请明天再来！")
        else:
            info("未知报文: {0}".format(r.text))
            return

        r = get(CHECKIN_HISTORY_URL)
        soup = BeautifulSoup(r.text, "html.parser")
        log = soup.select("span.xi1")
        if len(log) > 0:
            info("签到奖励：M币 {}".format(log[0].string))


if __name__ == "__main__":
    MYDIGITCheckIn("MYDIGIT", COOKIE).main()

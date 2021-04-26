#!/usr/bin/env python3
# -*- coding: utf8 -*-
import random
import os
import re
import sys
from bs4 import BeautifulSoup

sys.path.append(".")
from lib.checkbase import CheckIn


COOKIE = os.environ.get("cookie_u2")


class U2CheckIn(CheckIn):
    def _checkin(self, get, post, info, error):
        # 签到
        r = get("https://u2.dmhy.org/showup.php")
        soup = BeautifulSoup(r.text, 'html.parser')

        if soup.title.string == "Access Point :: U2":
            error("Cookie失效")
            return 1

        name = soup.select("a.NexusMaster_Name bdo")
        if len(name) > 0:
            self.member = name[0].string

        if "感谢，今天已签到。" in r.text:
            info("感谢，今天已签到。")
            return 0

        req = soup.find("input", {"name": "req"}).get("value")
        hs = soup.find("input", {"name": "hash"}).get("value")
        form = soup.find("input", {"name": "form"}).get("value")
        options = soup.find_all("input", {"type": "submit", "name": re.compile("captcha.+")})
        option = random.choice(options)

        r = post("https://u2.dmhy.org/showup.php?action=show", {
            "message": "注意：回答按钮点击时即提交，手滑损失自负~",
            "req": req,
            "hash": hs,
            "form": form,
            option.get("name"): option.get("value")
        })
        if "点我重新签到" in r.text:
            error("签到失败", r.text)
            return 1


if __name__ == "__main__":
    U2CheckIn("U2", COOKIE).main()

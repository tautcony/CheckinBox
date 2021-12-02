#!/usr/bin/env python3
# -*- coding: utf8 -*-
import random
import os
import re
import sys
from bs4 import BeautifulSoup

sys.path.append(".")
from lib.checkbase import CheckIn


RE_UID = re.compile(r"id=(\d+)")

COOKIE = os.environ.get("COOKIE_U2")


class U2CheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error):
        # 签到
        r = get("https://u2.dmhy.org/showup.php")
        soup = BeautifulSoup(r.text, "html.parser")

        if soup.title.string == "Access Point :: U2":
            error("Cookie失效")
            return 1
        if soup.title.string == "Just a moment...":
            error("Blocked by Cloudflare")
            return 1

        uid = soup.select("a.NexusMaster_Name")
        if len(uid) > 0:
            self.uid = RE_UID.search(uid[0]["href"])[1]

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
        r = get(f"https://u2.dmhy.org/ucoin.php?id={self.uid}&log=1")
        r_soup = BeautifulSoup(r.text, "html.parser")
        records = r_soup.find_all("td", {"title": ""}, text="Showup Reward")
        if len(records) > 0:
            uc = records[-1].findNext('td').string
            info(f"签到奖励: {uc}UC, " + ("猜错了" if uc == "1.000" else "猜对了"))
        return 0


if __name__ == "__main__":
    U2CheckIn("U2", COOKIE, cloudscraper=True).main()

#!/usr/bin/env python3
# -*- coding: utf8 -*-
import logging
import os
import re
import sys
import time
import requests


# init logger
app_log = logging.getLogger()
fmt = "%(asctime)s %(levelname)-8s %(message)s"
log_formatter = logging.Formatter(fmt)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
app_log.addHandler(console_handler)
app_log.setLevel(logging.INFO)


try:
    sys.path.append(".")
    from notify import notify
except:
    logging.error("无法加载notify函数")

    def notify(message):
        pass

SIGN_URL = "https://zhiyou.smzdm.com/user/checkin/jsonp_checkin?_={0}"

CI = os.environ.get("CI")
COOKIE_SMZDM = os.environ.get("cookie_smzdm")


def signin(cookie):
    member = "/"
    s = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cookie": cookie,
        "Referer": "https://www.smzdm.com/"
    }

    def get(url): return s.get(url, headers=headers, timeout=120)

    def info(message):
        prefix = "[SMZDM]" if CI else f"[SMZDM:{member}]"
        logging.info(f"{prefix} {message}")

    def error(message):
        prefix = "[SMZDM]" if CI else f"[SMZDM:{member}]"
        logging.error(f"{prefix} {message}")
        notify(f"[SMZDM:{member}] {message}")

    t = round(int(time.time() * 1000))

    r = get(SIGN_URL.format(t))
    response = r.json()
    logging.debug(response)
    if response.get("error_code", 99) != 0:
        error(response.get("error_msg", "未知错误"))
    else:
        add_point = response.get("data", {}).get("add_point", 0)
        continue_checkin_days = response.get(
            "data", {}).get("continue_checkin_days", 1)
        info(f"签到成功，获得积分{add_point}，已连续签到{continue_checkin_days}天")


def main(cookie):
    full_log = []
    if "\\n" in cookie:
        clist = cookie.split("\\n")
    else:
        clist = cookie.split("\n")
    i = 0
    for i in range(len(clist)):
        try:
            signin(clist[i])
        except Exception as ex:
            logging.error(repr(ex))


if __name__ == "__main__":
    if COOKIE_SMZDM:
        print("----------什么值得买开始签到----------")
        main(COOKIE_SMZDM)
        print("----------什么值得买签到完毕----------")

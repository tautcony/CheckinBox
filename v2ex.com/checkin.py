#!/usr/bin/env python3
# -*- coding: utf8 -*-
import logging
import os
import re
import sys
import requests
import traceback


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

RE_USER = re.compile(r"/member/([^\"]+)")
RE_ONCE = re.compile(r"\?once=(\d+)")
RE_BALANCE = re.compile(r"\d+?\s+的每日登录奖励\s+\d+\s+铜币")

DAILY_URL = "https://www.v2ex.com/mission/daily"
SIGN_URL = "https://www.v2ex.com/mission/daily/redeem?once={0}"
BALANCE_URL = "https://www.v2ex.com/balance"

# 获取参数
CI = os.environ.get("CI")
COOKIE_V2EX = os.environ.get("cookie_v2ex")


def signin(cookie, **kwargs):
    member = "/"
    s = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "accept-encoding": "gzip, deflate",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "Cookie": cookie
    }

    def get(url): return s.get(url, headers=headers, timeout=120)

    def info(message):
        prefix = "[V2EX]" if CI else f"[V2EX:{member}]"
        logging.info(f"{prefix} {message}")

    def error(message):
        prefix = "[V2EX]" if CI else f"[V2EX:{member}]"
        logging.error(f"{prefix} {message}")
        notify(f"[V2EX:{member}] {message}")

    # 获取 once
    r = get(DAILY_URL)
    result = RE_USER.search(r.text)
    if result:
        member = result[1]
    if "需要先登录" in r.text:
        # TODO pusher
        error("Cookie失效")
        return
    elif "每日登录奖励已领取" in r.text:
        info("每日登录奖励已领取")
        return
    once = RE_ONCE.search(r.text)
    if once:
        once = once[1]
    else:
        error("无法获取once")
        return

    # 签到
    sign = get(SIGN_URL.format(once))
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


def main(cookie):
    full_log = []
    if "\\n" in cookie:
        clist = cookie.split("\\n")
    else:
        clist = cookie.split("\n")
    i = 0
    for i in range(len(clist)):
        logging.info(f"第 {i+1} 个账号开始签到")
        try:
            signin(clist[i])
        except Exception as ex:
            notify(f"[V2EX:Exception]", traceback.format_exc())


if __name__ == "__main__":
    if COOKIE_V2EX:
        logging.info("----------V2EX开始签到----------")
        main(COOKIE_V2EX)
        logging.info("----------V2EX签到完毕----------")

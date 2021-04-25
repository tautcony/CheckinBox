#!/usr/bin/env python3
# -*- coding: utf8 -*-
import logging
import random
import os
import re
import sys
import requests
import traceback
from bs4 import BeautifulSoup


# init logger
app_log = logging.getLogger()
fmt = "%(asctime)s %(levelname)-8s %(message)s"
log_formatter = logging.Formatter(fmt)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
app_log.addHandler(console_handler)
app_log.setLevel(logging.INFO)

TITLE = "U2"


try:
    sys.path.append(".")
    from notify import notify
except:
    logging.error("无法加载notify函数")

    def notify(message):
        pass

# 获取参数
CI = os.environ.get("CI")
COOKIE = os.environ.get("cookie_u2")


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
    def post(url, data): return s.post(url, data=data, headers=headers, timeout=120)

    def info(message):
        prefix = f"[{TITLE}]" if CI else f"[{TITLE}:{member}]"
        logging.info(f"{prefix} {message}")

    def error(message, *args):
        prefix = f"[{TITLE}]" if CI else f"[{TITLE}:{member}]"
        logging.error(f"{prefix} {message}")
        notify(f"[{TITLE}:{member}] {message}", *args)

    # 签到
    r = get("https://u2.dmhy.org/showup.php")
    soup = BeautifulSoup(r.text, 'html.parser')

    if soup.title.string == "Access Point :: U2":
        error("Cookie失效")
        return

    name = soup.select("a.NexusMaster_Name bdo")
    if len(name) > 0:
        member = name[0].string

    if "感谢，今天已签到。" in r.text:
        info("感谢，今天已签到。")
        return

    req = soup.find("input", {"name": "req"}).get("value")
    hash = soup.find("input", {"name": "hash"}).get("value")
    form = soup.find("input", {"name": "form"}).get("value")
    options = soup.find_all("input", {"type": "submit", "name": re.compile("captcha.+")})
    option = random.choice(options)

    r = post("https://u2.dmhy.org/showup.php?action=show", {
        "message": "注意：回答按钮点击时即提交，手滑损失自负~",
        "req": req,
        "hash": hash,
        "form": form,
        option.get("name"): option.get("value")
    })
    if "点我重新签到" in r.text:
        error("签到失败", r.text)
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
            logging.error(traceback.format_exc())
            notify(f"[{TITLE}:Exception]", traceback.format_exc())


if __name__ == "__main__":
    if COOKIE:
        logging.info(f"----------{TITLE}开始签到----------")
        main(COOKIE)
        logging.info(f"----------{TITLE}签到完毕----------")

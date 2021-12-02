import os
import re
import sys
import traceback
from typing import Any, Callable

import requests
from requests import Response
from requests.utils import add_dict_to_cookiejar
from requests.exceptions import ConnectTimeout, Timeout

from lib.logger import app_logger as logger
from lib.notify import notify


CI = os.environ.get("CI")
GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY")
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID")

GITHUB_NOTIFICATION = os.environ.get("GITHUB_NOTIFICATION")
ENABLE_GITHUB_NOTIFICATION = GITHUB_NOTIFICATION and \
    (GITHUB_NOTIFICATION.lower() == "true" or GITHUB_NOTIFICATION.lower() == "1")

RE_COOKIE = re.compile("([^=]+)=\"?(.+?)\"?;\\s*")


class CheckIn(object):
    def __init__(self, title: str, cookies: str, cloudscraper=False, extra_headers=None):
        self.title = title
        self.cookies = cookies
        self.ci = CI
        self.member = None
        self.uid = None
        self.cloudscraper = cloudscraper
        self.extra_headers = extra_headers

    def _checkin(self,
                 session: requests.Session,
                 get: Callable[[str], Response],
                 post: Callable[[str, Any], Response],
                 info: Callable,
                 error: Callable) -> int:
        error("未重载`_checkin`函数")
        return 255

    def prefix(self):
        return f"[{self.title}]" if self.ci or not self.member else f"[{self.title}:{self.member}]"

    def notify(self, title: str, *args):
        prefixed_title = f"{self.prefix()} {title}"
        logger.error(prefixed_title)
        print(f"::warning:: {prefixed_title}")
        notify(prefixed_title, *args, f"ref: https://github.com/{GITHUB_REPOSITORY}/actions/runs/{GITHUB_RUN_ID}")

    @staticmethod
    def chunker(seq, size):
        return (seq[pos:pos + size] for pos in range(0, len(seq), size))

    def checkin(self, cookie: str) -> int:
        self.member = "/"
        self.uid = None
        if self.cloudscraper:
            from cloudscraper import create_scraper
            s = create_scraper()
        else:
            s = requests.Session()

        cookie_dict = {}
        match = RE_COOKIE.findall(cookie + ";")
        for item in match:
            cookie_dict[item[0]] = item[1]

        add_dict_to_cookiejar(s.cookies, cookie_dict)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/90.0.4430.85 "
                          "Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                      "image/avif,image/webp,image/apng,*/*;q=0.8,"
                      "application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7"
        }

        if self.extra_headers:
            headers.update(self.extra_headers)

        def get(url: str, **kwargs):
            return s.get(url, headers=headers, timeout=20, **kwargs)

        def post(url: str, data=None, **kwargs):
            return s.post(url, data=data, headers=headers, timeout=20, **kwargs)

        def info(message: str):
            logger.info(f"{self.prefix()} {message}")

        def error(message: str, *args):
            self.notify(message, *args)

        return self._checkin(s, get, post, info, error)

    def main(self):
        print(f"::group::{self.title}")
        if not self.cookies:
            logger.info(f"{self.prefix()} 未配置Cookie，跳过签到")
            print("::endgroup::")
            return
        ret = 0
        logger.info(f"----------{self.title:8}开始签到----------")
        if "\\n" in self.cookies:
            clist = self.cookies.split("\\n")
        else:
            clist = self.cookies.split("\n")

        for i in range(len(clist)):
            if len(clist) > 1:
                logger.info(f"第{i+1}个账号开始签到")
            try:
                code = self.checkin(clist[i])
                ret |= code if code is not None else 0
            except (ConnectTimeout, Timeout) as e:
                ret |= 1
                self.notify(f"请求超时: {str(e)}")
            except Exception as e:
                ret |= 1
                self.notify(f"未知异常{type(e)}", traceback.format_exc())
        logger.info(f"----------{self.title:8}签到完毕----------")
        print("::endgroup::")
        if ENABLE_GITHUB_NOTIFICATION:
            sys.exit(ret)

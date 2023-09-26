#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import sys
import json

sys.path.append(".")
from lib.checkbase import CheckIn

UID_CRED_KEY = os.environ.get("SKLAND_UID_CRED_KEY")

SIGN_URL = "https://zonai.skland.com/api/v1/game/attendance"


class SKLandCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error, uid_cred_key=None):
        [uid, cred_key] = uid_cred_key.split("&")
        headers = {
            "user-agent": "Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 33; ) Okhttp/4.11.0",
            "cred": cred_key,
            "Accept-Encoding": "gzip",
            "Connection": "close",
            "platform": "1"
        }
        data = {
            "uid": str(uid),
            "gameId": 1
        }
        r = post(SIGN_URL, headers=headers, data=data)
        try:
            resp = json.loads(r.text)
            data = resp.get("data")
            if resp.get("code") == 0:
                print("签到成功")
                for award in resp.get("data").get("awards"):
                    print(f"此次签到获得了{award.get('count')}单位的{award.get('resource').get('name')}\
                          ({award.get('resource').get('type')})")
                    print(f"奖励类型为：{award.get('type')}")
            else:
                message = resp.get("message")
                print(message)
                print("签到失败，请检查以上信息...")
        except:
            print(r.text)

        return 0


if __name__ == "__main__":
    SKLandCheckIn("skland", UID_CRED_KEY).main()

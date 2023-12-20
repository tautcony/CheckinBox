#!/usr/bin/env python3
# -*- coding: utf8 -*-
import os
import sys
import json

sys.path.append(".")
from lib.checkbase import CheckIn

APP_CODE = "4ca99fa6b56cc2ba"
temp_header = {
    "cred": "",
    "User-Agent": "Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 31; ) Okhttp/4.11.0",
    "Accept-Encoding": "gzip",
    "Connection": "close",
}

# 签名请求头一定要这个顺序，否则失败
# timestamp是必填的,其它三个随便填,不要为none即可
header_for_sign = {"platform": "1", "timestamp": "", "dId": "de9759a5afaa634f", "vName": "1.0.1"}

sign_url = "https://zonai.skland.com/api/v1/game/attendance"
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
cred_code_url = "https://zonai.skland.com/api/v1/user/auth/generate_cred_by_code"

UID_CRED_KEY = os.environ.get("SKLAND_UID_CRED_KEY")

SIGN_URL = "https://zonai.skland.com/api/v1/game/attendance"


class SKLandCheckIn(CheckIn):
    def _checkin(self, session, get, post, info, error, uid_cred_key=None):
        [uid, cred_key] = uid_cred_key.split("&")
        data = {
            "uid": str(uid),
            "gameId": 1
        }
        r = post(SIGN_URL, data=data)
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

    def cleantext(text: str) -> str:
        lines = text.strip().split("\n")
        cleaned_lines = [line.strip() for line in lines]
        result = "\n".join(cleaned_lines)
        return result


"""
    async def get_grant_code(token: str) -> str:
        data = {"appCode": APP_CODE, "token": token, "type": 0}

        async with AsyncClient() as client:
            response = await client.post(grant_code_url, headers=login_header, data=data)
            response.raise_for_status()
            return response.json()["data"]["code"]


    async def get_cred(grant_code: str) -> dict[str, Any]:
        data = {"code": grant_code, "kind": 1}

        async with AsyncClient() as client:
            response = await client.post(cred_code_url, headers=login_header, data=data)
            response.raise_for_status()
            return response.json()["data"]


    async def get_cred_by_token(token: str) -> dict[str, Any]:
        grant_code = await get_grant_code(token)
        return await get_cred(grant_code)


    async def get_binding_list(cred_resp: dict) -> list[dict[str, Any]]:
        headers = temp_header.copy()
        headers["cred"] = cred_resp["cred"]
        async with AsyncClient() as client:
            response = await client.get(
                binding_url, headers=get_sign_header(binding_url, "get", None, headers, cred_resp["token"])
            )
            response.raise_for_status()
            response = response.json()
        for i in response["data"]["list"]:
            if i.get("appCode") == "arknights":
                return i["bindingList"]
        return []
"""


if __name__ == "__main__":
    if UID_CRED_KEY is None:
        print("未找到环境变量：SKLAND_UID_CRED_KEY")
        exit(0)
    [uid, cred_key] = UID_CRED_KEY.split("&")
    headers = {
        "user-agent": "Skland/1.0.1 (com.hypergryph.skland; build:100001014; Android 33; ) Okhttp/4.11.0",
        "cred": cred_key,
        "Accept-Encoding": "gzip",
        "Connection": "close",
        "platform": "1"
    }
    SKLandCheckIn("skland", UID_CRED_KEY, headers).main()

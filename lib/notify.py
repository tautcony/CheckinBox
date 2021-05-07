import logging
import time
import hmac
import hashlib
import base64
import requests
import urllib.parse
import os


# 微信server酱通知
SCKEY = os.environ.get("SCKEY")  # https://sc.ftqq.com/
SCTKEY = os.environ.get("SCTKEY")  # https://sct.ftqq.com/

# QQ酷推通知
CP_KEY = os.environ.get("CP_KEY")  # https://cp.xuthus.cc/
# send, group, psend, pgroup, wx, tg, ww, ding(no send email)
CP_MODE = os.environ.get("CP_MODE")

# pushplus通知
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN")  # https://www.pushplus.plus/
# pushplus一对多推送需要填写"群组编码"
PUSH_PLUS_TOPIC = os.environ.get("PUSH_PLUS_TOPIC")

# 钉钉bot通知
# 钉钉bot webhook的Token
DD_BOT_TOKEN = os.environ.get("DD_BOT_TOKEN")
# 密钥，安全设置选择"加密"
DD_BOT_SECRET = os.environ.get("DD_BOT_SECRET")

# telegram bot通知
# Telegram bot的Token
TG_TOKEN = os.environ.get("TG_TOKEN")
# 接收通知消息的Telegram用户的id
TG_CHATID = os.environ.get("TG_CHATID")
# Telegram api自建的反向代理地址，默认tg官方api=api.telegram.org
TG_API_HOST = os.environ.get("TG_API_HOST")


def server_notify(title: str, content: str):
    if SCKEY:
        r = requests.post(f"https://sc.ftqq.com/{SCKEY}.send", data={
            "text": title,
            "desp": content
        })
        logging.debug(r.text)
    if SCTKEY:
        r = requests.post(f"https://sctapi.ftqq.com/{SCTKEY}.send", data={
            "title": title,
            "desp": content
        })
        logging.debug(r.text)


def push_plus_notify(title: str, content: str):
    if not PUSH_PLUS_TOKEN:
        return
    params = {
        "token": PUSH_PLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "html"
    }
    if PUSH_PLUS_TOPIC:
        params["topic"] = PUSH_PLUS_TOPIC
    r = requests.post("https://www.pushplus.plus/send", params=params)
    logging.debug(r.text)
    obj: dict = r.json()
    if obj.get("code", 404) != 200:
        msg = obj.get("msg", "")
        data = obj.get("data", "")
        logging.error(f"pushplus消息发送失败: {msg}\n{data}")
    else:
        print("pushplus消息发送成功")


def cp_notify(title: str, content: str):
    if not CP_KEY:
        return
    mode = "send" if not CP_MODE else CP_MODE
    if content:
        title = title + "\n" + content
    r = requests.post(f"https://push.xuthus.cc/{mode}/{CP_KEY}", params={
        "c": title
    })
    logging.debug(r.text)


def dd_notify(title: str, content: str, msgtype="text"):
    if not DD_BOT_TOKEN:
        return
    url = f"https://oapi.dingtalk.com/robot/send?access_token={DD_BOT_TOKEN}"
    if DD_BOT_SECRET:
        timestamp = str(round(time.time() * 1000))
        secret_enc = DD_BOT_SECRET.encode('utf-8')
        string_to_sign = f'{timestamp}\n{DD_BOT_SECRET}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        url = f"{url}&timestamp={timestamp}&sign={sign}"
    data = {
        "msgtype": msgtype
    }
    if msgtype == "text":
        data["text"] = {
            "content": f"{title}\n{content}"
        }
    elif msgtype == "markdown":
        data["markdown"] = {
            "title": title,
            "text": content
        }
    r = requests.post(url=url, json=data)
    logging.debug(r.text)
    obj: dict = r.json()
    if obj.get("errcode", -1) != 0:
        errorcode = obj.get("errcode", -1)
        errmsg = obj.get("errmsg", "")
        logging.error(f"钉钉消息发送失败: {errorcode}\n{errmsg}")
    else:
        logging.info("钉钉消息发送成功")


def tg_notify(title: str, content: str):
    if not (TG_TOKEN and TG_CHATID):
        return
    api_host = TG_API_HOST if TG_API_HOST else "api.telegram.org"
    r = requests.post(f"https://{api_host}/bot{TG_TOKEN}/sendMessage", json={
        "chat_id": TG_CHATID,
        "text": f"{title}\n{content}"
    })
    logging.debug(r.text)
    obj: dict = r.json()
    if not obj.get("ok", False):
        error_code = obj.get("error_code", 0)
        description = obj.get("description", "")
        logging.error(f"Telegram消息发送失败: {error_code}\n{description}")
    else:
        logging.info("Telegram消息发送成功")


def notify(title: str, *args):
    content = "\n".join([str(i) for i in args])
    if len(title) > 128:
        if not content:
            content = title
        else:
            content = f"{title}\n\n{content}"
        title = f"{title[:128]}..."

    server_notify(title, content)
    push_plus_notify(title, content)
    cp_notify(title, content)
    dd_notify(title, content)
    tg_notify(title, content)

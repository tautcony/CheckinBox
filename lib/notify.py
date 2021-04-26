import logging
import requests
import os

SCKEY = os.environ.get("SCKEY")  # http://sc.ftqq.com/
SCTKEY = os.environ.get("SCTKEY")  # http://sct.ftqq.com/

CPkey = os.environ.get("CPkey")  # https://cp.xuthus.cc/
# send, group, psend, pgroup, wx, tg, ww, ding(no send email)
CPmode = os.environ.get("CPmode")

pushplus_token = os.environ.get("pushplus_token")  # http://www.pushplus.plus/
# pushplus一对多推送需要的"群组编码"，一对一推送不用管
pushplus_topic = os.environ.get("pushplus_topic")

# telegram bot的Token，telegram机器人通知推送必填项
tg_token = os.environ.get("tg_token")
# 接收通知消息的telegram用户的id，telegram机器人通知推送必填项
tg_chatid = os.environ.get("tg_chatid")
# Telegram api自建的反向代理地址，默认tg官方api=api.telegram.org
tg_api_host = os.environ.get("tg_api_host")


def notify(title, *args, **kwargs):
    content = ""
    for item in args:
        content += item
        content += "\n"
    if not content:
        content = title

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
    if pushplus_token:
        params = {
            "token": pushplus_token,
            "title": title,
            "content": content,
            "template": "html",
            "topic": pushplus_topic
        }
        if pushplus_topic:
            params["topic"] = pushplus_topic
        r = requests.post("https://www.pushplus.plus/send", params=params)
        if r.json()["code"] != 200:
            print(r.json())
            print(f"pushplus推送失败！")
        logging.debug(r.text)
    if CPkey:
        mode = "send" if not CPmode else CPmode
        if content:
            title = title + "\n" + content
        r = requests.post(f"https://push.xuthus.cc/{mode}/{CPkey}", params={
            "c": title
        })
        logging.debug(r.text)
    if tg_token and tg_chatid:
        api_host = tg_api_host if tg_api_host else "api.telegram.org"
        r = requests.post(f"https://{api_host}/bot{tg_token}/sendMessage", data={
            "chat_id": tg_chatid,
            "text": f"{title}\n{content}"
        })
        logging.debug(r.text)

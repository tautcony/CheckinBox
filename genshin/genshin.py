'''
@File                : genshin.py
@Github              : https://github.com/y1ndan/genshin-impact-helper
@Last modified by    : y1ndan
@Last modified time  : 2021-02-02 14:10:30
'''
import hashlib
import json
import random
import string
import time
import uuid
from requests import Session

from settings import CONFIG


def version():
    return 'v1.6.11'


def hexdigest(text):
    md5 = hashlib.md5()
    md5.update(text.encode())
    return md5.hexdigest()


class Base(object):
    def __init__(self, session: Session, cookie: str, info, error):
        self.session = session
        self._cookie = cookie
        self.info = info
        self.error = error

    def get_header(self):
        header = {
            'User-Agent': CONFIG.USER_AGENT,
            'Referer': CONFIG.REFERER_URL,
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': self._cookie
        }
        return header


class Roles(Base):
    def __init__(self, session: Session, cookie: str, info, error):
        super().__init__(session, cookie, info, error)

    def get_awards(self):
        response = {}
        try:
            response = self.session.get(CONFIG.AWARD_URL, headers=self.get_header(), timeout=20).json()
        except json.JSONDecodeError as e:
            raise Exception(e)

        return response

    def get_roles(self):
        self.info('准备获取账号信息...')
        response = {}
        try:
            response = self.session.get(CONFIG.ROLE_URL, headers=self.get_header(), timeout=20).json()
            message = response['message']
        except Exception as e:
            raise Exception(e)
        if response.get('retcode', 1) != 0 or response.get('data', None) is None:
            raise Exception(message)

        self.info('账号信息获取完毕')
        return response


class Sign(Base):
    def __init__(self, session: Session, cookie: str, info, error):
        super(Sign, self).__init__(session, cookie, info, error)
        self._roles = Roles(self.session, self._cookie, self.info, self.error)
        self._region_list = []
        self._region_name_list = []
        self._uid_list = []

    @staticmethod
    def get_ds():
        # v2.3.0-web @povsister & @journey-ad
        n = 'h8w582wxwgqvahcdkpvdhbh2w9casgfl'
        i = str(int(time.time()))
        r = ''.join(random.sample(string.ascii_lowercase + string.digits, 6))
        c = hexdigest('salt=' + n + '&t=' + i + '&r=' + r)
        return '{},{},{}'.format(i, r, c)

    def get_header(self):
        header = super(Sign, self).get_header()
        header.update({
            'x-rpc-device_id': str(uuid.uuid3(
                uuid.NAMESPACE_URL, self._cookie)).replace('-', '').upper(),
            # 1:  ios
            # 2:  android
            # 4:  pc web
            # 5:  mobile web
            'x-rpc-client_type': '5',
            'x-rpc-app_version': CONFIG.APP_VERSION,
            'DS': self.get_ds(),
        })
        return header

    def get_info(self):
        user_game_roles = self._roles.get_roles()
        role_list = user_game_roles.get('data', {}).get('list', [])

        # role list empty
        if not role_list:
            raise Exception(user_game_roles.get('message', 'Role list empty'))

        self.info(f'当前账号绑定了 {len(role_list)} 个角色')
        info_list = []
        # cn_gf01:  天空岛
        # cn_qd01:  世界树
        self._region_list = [(i.get('region', 'NA')) for i in role_list]
        self._region_name_list = [(i.get('region_name', 'NA')) for i in role_list]
        self._uid_list = [(i.get('game_uid', 'NA')) for i in role_list]

        self.info('准备获取签到信息...')
        for i in range(len(self._uid_list)):
            info_url = CONFIG.INFO_URL.format(
                self._region_list[i], CONFIG.ACT_ID, self._uid_list[i])
            try:
                content = self.session.get(info_url, headers=self.get_header(), timeout=20).json()
                info_list.append(content)
            except Exception as e:
                raise Exception(e)

        if not info_list:
            raise Exception('User sign info list is empty')
        self.info('签到信息获取完毕')
        return info_list

    def run(self):
        info_list = self.get_info()
        message_list = []
        for i in range(len(info_list)):
            today = info_list[i]['data']['today']
            total_sign_day = info_list[i]['data']['total_sign_day']
            awards = self._roles.get_awards()['data']['awards']
            uid = str(self._uid_list[i]).replace(
                str(self._uid_list[i])[1:8], '******', 1)

            self.info(f'准备为旅行者 {i + 1} 号签到...')
            time.sleep(10)
            message = {
                'today': today,
                'region_name': self._region_name_list[i],
                'uid': uid,
                'total_sign_day': total_sign_day,
                'end': '',
            }
            if info_list[i]['data']['is_sign'] is True:
                message['award_name'] = awards[total_sign_day - 1]['name']
                message['award_cnt'] = awards[total_sign_day - 1]['cnt']
                message['status'] = f'👀 旅行者 {i + 1} 号, 你已经签到过了哦'
                message_list.append(self.message.format(**message))
                continue
            else:
                message['award_name'] = awards[total_sign_day]['name']
                message['award_cnt'] = awards[total_sign_day]['cnt']
            if info_list[i]['data']['first_bind'] is True:
                message['status'] = f'💪 旅行者 {i + 1} 号, 请先前往米游社App手动签到一次'
                message_list.append(self.message.format(**message))
                continue

            data = {
                'act_id': CONFIG.ACT_ID,
                'region': self._region_list[i],
                'uid': self._uid_list[i]
            }

            try:
                response = self.session.post(CONFIG.SIGN_URL, headers=self.get_header(),
                                             data=json.dumps(data, ensure_ascii=False), timeout=20).json()
            except Exception as e:
                self.error(e)
                raise
            code = response.get('retcode', 99999)
            # 0:      success
            # -5003:  already signed in
            if code != 0:
                message_list.append(response)
                continue
            message['total_sign_day'] = total_sign_day + 1
            message['status'] = response['message']
            message_list.append(self.message.format(**message))
        self.info('签到完毕')

        return ''.join(message_list)

    @property
    def message(self):
        return CONFIG.MESSAGE_TEMPLATE

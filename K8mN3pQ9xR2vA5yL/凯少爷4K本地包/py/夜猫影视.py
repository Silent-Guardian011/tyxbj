# -*- coding: utf-8 -*-
# by  灰太狼
import sys,json
import requests

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):

    def init(self, extend):
        js1 = json.loads(extend)
        self.host=js1['host']
        self.username=js1['username']
        self.password=js1['password']
        pass

    def getName(self):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0',
    }

    def homeContent(self, filter):
        data = self.fetch(f"{self.host}/api/v1/video/categories",headers=self.headers).json()
        return {'class':data['data']}

    def homeVideoContent(self):
        data=self.fetch(f"{self.host}/api/v1/content/slides",headers=self.headers).json()
        videos = []
        for i in data['data']:
            id = i['vod_id']
            name = i['title']
            pic = i['image_url']
            video = {
                "vod_id": id,
                "vod_name": name,
                "vod_pic": pic
            }
            videos.append(video)
        return {'list':videos}

    def categoryContent(self, tid, pg, filter, extend):
        params = {'type_id':tid,'page_size':'18','page':pg,'order':'time'}
        data=self.fetch(f"{self.host}/api/v1/video/list",params=params,headers=self.headers).json()
        return data['data']

    def detailContent(self, ids):
        data=self.fetch(f"{self.host}/api/v1/video/detail/{ids[0]}",headers=self.headers).json()
        return  {'list':[data['data']]}

    def searchContent(self, key, quick, pg="1"):
        params = {'keyword': key, 'page_size': '18', 'page': pg}
        data = self.fetch(f"{self.host}/api/v1/video/search", params=params, headers=self.headers).json()
        return {'list':data['data']['list'],'page':pg}

    def playerContent(self, flag, id, vipFlags):
        auth_token = self.getCache("auth_token")
        if not auth_token:
            login_res = self.login()
        auth_token = self.getCache("auth_token")
        if not auth_token:
            raise Exception("自动登录失败，请检查账号密码或网络")
        self.headers["authorization"] = auth_token
        data = self.fetch(f"{self.host}/api/v1/content/parse?url={id}&no_dash=1", headers=self.headers).json()
        if 'data' not in data or 'url' not in data['data']:
            raise Exception(f"获取播放地址失败：{data.get('msg', '未知错误')}")
        playurl = self.decrypt(data['data']['url'])
        return {"parse": 0, "playUrl": '', "url": playurl, 'header': self.headers}

    def localProxy(self, param):
        pass

    def decrypt(self, encrypted_data_b64):
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import unpad
        import base64
        key = b"YeCat2026AesKey!"
        encrypted_data = base64.b64decode(encrypted_data_b64)
        iv = encrypted_data[:16]
        ciphertext = encrypted_data[16:]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        decrypted = unpad(decrypted_padded, AES.block_size)
        return decrypted.decode('utf-8')

    def login(self):
        data = {"username": self.username, "password": self.password}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
        }
        response = self.post(
            url=f"{self.host}/api/v1/auth/login",
            json=data,
            headers=headers
        )
        res = response.json()
        if res.get('code') == 1 or 'data' in res and 'token' in res['data']:
            token = res['data']['token']
            self.setCache("auth_token", f"Bearer {token}")
        return res

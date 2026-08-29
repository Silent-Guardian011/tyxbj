# coding=utf-8
# !/usr/bin/python

"""

作者 丢丢喵 内容均从互联网收集而来 仅供交流学习使用 严禁用于商业用途 请于24小时内删除
         ====================Diudiumiao====================

"""

from Crypto.Util.Padding import unpad
from Crypto.Util.Padding import pad
from urllib.parse import unquote
from Crypto.Cipher import ARC4
from urllib.parse import quote
from base.spider import Spider
from Crypto.Cipher import AES
from datetime import datetime
from bs4 import BeautifulSoup
from base64 import b64decode
import urllib.request
import urllib.parse
import datetime
import binascii
import requests
import hashlib
import base64
import json
import time
import uuid
import sys
import re
import os

sys.path.append('..')

xurl = "https://ansj.ejjjaakq.com"  # 首页   YQS3.APP    https://yqs3.app/download/index.html

xurls = "https://pp.ctecdn.com/"

headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
          }

headers = {
    'accept': 'application/json, text/plain, */*',
    'content-type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
          }

class Spider(Spider):

    def getName(self):
        return "丢丢喵"

    def init(self, extend):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def homeVideoContent(self):
        pass

    def homeContent(self, filter):
        result = {"class": []}
        data = self.build_request_data()
        response_data = self.send_header_request(data)
        onse_data = self.process_response(response_data)
        self.extract_classify_data(onse_data, result)
        return result

    def build_request_data(self):
        current_request_id, current_sign = self.generate_request_components()
        return {
            'app_id': '1',
            'version': '1.1.4',
            'device_info': 'pc',
            "request_id": current_request_id,
            "sign": current_sign,
            'uuid': '3089b604-b5ff-476b-b25d-175cb1f37608',
               }

    def send_header_request(self, data):
        response = requests.post(f'{xurl}/api/index/header', headers=headers, json=data)
        return response.text

    def process_response(self, response_data):
        onse_data = self.decrypt_data(response_data)
        return json.loads(onse_data)

    def extract_classify_data(self, onse_data, result):
        for vod in onse_data['data']['classifylist']:
            result["class"].append({
                "type_id": vod['classifyid'],
                "type_name": "集多🌠" + vod['classifyname']
                                  })

    def calculate_sign(self, request_id):
        salt = "kandianying123"
        inner_str = request_id + salt
        inner_hash = hashlib.md5(inner_str.encode('utf-8')).hexdigest()
        outer_str = inner_hash + salt
        sign = hashlib.md5(outer_str.encode('utf-8')).hexdigest()
        return sign

    def generate_request_components(self):
        current_request_id = str(uuid.uuid4())
        current_sign = self.calculate_sign(current_request_id)
        return current_request_id, current_sign

    def decrypt_data(self, encrypted_base64_str):
        base_str = "kandianying123"
        md5_hash = hashlib.md5(base_str.encode('utf-8')).hexdigest()
        key = md5_hash[:16].encode('utf-8')
        iv = md5_hash[16:].encode('utf-8')
        encrypted_bytes = base64.b64decode(encrypted_base64_str)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
        decrypted_str = decrypted_bytes.decode('utf-8')
        return decrypted_str

    def categoryContent(self, cid, pg, filter, ext):
        videos = []
        page = self.get_page_number(pg)
        data = self.build_category_request_data(cid, page)
        response_data = self.send_category_request(data)
        onse_data = self.process_category_response(response_data)
        self.extract_video_data(onse_data, videos)
        return self.build_category_result(videos, pg)

    def get_page_number(self, pg):
        return int(pg) if pg else 1

    def build_category_request_data(self, cid, page):
        current_request_id, current_sign = self.generate_request_components()
        return {
            "page_num": page,
            "page_size": 10,
            "classify_id": cid,
            "filter_type": "popularity",
            "app_id": "1",
            "version": "1.1.4",
            "device_info": "pc",
            "request_id": current_request_id,
            "sign": current_sign,
            "uuid": "3089b604-b5ff-476b-b25d-175cb1f37608"
               }

    def send_category_request(self, data):
        response = requests.post(f'{xurl}/api/vod/search', headers=headers, json=data)
        return response.text

    def process_category_response(self, response_data):
        onse_data = self.decrypt_data(response_data)
        return json.loads(onse_data)

    def extract_video_data(self, onse_data, videos):
        for vod in onse_data['data']['video_list']:
            video = {
                "vod_id": vod['videoid'],
                "vod_name": vod['title'],
                "vod_pic": f"{xurls}{vod['verticalurl']}",
                "vod_remarks": '集多▶️' + vod.get('remark', '暂无')
                    }
            videos.append(video)

    def build_category_result(self, videos, pg):
        return {
            'list': videos,
            'page': pg,
            'pagecount': 9999,
            'limit': 90,
            'total': 999999
               }

    def get_content(self, vod_data):
        if vod_data and 'introduction' in vod_data:
            return '集多🎉为您介绍剧情📢' + vod_data['introduction']
        else:
            return '集多🎉为您介绍剧情📢未知'

    def get_director(self, vod_data):
        if vod_data and 'director_list' in vod_data and vod_data['director_list']:
            return vod_data['director_list'][0].get('name', '')
        else:
            return '未知'

    def get_actor(self, vod_data):
        if vod_data and 'actor_list' in vod_data and vod_data['actor_list']:
            return vod_data['actor_list'][0].get('name', '')
        else:
            return '未知'

    def get_year(self, vod_data):
        if vod_data and 'year' in vod_data:
            return vod_data['year']
        else:
            return '未知'

    def get_area(self, vod_data):
        if vod_data and 'area_name' in vod_data:
            return vod_data['area_name']
        else:
            return '未知'

    def get_xianlu(self, vod_data):
        xianlu_values = [vod['player_name'] for vod in vod_data['player_list']] if vod_data and 'player_list' in vod_data else []
        return '$$$'.join(xianlu_values)

    def get_bofang(self, vod_data):
        bofang = ''
        for vod in vod_data['player_list'] if vod_data and 'player_list' in vod_data else []:
            for sou in vod['ep_list']:
                id = sou['ep_id']
                name = sou['ep_name']
                bofang = bofang + name + '$' + str(id) + '#'
            bofang = bofang[:-1] + '$$$'
        return bofang[:-3]

    def detailContent(self, ids):
        did = ids[0]
        result = {}
        videos = []
        current_request_id, current_sign = self.generate_request_components()
        data = {
            'video_id': int(did),
            'app_id': '1',
            'version': '1.1.4',
            'device_info': 'pc',
            "request_id": current_request_id,
            "sign": current_sign,
            'uuid': '3089b604-b5ff-476b-b25d-175cb1f37608',
               }
        response = requests.post(f'{xurl}/api/vod/info', headers=headers, json=data)
        response_data = response.text
        decrypted_data = self.decrypt_data(response_data)
        onse_data = json.loads(decrypted_data)
        vod_data = onse_data.get('data')
        videos.append({
            "vod_id": did,
            "vod_director": self.get_director(vod_data),
            "vod_actor": self.get_actor(vod_data),
            "vod_year": self.get_year(vod_data),
            "vod_area": self.get_area(vod_data),
            "vod_content": self.get_content(vod_data),
            "vod_play_from": self.get_xianlu(vod_data),
            "vod_play_url": self.get_bofang(vod_data)
                      })
        result['list'] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        data = self.build_player_request_data(id)
        response_data = self.send_player_request(data)
        onse_data = self.process_player_response(response_data)
        play_url = self.extract_play_url(onse_data)
        return self.build_player_result(play_url)

    def build_player_request_data(self, id):
        current_request_id, current_sign = self.generate_request_components()
        return {
            'ep_id': int(id),
            'resolution': 'sd',
            'play_line_id': 1,
            'app_id': '1',
            'version': '1.1.4',
            'device_info': 'pc',
            "request_id": current_request_id,
            "sign": current_sign,
            'uuid': '3089b604-b5ff-476b-b25d-175cb1f37608',
               }

    def send_player_request(self, data):
        response = requests.post(f'{xurl}/api/vod/play_url', headers=headers, json=data)
        return response.text

    def process_player_response(self, response_data):
        decrypted_data = self.decrypt_data(response_data)
        return json.loads(decrypted_data)

    def extract_play_url(self, onse_data):
        return (onse_data.get('data') or {}).get('play_url', '')

    def build_player_result(self, play_url):
        return {
            "parse": 0,
            "playUrl": '',
            "url": play_url,
            "header": headerx
               }

    def searchContentPage(self, key, quick, pg):
        videos = []
        data = self.build_search_request_data(key)
        response_data = self.send_search_request(data)
        onse_data = self.process_search_response(response_data)
        self.extract_search_video_data(onse_data, videos)
        return self.build_search_result(videos, pg)

    def build_search_request_data(self, key):
        current_request_id, current_sign = self.generate_request_components()
        return {
            'keyword': key,
            'next_value': '',
            'app_id': '1',
            'version': '1.1.4',
            'device_info': 'pc',
            "request_id": current_request_id,
            "sign": current_sign,
            'uuid': '3089b604-b5ff-476b-b25d-175cb1f37608',
               }

    def send_search_request(self, data):
        response = requests.post(f'{xurl}/api/search/search', headers=headers, json=data)
        return response.text

    def process_search_response(self, response_data):
        decrypted_data = self.decrypt_data(response_data)
        return json.loads(decrypted_data)

    def extract_search_video_data(self, onse_data, videos):
        for vod in onse_data['data']['video_list']:
            video = {
                "vod_id": vod['videoid'],
                "vod_name": vod['title'],
                "vod_pic": f"{xurls}{vod['verticalurl']}",
                "vod_remarks": '集多▶️' + vod.get('remark', '暂无')
                    }
            videos.append(video)

    def build_search_result(self, videos, pg):
        return {
            'list': videos,
            'page': pg,
            'pagecount': 9999,
            'limit': 90,
            'total': 999999
               }

    def searchContent(self, key, quick, pg="1"):
        return self.searchContentPage(key, quick, '1')

    def localProxy(self, params):
        if params['type'] == "m3u8":
            return self.proxyM3u8(params)
        elif params['type'] == "media":
            return self.proxyMedia(params)
        elif params['type'] == "ts":
            return self.proxyTs(params)
        return None













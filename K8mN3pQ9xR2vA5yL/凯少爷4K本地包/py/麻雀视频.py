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
import sys
import re
import os

sys.path.append('..')

xurl = "https://www.mqtv.cc"

headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
          }

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
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

    def extract_middle_text(self, text, start_str, end_str, pl, start_index1: str = '', end_index2: str = ''):
        if pl == 3:
            plx = []
            while True:
                start_index = text.find(start_str)
                if start_index == -1:
                    break
                end_index = text.find(end_str, start_index + len(start_str))
                if end_index == -1:
                    break
                middle_text = text[start_index + len(start_str):end_index]
                plx.append(middle_text)
                text = text.replace(start_str + middle_text + end_str, '')
            if len(plx) > 0:
                purl = ''
                for i in range(len(plx)):
                    matches = re.findall(start_index1, plx[i])
                    output = ""
                    for match in matches:
                        match3 = re.search(r'(?:^|[^0-9])(\d+)(?:[^0-9]|$)', match[1])
                        if match3:
                            number = match3.group(1)
                        else:
                            number = 0
                        if 'http' not in match[0]:
                            output += f"#{match[1]}${number}{xurl}{match[0]}"
                        else:
                            output += f"#{match[1]}${number}{match[0]}"
                    output = output[1:]
                    purl = purl + output + "$$$"
                purl = purl[:-3]
                return purl
            else:
                return ""
        else:
            start_index = text.find(start_str)
            if start_index == -1:
                return ""
            end_index = text.find(end_str, start_index + len(start_str))
            if end_index == -1:
                return ""

        if pl == 0:
            middle_text = text[start_index + len(start_str):end_index]
            return middle_text.replace("\\", "")

        if pl == 1:
            middle_text = text[start_index + len(start_str):end_index]
            matches = re.findall(start_index1, middle_text)
            if matches:
                jg = ' '.join(matches)
                return jg

        if pl == 2:
            middle_text = text[start_index + len(start_str):end_index]
            matches = re.findall(start_index1, middle_text)
            if matches:
                new_list = [f'{item}' for item in matches]
                jg = '$$$'.join(new_list)
                return jg

    def homeContent(self, filter):
        result = {"class": []}
        res = self.fetch_home_page_content()
        doc = self.parse_html_content(res)
        soups = self.extract_navigation_elements(doc)
        self.process_navigation_items(soups, result)
        return result

    def fetch_home_page_content(self):
        detail = requests.get(f'{xurl}/type/movie', headers=headers)
        detail.encoding = "utf-8"
        return detail.text

    def parse_html_content(self, res):
        return BeautifulSoup(res, "lxml")

    def extract_navigation_elements(self, doc):
        return doc.find_all('div', class_="leo-head-nav-wrap")

    def process_navigation_items(self, soups, result):
        for soup in soups:
            vods = soup.find_all('a')
            for vod in vods:
                name = vod.text.strip()
                id = vod['href']
                result["class"].append({"type_id": id, "type_name": name})

    def get_mqtv_token(self, page_id):
        KEY = 'Mcxos@mucho!nmme'
        json_str = self.convert_to_json_string(page_id)
        b64_1 = self.encode_base64(json_str)
        xor_str = self.perform_xor_encryption(b64_1, KEY)
        b64_2 = self.encode_base64_latin1(xor_str)
        return self.url_encode(b64_2)

    def convert_to_json_string(self, page_id):
        return json.dumps(page_id, separators=(',', ':'))

    def encode_base64(self, json_str):
        return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')

    def perform_xor_encryption(self, b64_1, KEY):
        xor_chars = []
        key_len = len(KEY)
        for i, char in enumerate(b64_1):
            code = ord(char) ^ ord(KEY[i % key_len])
            xor_chars.append(chr(code))
        return "".join(xor_chars)

    def encode_base64_latin1(self, xor_str):
        return base64.b64encode(xor_str.encode('latin-1')).decode('utf-8')

    def url_encode(self, b64_2):
        return quote(b64_2, safe='')

    def get_target_pageid(self, xurl, headers):
        res = self.fetch_page_content(xurl, headers)
        pageid = self.extract_pageid_from_content(res)
        target_pageid = self.get_mqtv_token(pageid)
        return target_pageid

    def fetch_page_content(self, xurl, headers):
        detail = requests.get(f'{xurl}', headers=headers)
        detail.encoding = "utf-8"
        return detail.text

    def extract_pageid_from_content(self, res):
        return self.extract_middle_text(res, "window.pageid = '", "'", 0)

    def categoryContent(self, cid, pg, filter, ext):
        videos = []
        page = self.parse_page_number(pg)
        updated_headers = self.prepare_headers(cid)
        for attempt in range(10):
            try:
                target_pageid = self.get_target_pageid(xurl, headers)
                params = self.build_category_params(cid, page, target_pageid)
                resp = self.make_category_request(params, updated_headers)
                if self.handle_successful_response(resp, videos):
                    break
                elif self.should_retry_response(resp):
                    continue
                else:
                    break
            except Exception:
                continue
        return self.build_category_result(videos, page)

    def parse_page_number(self, pg):
        return int(pg) if pg else 1

    def prepare_headers(self, cid):
        updated_headers = headers.copy()
        updated_headers['referer'] = f'{xurl}{cid}'
        updated_headers['x-requested-with'] = 'XMLHttpRequest'
        return updated_headers

    def build_category_params(self, cid, page, target_pageid):
        return {'type': cid.split('/')[-1],'rank': 'rankhot','cat': '','year': '','area': '','page': page,'token': target_pageid,}

    def make_category_request(self, params, updated_headers):
        return requests.get(f'{xurl}/libs/VodList.api.php', params=params, headers=updated_headers,allow_redirects=False)

    def handle_successful_response(self, resp, videos):
        if resp.status_code == 200:
            try:
                resp.encoding = "utf-8"
                data = resp.json()
                if data.get('data'):
                    self.process_video_data(data['data'], videos)
                    return True
            except Exception:
                pass
        return False

    def process_video_data(self, video_data, videos):
        for vod in video_data:
            try:
                video_item = self.create_video_item(vod)
                videos.append(video_item)
            except Exception:
                continue

    def create_video_item(self, vod):
        vod_id = f"{vod.get('url', '').split('/')[-1]}@{vod.get('type', '')}"
        return {"vod_id": vod_id,"vod_name": vod.get('title', '未知片名'),"vod_pic": vod.get('img', ''),"vod_remarks": vod.get('remark', '暂无备注')}

    def should_retry_response(self, resp):
        return resp.status_code in [301, 302]

    def build_category_result(self, videos, page):
        return {'list': videos,'page': page,'pagecount': 9999,'limit': 90,'total': 999999}

    def detailContent(self, ids):
        did = ids[0]
        result = {}
        videos = []
        fenge = did.split("@")
        updated_headers = self.prepare_detail_headers(fenge)
        for attempt in range(10):
            try:
                target_pageid = self.get_target_pageid(xurl, headers)
                params = self.build_detail_params(fenge, target_pageid)
                detail = self.make_detail_request(params, updated_headers)
                if self.handle_successful_detail_response(detail, did, videos, result):
                    return result
                elif self.should_retry_detail_response(detail):
                    continue
                else:
                    break
            except Exception:
                continue
        return {'list': []}

    def prepare_detail_headers(self, fenge):
        updated_headers = headers.copy()
        updated_headers['referer'] = f'{xurl}/play/{fenge[1]}/{fenge[0]}'
        return updated_headers

    def build_detail_params(self, fenge, target_pageid):
        return {'type': fenge[1],'id': fenge[0],'token': target_pageid,}

    def make_detail_request(self, params, updated_headers):
        return requests.get(f'{xurl}/libs/VodInfo.api.php', params=params, headers=updated_headers, allow_redirects=False)

    def handle_successful_detail_response(self, detail, did, videos, result):
        if detail.status_code == 200:
            detail.encoding = "utf-8"
            data = detail.json()
            if data.get('data'):
                info = data['data']
                vod_play_from_list, vod_play_url_list = self.extract_play_info(info)
                video_item = self.create_detail_video_item(did, info, vod_play_from_list, vod_play_url_list)
                videos.append(video_item)
                result['list'] = videos
                return True
        return False

    def extract_play_info(self, info):
        vod_play_from_list = []
        vod_play_url_list = []
        if 'playinfo' in info:
            for play_source in info['playinfo']:
                vod_play_from_list.append(play_source.get('cnsite', '未知源'))
                urls = self.extract_episode_urls(play_source)
                vod_play_url_list.append("#".join(urls))
        return vod_play_from_list, vod_play_url_list

    def extract_episode_urls(self, play_source):
        urls = []
        for episode in play_source.get('player', []):
            ep_name = episode.get('no', '')
            ep_url = episode.get('url', '')
            urls.append(f"{ep_name}${ep_url}")
        return urls

    def create_detail_video_item(self, did, info, vod_play_from_list, vod_play_url_list):
        return {
            "vod_id": did,
            "vod_name": info.get('title', ''),
            "vod_director": info.get('director', ''),
            "vod_actor": info.get('actor', ''),
            "vod_remarks": info.get('remark', ''),
            "vod_year": info.get('year', ''),
            "vod_area": info.get('area', ''),
            "vod_content": '😸丢丢为您介绍剧情📢' + info.get('des', ''),
            "vod_play_from": "$$$".join(vod_play_from_list),
            "vod_play_url": "$$$".join(vod_play_url_list)
               }

    def should_retry_detail_response(self, detail):
        return detail.status_code in [302, 301]

    def manual_decrypt(self, encrypted_url, raw_text, raw_sort):
        salt = "lemon"
        sorted_str = self.sort_and_combine_chars(raw_text, raw_sort)
        final_str = self.add_salt_to_string(sorted_str, salt)
        md5_hex = self.calculate_md5_hash(final_str)
        iv, key = self.extract_iv_and_key(md5_hex)
        real_url = self.perform_aes_decryption(encrypted_url, key, iv)
        return real_url

    def sort_and_combine_chars(self, raw_text, raw_sort):
        pairs = []
        min_len = min(len(raw_text), len(raw_sort))
        for i in range(min_len):
            pairs.append({'char': raw_text[i], 'sort': raw_sort[i]})
        pairs.sort(key=lambda x: x['sort'])
        return "".join([p['char'] for p in pairs])

    def add_salt_to_string(self, sorted_str, salt):
        return sorted_str + salt

    def calculate_md5_hash(self, final_str):
        return hashlib.md5(final_str.encode('utf-8')).hexdigest()

    def extract_iv_and_key(self, md5_hex):
        iv = md5_hex[0:16].encode('utf-8')
        key = md5_hex[16:32].encode('utf-8')
        return iv, key

    def perform_aes_decryption(self, encrypted_url, key, iv):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_bytes = base64.b64decode(encrypted_url)
        decrypted_bytes = cipher.decrypt(encrypted_bytes)
        return unpad(decrypted_bytes, AES.block_size).decode('utf-8')

    def playerContent(self, flag, id, vipFlags):
        res = self.fetch_player_page_content(id)
        encrypted_url = self.extract_encrypted_url(res)
        raw_text = self.extract_raw_text(res)
        raw_sort = self.extract_raw_sort(res)
        url = self.manual_decrypt(encrypted_url, raw_text, raw_sort)
        return self.build_player_result(url)

    def fetch_player_page_content(self, id):
        detail = requests.get(url=f"https://player.mcue.cc/fun/?url={id}&dmid=tv_41517_1", headers=headers)
        detail.encoding = "utf-8"
        return detail.text

    def extract_encrypted_url(self, res):
        return self.extract_middle_text(res, '"url": "', '"', 0)

    def extract_raw_text(self, res):
        return self.extract_middle_text(res, 'user-scalable=no" id="now_', '"', 0)

    def extract_raw_sort(self, res):
        return self.extract_middle_text(res, 'charset="UTF-8" id="now_', '"', 0)

    def build_player_result(self, url):
        return {"parse": 0,"playUrl": '',"url": url,"header": headerx}

    def decrypt_data(self, encoded_str):
        key = 'Mcxos@mucho!nmme'
        step1_str = self.decode_base64_latin1(encoded_str)
        xor_result_str = self.perform_xor_decryption(step1_str, key)
        step2_str = self.decode_base64_utf8(xor_result_str)
        final_json_str = self.url_decode(step2_str)
        return json.loads(final_json_str)

    def decode_base64_latin1(self, encoded_str):
        step1_bytes = base64.b64decode(encoded_str)
        return step1_bytes.decode('latin1')

    def perform_xor_decryption(self, step1_str, key):
        xor_result = []
        key_len = len(key)
        for i, char in enumerate(step1_str):
            code = ord(char) ^ ord(key[i % key_len])
            xor_result.append(chr(code))
        return "".join(xor_result)

    def decode_base64_utf8(self, xor_result_str):
        step2_bytes = base64.b64decode(xor_result_str)
        return step2_bytes.decode('utf-8')

    def url_decode(self, step2_str):
        return urllib.parse.unquote(step2_str)

    def searchContentPage(self, key, quick, pg):
        videos = []
        updated_headers = self.prepare_search_headers(key)
        for attempt in range(10):
            try:
                target_pageid = self.get_target_pageid(xurl, headers)
                params = self.build_search_params(key, target_pageid)
                detail = self.make_search_request(params, updated_headers)
                if self.handle_successful_search_response(detail, videos):
                    break
                elif self.should_retry_search_response(detail):
                    continue
                else:
                    break
            except Exception:
                continue
        return self.build_search_result(videos, pg)

    def prepare_search_headers(self, key):
        updated_headers = headers.copy()
        updated_headers['referer'] = f'{xurl}/search/{quote(key)}'
        return updated_headers

    def build_search_params(self, key, target_pageid):
        return {'search': key,'token': target_pageid,}

    def make_search_request(self, params, updated_headers):
        return requests.get(f'{xurl}/libs/VodList.api.php', params=params, headers=updated_headers,allow_redirects=False)

    def handle_successful_search_response(self, detail, videos):
        if detail.status_code == 200:
            try:
                detail.encoding = "utf-8"
                json_data = detail.json()
                raw_data = json_data.get('data')
                if raw_data:
                    data = self.decrypt_data(raw_data)
                    if self.has_valid_search_data(data):
                        self.process_search_videos(data, videos)
                        return True
            except Exception:
                pass
        return False

    def has_valid_search_data(self, data):
        return 'vod_all' in data and data['vod_all'] and 'show' in data['vod_all'][0]

    def process_search_videos(self, data, videos):
        for vod in data['vod_all'][0]['show']:
            try:
                video = self.create_search_video_item(vod)
                videos.append(video)
            except Exception:
                continue

    def create_search_video_item(self, vod):
        vod_id = f"{vod.get('url', '').split('/')[-1]}@{vod.get('type')}"
        return {"vod_id": vod_id,"vod_name": vod.get('title'),"vod_pic": vod.get('img'),"vod_remarks": vod.get('remark', '暂无备注')}

    def should_retry_search_response(self, detail):
        return detail.status_code in [301, 302]

    def build_search_result(self, videos, pg):
        return {'list': videos,'page': pg,'pagecount': 1,'limit': 90,'total': 999999}

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













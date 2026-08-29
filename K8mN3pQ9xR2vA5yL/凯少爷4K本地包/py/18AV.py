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
import base64
import json
import time
import sys
import re
import os

sys.path.append('..')

xurl = "https://mjv009.com"

headers = {
    'referer': xurl,
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

    def __init__(self):
        self.sess = requests.Session()
        self.sess.headers.update(headers)
        self.cached_base_url = None

    def extract_middle_text(self, text, start, end, index=0):
        try:
            return text.split(start)[index + 1].split(end)[0]
        except Exception:
            return ""

    def homeContent(self, filter):
        result = {"class": []}
        if not self.cached_base_url:
            success = self.refresh_session()
            if not success:
                return result
        res = self.get_html(self.cached_base_url)
        doc = self.parse_html(res)
        soups = doc.find_all('li', class_="animenu__nav_transparent")
        categories = self.extract_categories(soups)
        result["class"] = categories
        result["class"].append({'type_id': f'{xurl}/zh/dt_random/all/index.html', 'type_name': '国产自拍'})
        return result

    def parse_html(self, html):
        return BeautifulSoup(html, "lxml")

    def extract_categories(self, soups):
        categories = []
        skip_names = ["18av首頁", "18H漫畫", "寫真圖片", "小說", "91", "Hgame"]
        for soup in soups:
            vods = soup.find('a')
            if not vods:
                continue
            name = vods.get_text().strip()
            if name in skip_names:
                continue
            id_url = vods['href']
            categories.append({"type_id": id_url, "type_name": name})
        return categories

    def categoryContent(self, cid, pg, filter, ext):
        page = self.get_page_number(pg)
        cid = self.adjust_cid(cid)
        target_url = self.build_category_url(cid, page)
        res = self.get_html(target_url)
        doc = self.parse_html(res)
        soups = doc.find_all('div', class_="posts")
        videos = self.extract_category_videos(soups)
        return self.build_category_result(videos, pg)

    def get_page_number(self, pg):
        return int(pg) if pg else 1

    def adjust_cid(self, cid):
        return cid.replace('random', 'list')

    def build_category_url(self, cid, page):
        fenge = cid.split("index.html")
        return f'{fenge[0]}{str(page)}.html'

    def parse_html(self, html):
        return BeautifulSoup(html, "lxml")

    def extract_category_videos(self, soups):
        videos = []
        for soup in soups:
            for vod in soup.find_all('div', class_="post"):
                videos.append(self.parse_category_video(vod))
        return videos

    def parse_category_video(self, vod):
        names = vod.find('div', class_="con")
        name = names.text.strip()
        id_url = names.find('a')['href']
        pic_tag = vod.find('img')
        pic = pic_tag['src'] if pic_tag else ""
        return {"vod_id": id_url, "vod_name": name, "vod_pic": pic}

    def build_category_result(self, videos, pg):
        result = {'list': videos}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def jfun_decrypt_v2(self, key_str, iv_str, cipher_raw, base_val=16, xor_val=29):
        base_val = int(base_val)
        split_char = self.get_split_char(base_val)
        parts = self.split_cipher(cipher_raw, split_char)
        decrypted_base64 = self.process_parts(parts, base_val, xor_val)
        key = key_str.encode('utf-8')
        iv = iv_str.encode('utf-8')
        raw_bytes = base64.b64decode(decrypted_base64)
        decrypted_bytes = self.aes_decrypt(key, iv, raw_bytes)
        return self.finalize_result(decrypted_bytes)

    def get_split_char(self, base_val):
        return chr(base_val + 97)

    def split_cipher(self, cipher_raw, split_char):
        return cipher_raw.split(split_char)

    def process_parts(self, parts, base_val, xor_val):
        decrypted_base64 = ""
        for p in parts:
            if not p: continue
            try:
                val = int(p, base_val)
                val = val ^ xor_val
                decrypted_base64 += chr(val)
            except ValueError:
                continue
        return decrypted_base64

    def aes_decrypt(self, key, iv, raw_bytes):
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return cipher.decrypt(raw_bytes)

    def finalize_result(self, decrypted_bytes):
        result = unpad(decrypted_bytes, AES.block_size).decode('utf-8')
        return result

    def refresh_session(self):
        url = f'{xurl}/zh/'
        detail = self.sess.get(url=url)
        detail.encoding = "utf-8"
        res = detail.text
        url2 = self.extract_middle_text(res, 'window.location="', '"', 0)
        if not url2:
            return False
        self.sess.get(url=url2)
        self.cached_base_url = url2
        return True

    def get_html(self, url):
        if not self.cached_base_url:
            self.refresh_session()
        resp = self.sess.get(url)
        resp.encoding = "utf-8"
        if 'window.location="' in resp.text and len(resp.text) < 1000:
            if self.refresh_session():
                resp = self.sess.get(url)
                resp.encoding = "utf-8"
        return resp.text

    def detailContent(self, ids):
        did = ids[0]
        html_content = self.get_html(did)
        my_cipher = self.extract_cipher(html_content)
        my_key = self.extract_key(html_content)
        my_base = self.extract_base(html_content)
        my_iv = self.extract_iv(html_content)
        final_url = self.jfun_decrypt_v2(my_key, my_iv, my_cipher, base_val=my_base)
        response_text = self.fetch_player_response(final_url)
        matches = self.extract_video_matches(response_text)
        bofang = self.build_play_url(matches)
        videos = [self.build_video_data(did, bofang)]
        return {'list': videos}

    def extract_cipher(self, html_content):
        pattern = r"'a_iframe_id_\d+_\d+_\d+',\s*'([a-z0-9u]+)',"
        match = re.search(pattern, html_content)
        return match.group(1)

    def extract_key(self, html_content):
        argdeqweqweqwe_pattern = r"var\s+argdeqweqweqwe\s*=\s*'([a-f0-9]+)';"
        argdeqweqweqwe_match = re.search(argdeqweqweqwe_pattern, html_content)
        return argdeqweqweqwe_match.group(1)

    def extract_base(self, html_content):
        hadeedd252_pattern = r"hadeedd252=(\d+);"
        hadeedd252_match = re.search(hadeedd252_pattern, html_content)
        return hadeedd252_match.group(1)

    def extract_iv(self, html_content):
        hdddedg252_pattern = r"var\s+hdddedg252\s*=\s*'([a-f0-9]+)';"
        hdddedg252_match = re.search(hdddedg252_pattern, html_content)
        return hdddedg252_match.group(1)

    def fetch_player_response(self, final_url):
        params = {'lo': 'on', 'id': final_url}
        response = self.sess.get(f'{xurl}/js/player/play.php', params=params)
        return response.text

    def extract_video_matches(self, response_text):
        video_pattern = r"{src:\s*'([^']+)',\s*type:\s*'([^']+)',\s*size:\s*'(\d+)'"
        return re.findall(video_pattern, response_text)

    def build_play_url(self, matches):
        if len(matches) == 1:
            return matches[0][2] + '$' + matches[0][0]
        else:
            first_url = matches[0][0]
            first_size = matches[0][2]
            if len(matches) > 1:
                second_url = matches[1][0]
                second_size = matches[1][2]
                return second_size + '$' + second_url + '#' + first_size + '$' + first_url
            else:
                return first_size + '$' + first_url

    def build_video_data(self, did, bofang):
        return {"vod_id": did, "vod_play_from": "18AV专线", "vod_play_url": bofang}

    def playerContent(self, flag, id, vipFlags):
        result = {}
        result["parse"] = 0
        result["playUrl"] = ''
        result["url"] = id
        result["header"] = headers
        return result

    def searchContentPage(self, key, quick, pg):
        page = self.get_page_number(pg)
        target_url = self.build_search_url(key, page)
        res = self.get_html(target_url)
        doc = self.parse_html(res)
        soups = doc.find_all('div', class_="posts")
        videos = self.extract_search_videos(soups)
        return self.build_search_result(videos, pg)

    def get_page_number(self, pg):
        return int(pg) if pg else 1

    def build_search_url(self, key, page):
        return f'{xurl}/zh/fc_search/all/{key}/{str(page)}.html'

    def parse_html(self, html):
        return BeautifulSoup(html, "lxml")

    def extract_search_videos(self, soups):
        videos = []
        for soup in soups:
            for vod in soup.find_all('div', class_="post"):
                videos.append(self.parse_search_video(vod))
        return videos

    def parse_search_video(self, vod):
        names = vod.find('div', class_="con")
        name = names.text.strip()
        id_url = names.find('a')['href']
        pic_tag = vod.find('img')
        pic = pic_tag['src'] if pic_tag else ""
        return {"vod_id": id_url, "vod_name": name, "vod_pic": pic}

    def build_search_result(self, videos, pg):
        result = {'list': videos}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

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













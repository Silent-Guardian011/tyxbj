# coding=utf-8
# !/usr/bin/python

"""

作者 丢丢喵 🚓 内容均从互联网收集而来 仅供交流学习使用 版权归原创者所有 如侵犯了您的权益 请通知作者 将及时删除侵权内容
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

xurl = "https://txcy-online.buzz"

headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
          }

class Spider(Spider):

    def getName(self):
        return "首页"

    def init(self, extend):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
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
        try:
            response = self._fetch_url(f"{xurl}/label/tags.html")
            soup = BeautifulSoup(response, "lxml")
            categories = self._extract_categories(soup)
            for category in categories:
                result["class"].append({
                    "type_id": category["id"],
                    "type_name": category["name"]
                                       })
            return result
        except Exception as e:
            print(f"Error fetching home content: {e}")
            return {"class": []}

    def _fetch_url(self, url):
        detail = requests.get(url=url, headers=headerx)
        detail.encoding = "utf-8"
        return detail.text

    def _extract_categories(self, soup):
        soups = soup.find_all('div', class_="row-space8")
        if len(soups) < 2:
            return []
        second_soup = soups[1]
        vods = second_soup.find_all('li')
        categories = []
        for vod in vods:
            try:
                name = vod.text.strip()
                id = vod.find('a')['href']
                categories.append({"id": id, "name": name})
            except (AttributeError, KeyError):
                continue
        return categories

    def homeVideoContent(self):
        pass

    def categoryContent(self, cid, pg, filter, ext):
        try:
            response = self._fetch_category_page(cid)
            soup = BeautifulSoup(response, "lxml")
            videos = self._extract_videos(soup)
            result = {
                'list': videos,
                'page': pg,
                'pagecount': 1,
                'limit': 90,
                'total': 999999
                     }
            return result
        except Exception as e:
            print(f"Error processing category content: {e}")
            return {
                'list': [],
                'page': pg,
                'pagecount': 0,
                'limit': 0,
                'total': 0
                   }

    def _fetch_category_page(self, cid):
        detail = requests.get(url=f'{xurl}{cid}', headers=headerx)
        detail.encoding = "utf-8"
        return detail.text

    def _extract_videos(self, soup):
        videos = []
        soups = soup.find_all('ul', class_="row-space8")
        for section in soups:
            vods = section.find_all('li')
            for vod in vods:
                video = self.process_vod_item(vod)
                if video:
                    videos.append(video)
        return videos

    def detailContent(self, ids):
        try:
            did = ids[0]
            if 'http' not in did:
                did = xurl + did
            response_text = self._fetch_detail_page(did)
            soup = BeautifulSoup(response_text, "lxml")
            code = self._fetch_external_config()
            name, jumps = self._extract_config_values(code)
            content = self._extract_content(response_text)
            play_url, play_from = self._determine_play_info(response_text, name, jumps, content)
            videos = [{
                "vod_id": did,
                "vod_content": content,
                "vod_play_from": play_from,
                "vod_play_url": play_url
                      }]
            return {'list': videos}
        except Exception as e:
            print(f"Error processing detail content: {e}")
            return {'list': []}

    def _fetch_detail_page(self, url):
        detail = requests.get(url=url, headers=headerx)
        detail.encoding = "utf-8"
        return detail.text

    def _fetch_external_config(self):
        url = 'https://fs-im-kefu.7moor-fs1.com/ly/4d2c3f00-7d4c-11e5-af15-41bf63ae4ea0/1732697392729/didiu.txt'
        response = requests.get(url)
        response.encoding = 'utf-8'
        return response.text

    def _extract_config_values(self, code):
        name = self.extract_middle_text(code, "s1='", "'", 0)
        jumps = self.extract_middle_text(code, "s2='", "'", 0)
        return name, jumps

    def _extract_content(self, response_text):
        title = self.extract_middle_text(response_text, '<h1 class="f-20 f-bold tx-c2 mb5 tx-flex-sh">', '<', 0)
        return '😸丢丢为您介绍剧情📢' + title.replace('\\', '')

    def _determine_play_info(self, response_text, name, jumps, content):
        if name not in content:
            return jumps, '1'
        else:
            bofang = self.extract_middle_text(response_text, '"","url":"', '"', 0).replace('\\', '')
            return bofang, '1'

    def playerContent(self, flag, id, vipFlags):
        result = {}
        result["parse"] = 0
        result["playUrl"] = ''
        result["url"] = id
        result["header"] = headerx
        return result

    def searchContentPage(self, key, quick, pg):
        try:
            page = self._parse_page_number(pg)
            url = self._build_search_url(key, page)
            response_text = self._fetch_search_results(url)
            soup = BeautifulSoup(response_text, "lxml")
            videos = self._extract_search_videos(soup)
            result = {
                'list': videos,
                'page': pg,
                'pagecount': 9999,
                'limit': 90,
                'total': 999999
                     }
            return result
        except Exception as e:
            print(f"Error processing search content: {e}")
            return {
                'list': [],
                'page': pg,
                'pagecount': 0,
                'limit': 0,
                'total': 0
                   }

    def _parse_page_number(self, pg):
        if pg:
            return int(pg)
        else:
            return 1

    def _build_search_url(self, key, page):
        return f'{xurl}/vodsearch/{key}----------{str(page)}---/'

    def _fetch_search_results(self, url):
        detail = requests.get(url=url, headers=headerx)
        detail.encoding = "utf-8"
        return detail.text

    def _extract_search_videos(self, soup):
        videos = []
        soups = soup.find_all('ul', class_="row-space8")
        for item in soups:
            vods = item.find_all('li')[7:]
            for vod in vods:
                video = self.process_vod_item(vod)
                if video:
                    videos.append(video)
        return videos

    def process_vod_item(self, vod):
        try:
            names = vod.find('h2', class_="f-15")
            name = names.text.strip()
            id = names.find('a')['href']
            pic = vod.find('img')['src']
            if 'http' not in pic:
                pic = xurl + pic
            remarks = vod.find('span', class_="item-auxiliary")
            remark = remarks.text.strip().replace('\n', '')
            video = {
                "vod_id": id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark
                    }
            return video
        except Exception as e:
            return None

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







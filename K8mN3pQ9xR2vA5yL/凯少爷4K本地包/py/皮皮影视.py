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

xurl = "https://www.pipiysb.com"

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
        result = {}
        result = {"class": [{"type_id": "/films/@1", "type_name": "电影"},
                            {"type_id": "/classify/meiju/@2", "type_name": "美剧"},
                            {"type_id": "/classify/guochan/@2", "type_name": "国产"},
                            {"type_id": "/classify/hanju/@2", "type_name": "韩剧"},
                            {"type_id": "/classify/fanju/@2", "type_name": "番剧"}],
                 }
        return result

    def homeVideoContent(self):
        pass

    def categoryContent(self, cid, pg, filter, ext):
        def get_page_data(url):
            detail = requests.get(url=url, headers=headerx)
            detail.encoding = "utf-8"
            res = detail.text
            return BeautifulSoup(res, "lxml")

        def extract_video_info(vod):
            name = vod.find('img')['alt']
            id = vod.find('div', class_='poster').find('a')['href']
            pic = vod.find('img')['src']
            remarks = vod.find('div', class_="rating")
            remark = remarks.text.strip() if remarks else ""
            return {
                "vod_id": id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark
                   }

        def process_first_type(soup):
            videos = []
            soups = soup.find_all('div', class_="items")
            if len(soups) > 1:
                second_soup = soups[1]
                vods = second_soup.find_all('article')
                for vod in vods:
                    videos.append(extract_video_info(vod))
            return videos

        def process_other_types(soup):
            videos = []
            soups = soup.find_all('div', class_="items")
            for item in soups:
                vods = item.find_all('article')
                for vod in vods:
                    videos.append(extract_video_info(vod))
            return videos

        result = {}
        videos = []
        page = int(pg) if pg else 1
        fenge = cid.split("@")
        url = f'{xurl}{fenge[0]}page/{str(page)}/'
        doc = get_page_data(url)
        if fenge[1] == "1":
            videos = process_first_type(doc)
        else:
            videos = process_other_types(doc)

        result = {'list': videos}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        def get_page_content(url):
            detail = requests.get(url=url, headers=headerx)
            detail.encoding = "utf-8"
            return detail.text

        def parse_tv_content(res):
            doc = BeautifulSoup(res, "lxml")
            pd_element = doc.find('ul', class_="smenu idTabs")
            if not pd_element or "集数" not in pd_element.text.strip():
                return None, None, None, {'msg': '😸丢丢友情提示📢无在线播放'}
            ids_href = doc.find('div', class_="se-q").find('a')['href']
            res1 = get_page_content(ids_href)
            return doc, res, res1, None

        def parse_movie_content(res):
            doc = BeautifulSoup(res, "lxml")
            return doc, res, None, None

        def get_external_config():
            url9 = 'https://fs-im-kefu.7moor-fs1.com/ly/4d2c3f00-7d4c-11e5-af15-41bf63ae4ea0/1732697392729/didiu.txt'
            response = requests.get(url=url9, headers=headerx)
            response.encoding = 'utf-8'
            code = response.text
            name = self.extract_middle_text(code, "s1='", "'", 0)
            jumps = self.extract_middle_text(code, "s2='", "'", 0)
            return name, jumps

        def extract_content_text(res):
            content = '😸丢丢为您介绍剧情📢' + self.extract_middle_text(res, 'class="wp-content">', '</p>', 0)
            return content.replace(' ', '').replace('<p>', '').replace('\n', '')

        def process_tv_episodes(res1, content_text, config_name):
            if config_name not in content_text:
                return None, '1'
            postid = self.extract_middle_text(res1, 'postid:', ',', 0)
            res2 = self.extract_middle_text(res1, 'videourls:[', '],', 0)
            data = json.loads(res2)
            bofang = ''
            for vod in data:
                name = str(vod.get('name', ''))
                url = str(vod.get('url', ''))
                id = f"{url}@{str(postid)}@juji"
                bofang = str(bofang) + name + '$' + id + '#'
            return bofang[:-1], '欢迎观看'

        def process_movie_episodes(doc, content_text, config_name):
            if config_name not in content_text:
                return None, '1'
            postid = doc.find('ul', class_="ajax_mode").find('li')['data-post']
            soups = doc.find_all('ul', class_="ajax_mode")
            bofang = ''
            for item in soups:
                vods = item.find_all('li')
                for vod in vods:
                    name = vod.text.strip()
                    html_string = str(vod)
                    match = re.search(r'data-nume="(\d+)"', html_string)
                    url = int(match.group(1)) - 1
                    id = f"{url}@{str(postid)}@dianying"
                    bofang = str(bofang) + name + '$' + id + '#'
            return bofang[:-1], '欢迎观看'

        did = ids[0]
        result = {}
        videos = []
        if '/tv/' in did:
            res = get_page_content(did)
            doc, _, res1, error_msg = parse_tv_content(res)
            if error_msg:
                return error_msg
        else:
            res = get_page_content(did)
            doc, _, _, _ = parse_movie_content(res)
        config_name, jumps = get_external_config()
        content_text = extract_content_text(res)
        if '/tv/' in did:
            bofang, xianlu = process_tv_episodes(res1, content_text, config_name)
        else:
            bofang, xianlu = process_movie_episodes(doc, content_text, config_name)
        if not bofang:
            bofang = jumps

        videos.append({
            "vod_id": did,
            "vod_content": content_text,
            "vod_play_from": xianlu,
            "vod_play_url": bofang
                      })
        result['list'] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        def get_direct_url(source_url):
            return source_url

        def handle_juji_type(fenge):
            url1 = f"https://www.pipiysb.com/artplayer/?id={fenge[1]}&source=0&ep={fenge[0]}"
            detail = requests.get(url=url1, headers=headerx)
            detail.encoding = "utf-8"
            res = detail.text
            source = self.extract_middle_text(res, "source: '", "'", 0)
            payload = {
                "expires": self.extract_middle_text(res, "expires: '", "'", 0),
                "client": self.extract_middle_text(res, "client: '", "'", 0),
                "nonce": self.extract_middle_text(res, "nonce: '", "'", 0),
                "token": self.extract_middle_text(res, "token: '", "'", 0),
                "source": source
                      }
            response = requests.post(url=source, headers=headerx, json=payload)
            response_data = response.json()
            return response_data['url']

        def handle_movie_type(fenge):
            url1 = f"https://www.pipiysb.com/artplayer/?mvsource={fenge[0]}&id={fenge[1]}&type=hls"
            detail = requests.get(url=url1, headers=headerx)
            detail.encoding = "utf-8"
            res = detail.text
            source = self.extract_middle_text(res, "source: '", "'", 0)
            if not source:
                return "https://api.cenguigui.cn/api/jp/?msg=  丢丢提醒  需要VIP会员!"
            payload = {
                "expires": self.extract_middle_text(res, "expires: '", "'", 0),
                "client": self.extract_middle_text(res, "client: '", "'", 0),
                "nonce": self.extract_middle_text(res, "nonce: '", "'", 0),
                "token": self.extract_middle_text(res, "token: '", "'", 0),
                "source": source
                      }
            response = requests.post(url=source, headers=headerx, json=payload)
            response_data = response.json()
            return response_data['url']

        fenge = id.split("@")
        if 'mp4' in fenge[0]:
            url = get_direct_url(fenge[0])
        elif fenge[2] == "juji":
            url = handle_juji_type(fenge)
        else:
            url = handle_movie_type(fenge)

        result = {}
        result["parse"] = 0
        result["playUrl"] = ''
        result["url"] = url
        result["header"] = headerx
        return result

    def searchContentPage(self, key, quick, pg):
        def get_page_number(page_param):
            return int(page_param) if page_param else 1

        def fetch_search_results(search_key, page_num):
            url = f'{xurl}/page/{str(page_num)}/?s={search_key}'
            detail = requests.get(url=url, headers=headerx)
            detail.encoding = "utf-8"
            return detail.text

        def parse_search_results(html_content):
            doc = BeautifulSoup(html_content, "lxml")
            return doc.find_all('div', class_="result-item")

        def extract_video_info(vod_item):
            names = vod_item.find('div', class_="title")
            name = names.text.strip()
            id = names.find('a')['href']
            pic = vod_item.find('img')['src']
            remarks = vod_item.find('div', class_="meta")
            remark = remarks.text.strip() if remarks else ""
            return {
                "vod_id": id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark
                   }

        def build_result_list(items):
            videos = []
            for vod in items:
                videos.append(extract_video_info(vod))
            return videos

        def create_response(video_list, page_param):
            result = {}
            result['list'] = video_list
            result['page'] = page_param
            result['pagecount'] = 9999
            result['limit'] = 90
            result['total'] = 999999
            return result
        
        page = get_page_number(pg)
        res = fetch_search_results(key, page)
        soups = parse_search_results(res)
        videos = build_result_list(soups)
        result = create_response(videos, pg)
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







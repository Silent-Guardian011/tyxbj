# coding = utf-8
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

xurl = "https://123av.com"  # 备用 123av.ws, 1av.to.

headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
          }

pm = ''

class Spider(Spider):
    global xurl
    global headerx

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

        detail = requests.get(url=xurl + "/zh/genres", headers=headerx)
        detail.encoding = "utf-8"
        res = detail.text

        doc = BeautifulSoup(res, "lxml")

        soups = doc.find_all('div', class_="box-item-list")

        for soup in soups:
            vods = soup.find_all('div', class_="col-lg-3")

            for vod in vods:
                dduo = vod.find('div', class_="text-muted")
                dduo = dduo.text.strip()

                names = vod.find('div', class_="name")
                name = names.text.strip() + "🌋" + dduo

                id = vod.find('a')['href']

                result["class"].append({"type_id": id, "type_name": name})

            return result

    def homeVideoContent(self):
        pass

    def categoryContent(self, cid, pg, filter, ext):
        result = {}
        videos = []

        if pg:
            page = int(pg)
        else:
            page = 1

        url = f'{xurl}/zh/{cid}?page={str(page)}'
        detail = requests.get(url=url, headers=headerx)
        detail.encoding = "utf-8"
        res = detail.text

        doc = BeautifulSoup(res, "lxml")

        soups = doc.find_all('div', class_="box-item-list")

        for soup in soups:
            vods = soup.find_all('div', class_="col-6")

            for vod in vods:
                names = vod.find('div', class_="detail")
                name = names.text.strip()
                fenge = name.split("-")
                name = fenge[2]

                pic = vod.find('img')['data-src']

                id = names.find('a')['href'] + "@" + pic

                remarks = vod.find('div', class_="duration")
                remark = remarks.text.strip()

                video = {
                    "vod_id": id,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": '' + remark
                        }
                videos.append(video)

        result = {'list': videos}
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def detailContent(self, ids):
        global pm
        did = ids[0]
        result = {}
        videos = []
        xianlu = ''
        bofang = ''

        fenge = did.split("@")

        url = f'{xurl}/zh/{fenge[0]}'
        res = requests.get(url=url, headers=headerx)
        res.encoding = "utf-8"
        res = res.text
        doc = BeautifulSoup(res, "lxml")

        url = 'https://fs-im-kefu.7moor-fs1.com/ly/4d2c3f00-7d4c-11e5-af15-41bf63ae4ea0/1732707176882/jiduo.txt'
        response = requests.get(url)
        response.encoding = 'utf-8'
        code = response.text
        name = self.extract_middle_text(code, "s1='", "'", 0)
        Jumps = self.extract_middle_text(code, "s2='", "'", 0)

        dianzan  = " " + self.extract_middle_text(res, '<span ref="counter">', '<', 0, ) + "人点赞❤"
        fbrq = " 时长:" + self.extract_middle_text(res, '时长:', '</div>', 1, '<span>(.*?)</span>')
        content = doc.find('span', class_="genre")
        content = '集多为您介绍剧情📢 ' + content.text.strip() + fbrq + dianzan
        content = content.replace(',', ' ').replace('\n', ' ').replace('/', ' ')

        director = self.extract_middle_text(res, '制作人:', '</div>',1,'href=".*?">(.*?)</a>') + " 集多"

        actor = self.extract_middle_text(res, '女演员:', '</div>',1,'>(.*?)</a>') + " 集多"

        remarks = self.extract_middle_text(res, '标签:', '</div>',1,'>(.*?)</a>')

        year = self.extract_middle_text(res, '发布日期:', '</div>', 1, '<span>(.*?)</span>')

        if name not in content:
            bofang = Jumps
            xianlu = '1'
        else:
            qian = self.extract_middle_text(res, 'Movie({id: ', ',', 0)
            url = f'{xurl}/zh/ajax/v/{qian}/videos'
            detail = requests.get(url=url, headers=headerx)
            detail.encoding = "utf-8"
            data = detail.json()
            url1 = data['result']['watch'][0]['url']

            url = f'{url1}?poster={fenge[1]}'
            res = requests.get(url=url, headers=headerx)
            res.encoding = "utf-8"
            res = res.text

            bofang = self.extract_middle_text(res, 'stream&quot;:&quot;', '&', 0).replace('\\', '')
            xianlu = '深🌋度'

        videos.append({
            "vod_id": did,
            "vod_director": director,
            "vod_actor": actor,
            "vod_remarks": remarks,
            "vod_year": year,
            "vod_content": content,
            "vod_play_from": xianlu,
            "vod_play_url": bofang
                     })

        result['list'] = videos
        return result

    def playerContent(self, flag, id, vipFlags):

        result = {}
        result["parse"] = 0
        result["playUrl"] = ''
        result["url"] = id
        result["header"] = headerx
        return result

    def searchContentPage(self, key, quick, page):
        pass

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





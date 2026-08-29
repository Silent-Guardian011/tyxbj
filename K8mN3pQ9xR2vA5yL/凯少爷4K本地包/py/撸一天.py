# coding=utf-8
import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider():
        def fetch(self, url, headers=None, timeout=10):
            try:
                res = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
                res.encoding = 'utf-8'
                return res
            except Exception as e:
                print(f"fetch error: {e}")
                return None

class Spider(BaseSpider):
    def getName(self):
        return "撸一天"

    def init(self, extend=""):
        self.host = "https://luyitian.com"
        self.session = requests.Session()
        # 访问首页获取基础 Cookie
        try:
            self.session.get(self.host, timeout=5)
        except:
            pass
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })

    def fetch(self, url, headers=None, timeout=10):
        try:
            req_headers = headers or self.session.headers
            res = self.session.get(url, headers=req_headers, timeout=timeout, allow_redirects=True)
            res.encoding = 'utf-8'
            return res
        except Exception as e:
            print(f"fetch error: {e}")
            return None

    # ---------- 分类首页 ----------
    def homeContent(self, filter):
        result = {}
        result['class'] = [
            {"type_name": "中文字幕", "type_id": "28"},
            {"type_name": "日本中字", "type_id": "51"},
            {"type_name": "日本无码", "type_id": "22"},
            {"type_name": "日本有码", "type_id": "21"},
            {"type_name": "国产精品", "type_id": "26"},
            {"type_name": "国产剧情", "type_id": "27"},
            {"type_name": "国产自拍", "type_id": "29"},
            {"type_name": "国产主播", "type_id": "35"},
            {"type_name": "欧美精品", "type_id": "104"},
            {"type_name": "动漫精品", "type_id": "103"},
            {"type_name": "韩国主播", "type_id": "37"},
            {"type_name": "Cosplay", "type_id": "106"},
            {"type_name": "人妻", "type_id": "31"},
            {"type_name": "素人", "type_id": "44"}
        ]
        result['list'] = []
        result['filters'] = {}
        return result

    # ---------- 分类列表 ----------
    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 999, "limit": 20, "total": 9999}
        url = f"{self.host}/vodtype/{tid}-{pg}/"
        res = self.fetch(url, headers={'Referer': self.host})
        if not res:
            return result

        soup = BeautifulSoup(res.text, 'html.parser')
        vod_list = []
        items = (soup.select('div#mdym > div') or
                 soup.select('.stui-vodlist__item') or
                 soup.select('.myui-vodlist__box') or
                 soup.select('.video-item') or
                 soup.select('.item') or
                 soup.select('.vodlist_item'))

        for item in items:
            a = item.select_one('a') or item.find('a')
            if not a:
                continue

            href = a.get('href', '')
            vid_match = re.search(r'/vodplay/(\d+)', href)
            vid = vid_match.group(1) if vid_match else href

            name = ""
            img = item.select_one('img')
            if img and img.get('alt'):
                name = img['alt']
            if not name and a.get('title'):
                name = a['title']
            if not name:
                title_elem = item.select_one('.title') or item.select_one('.name') or item.select_one('.text')
                if title_elem:
                    name = title_elem.get_text(strip=True)
            if not name:
                name = a.get_text(strip=True)
            if not name:
                name = "未知标题"

            pic = ""
            if img:
                pic = img.get('data-src') or img.get('src', '')
                if pic and not pic.startswith('http'):
                    pic = urljoin(self.host, pic)

            remark = ""
            remark_elem = item.select_one('.remarks') or item.select_one('.note') or item.select_one('.tag')
            if remark_elem:
                remark = remark_elem.get_text(strip=True)
            elif item.text.strip():
                lines = [l.strip() for l in item.text.split('\n') if l.strip()]
                if lines:
                    remark = lines[-1][:20]

            vod_list.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": remark
            })

        result['list'] = vod_list
        page_elem = soup.select_one('.page .page-link, .pagination a')
        if page_elem:
            try:
                last_page = int(re.search(r'(\d+)', page_elem.get('href', '')).group(1)) if 'href' in page_elem.attrs else 1
                result['pagecount'] = max(last_page, 1)
            except:
                pass
        return result

    # ---------- 详情 ----------
    def detailContent(self, ids):
        vid = ids[0]
        url = f"{self.host}/vodplay/{vid}-1-1/"
        res = self.fetch(url, headers={'Referer': self.host})
        if not res:
            return {"list": []}

        soup = BeautifulSoup(res.text, 'html.parser')
        raw_title = soup.title.text.split('|')[0].replace('在线播放在线观看','').replace('《','').replace('》','').strip()

        vod = {
            "vod_id": vid,
            "vod_name": raw_title,
            "vod_type": "视频",
            "vod_content": "撸一天资源",
            "vod_play_from": "Luyitian",
            # 关键修改：分隔符由 # 改为 $
            "vod_play_url": f"播放${vid}-1-1"
        }
        return {"list": [vod]}

    # ---------- 搜索 ----------
    def searchContent(self, key, quick, pg=1):
        url = f"{self.host}/vodsearch/{key}----------{pg}---/"
        res = self.fetch(url, headers={'Referer': self.host})
        if not res:
            return {"list": []}

        soup = BeautifulSoup(res.text, 'html.parser')
        vod_list = []
        items = (soup.select('div#mdym > div') or
                 soup.select('.stui-vodlist__item') or
                 soup.select('.myui-vodlist__box') or
                 soup.select('.video-item'))

        for item in items:
            a = item.select_one('a') or item.find('a')
            if not a:
                continue

            href = a.get('href', '')
            vid_match = re.search(r'/vodplay/(\d+)', href)
            vid = vid_match.group(1) if vid_match else href

            name = ""
            img = item.select_one('img')
            if img and img.get('alt'):
                name = img['alt']
            if not name and a.get('title'):
                name = a['title']
            if not name:
                title_elem = item.select_one('.title') or item.select_one('.name')
                if title_elem:
                    name = title_elem.get_text(strip=True)
            if not name:
                name = a.get_text(strip=True)
            if not name:
                name = "搜索结果"

            pic = ""
            if img:
                pic = img.get('data-src') or img.get('src', '')

            vod_list.append({
                "vod_id": vid,
                "vod_name": name.strip(),
                "vod_pic": pic,
                "vod_remarks": ""
            })
        return {"list": vod_list}

    # ---------- 播放核心 ----------
    def playerContent(self, flag, id, vipFlags):
        """
        返回播放页 URL，让播放器加载（parse=1），同时携带 Cookie 头
        """
        # 提取真实 vid（去除后面的 -1-1）
        vid_match = re.search(r'^(\d+)', str(id))
        if vid_match:
            real_vid = vid_match.group(1)
        else:
            real_vid = id

        play_url = f"{self.host}/vodplay/{real_vid}/"
        # 请求播放页获取最新 Cookie
        res = self.fetch(play_url, headers={'Referer': self.host})
        if not res:
            return {"parse": 1, "url": play_url}

        # 将当前 Session 的 Cookie 转换为字符串
        cookie_str = "; ".join([f"{k}={v}" for k, v in self.session.cookies.items()])

        # 返回播放页，让播放器加载（parse=1）
        return {
            "parse": 1,
            "url": play_url,
            "header": {
                "User-Agent": self.session.headers['User-Agent'],
                "Referer": self.host,
                "Cookie": cookie_str
            }
        }
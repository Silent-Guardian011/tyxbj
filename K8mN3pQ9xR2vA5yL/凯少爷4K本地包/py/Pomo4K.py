"""
@header({
  searchable: 1,
  filterable: 1,
  quickSearch: 1,
  title: 'Pomo4K',
  lang: 'hipy',
})
"""

# -*- coding: utf-8 -*-
import re, json, urllib.parse
from bs4 import BeautifulSoup
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host = "https://pomo.mom"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36",
        }

    def getName(self):
        return "Pomo4K"

    def homeContent(self, filter):
        return {"class": [
            {"type_id": "huayurm", "type_name": "华语热门"},
            {"type_id": "jiating", "type_name": "家庭影院"},
            {"type_id": "donghuadadiany", "type_name": "动画大电影"},
            {"type_id": "lengmenjiapian", "type_name": "冷门佳片"},
            {"type_id": "paihangbang", "type_name": "TOP250"},
            {"type_id": "sort/12", "type_name": "蓝光原盘"},
            {"type_id": "dianshiju", "type_name": "剧集"},
        ], "filters": {}}

    def homeVideoContent(self):
        return {"list": []}

    def _fetch(self, url):
        try:
            if not url.startswith("http"):
                url = self.host + url
            rsp = self.fetch(url, headers=self.headers)
            return rsp.text if rsp else ""
        except:
            return ""

    def _parse_list(self, html):
        items = []
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select('a[href*="/"]'):
            href = card.get("href", "")
            m = re.search(r'/pomo\.mom/(\d+)$', href) or re.search(r'https?://pomo\.mom/(\d+)$', href)
            if not m:
                continue
            vid = m.group(1)
            img = card.select_one("img")
            if not img:
                continue
            title = img.get("alt", "") or ""
            pic = img.get("src", "") or img.get("data-src", "") or ""
            # 获取备注（如果有）
            remarks = ""
            for tag in card.select(".tag, .badge"):
                t = tag.get_text(strip=True)
                if t:
                    remarks = t
            items.append({
                "vod_id": vid,
                "vod_name": title.strip(),
                "vod_pic": pic.strip(),
                "vod_remarks": remarks,
            })
        return items

    def categoryContent(self, tid, pg, filter, extend):
        try:
            pg = int(pg) if pg and str(pg).isdigit() else 1
            url = f"/{tid}"
            if pg > 1:
                url = f"/{tid}/page/{pg}"
            html = self._fetch(url)
            items = self._parse_list(html)
            # 取分页
            soup = BeautifulSoup(html, "html.parser")
            pages = []
            for a in soup.select("a[href*='page/']"):
                pm = re.search(r'page/(\d+)', a.get("href", ""))
                if pm:
                    pages.append(int(pm.group(1)))
            pc = max(pages) if pages else 1
            return {"page": pg, "pagecount": pc, "limit": 24, "total": 9999, "list": items}
        except:
            return {"page": pg, "pagecount": 1, "limit": 24, "total": 0, "list": []}

    def detailContent(self, ids):
        try:
            if isinstance(ids, list):
                ids = ids[0]
            html = self._fetch(f"/{ids}")
            soup = BeautifulSoup(html, "html.parser")
            # 片名
            title_el = soup.select_one("h2.x-dbjs-title") or soup.select_one("title")
            title = title_el.get_text(strip=True) if title_el else ids
            # 海报
            img_el = soup.select_one("img.x-dbjs-poster-img, .x-dbjs-poster img")
            pic = img_el.get("src", "") if img_el else ""
            # 简介
            desc_el = soup.select_one(".x-dbjs-card .x-dbjs-content, .x-dbjs-card p")
            desc = desc_el.get_text(strip=True) if desc_el else ""
            # 提取meta信息（年份、导演、演员等）
            year = ""
            director = ""
            actor = ""
            for meta_row in soup.select(".meta-row"):
                text = meta_row.get_text(" ", strip=True)
                if "导演" in text:
                    director = text.replace("导演：", "").replace("导演:", "").strip()
                elif "演员" in text or "主演" in text:
                    actor = text.replace("演员：", "").replace("演员:", "").replace("主演：", "").replace("主演:", "").strip()
                elif "时间" in text or "上映" in text:
                    ym = re.search(r'(\d{4})', text)
                    if ym:
                        year = ym.group(1)
            # 播放链接：通过在线播放页面获取
            play_url = f"在线播放${ids}:play"
            return {"list": [{
                "vod_id": ids, "vod_name": title, "vod_pic": pic,
                "vod_year": year, "vod_director": director, "vod_actor": actor,
                "vod_content": desc,
                "vod_play_from": "Pomo在线",
                "vod_play_url": play_url,
            }]}
        except:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        try:
            vid = id.split(":")[0] if ":" in id else id
            html = self._fetch(f"/?plugin=plyr_player&gid={vid}")
            # 匹配 route1Data 中的直接m3u8地址（注意页面中转义了\/）
            m = re.search(r'route1Data\s*=\s*\["([^"]*?)\$(https?:\\?/\\?/[^"]+)"\]', html)
            if m:
                src = m.group(2).replace('\\/', '/')
                return {"parse": 0, "url": src, "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host + "/"}}
            # 尝试调api解析（兜底）
            m2 = re.search(r'route1Data\s*=\s*\["([^"]+)"\]', html)
            if m2:
                raw = m2.group(1)
                parts = raw.split("$", 1)
                src = parts[1] if len(parts) > 1 else parts[0]
                if src.startswith("magnet:"):
                    api_url = f"/content/plugins/plyr_player/api.php?type=parse&url={urllib.parse.quote(src)}"
                    rsp = self.fetch(api_url, headers=self.headers)
                    if rsp:
                        try:
                            data = json.loads(rsp.text)
                            if data.get("url") or (data.get("code") == 200 and data.get("data")):
                                real_url = data.get("url") or data.get("data")
                                return {"parse": 0, "url": real_url, "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host + "/"}}
                        except:
                            pass
                elif src.startswith("http"):
                    return {"parse": 0, "url": src, "header": {"User-Agent": "Mozilla/5.0", "Referer": self.host + "/"}}
        except:
            pass
        return {"parse": 0, "url": ""}

    def searchContent(self, key, quick, pg="1"):
        try:
            wd = urllib.parse.quote(key)
            html = self._fetch(f"/?s={wd}")
            items = self._parse_list(html)
            return {"list": items}
        except:
            return {"list": []}

    def localProxy(self, param=''):
        return {}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False
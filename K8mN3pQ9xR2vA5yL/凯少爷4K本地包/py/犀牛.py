# -*- coding: utf-8 -*-
#!/usr/bin/python
# 遮天法·极道帝兵·万法归一·by24h.com·终极完美版
# 本命帝兵:吞天魔罐|境界:四极境·道宫境·轮海境|规范等级:S
import sys, re, json, base64, html, os, threading, time
from urllib.parse import quote, unquote, urljoin, urlparse

try:
    from base.spider import Spider as BaseSpider
except ImportError:
    class BaseSpider:
        def init(self, extend=""): pass
        def homeContent(self, filter): pass
        def homeVideoContent(self): pass
        def categoryContent(self, tid, pg, filter, extend): pass
        def detailContent(self, ids): pass
        def playerContent(self, flag, id, vipFlags=None): pass
        def searchContent(self, key, quick, pg="1"): pass
        def isVideoFormat(self, url): return False
        def manualVideoCheck(self): return False
        def localProxy(self, param): pass

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    requests = None


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = "https://by24h.com"
        self.name = "ZheTian_by24h_v4"
        self.cms = "v8"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Referer": self.host + "/",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
        }
        self.s = requests.Session() if requests else None
        if self.s:
            self.s.headers.update(self.headers)
            self.s.verify = False
        self._cache = {}
        self._cache_lock = threading.Lock()
        self.AD_KEYWORDS = [
            "ad", "ads", "advert", "preroll", "片头", "广告",
            "/gg/", "banner", "promo", "casino", "博彩", "充值"
        ]
        self._fallback_classes = [
            {"type_id": "1", "type_name": "重生"},
            {"type_id": "2", "type_name": "穿越"},
            {"type_id": "3", "type_name": "爽剧"},
            {"type_id": "4", "type_name": "言情"},
            {"type_id": "5", "type_name": "都市"},
            {"type_id": "6", "type_name": "古装"},
            {"type_id": "7", "type_name": "悬疑"},
            {"type_id": "8", "type_name": "其他"},
        ]
        self._page_patterns = [
            "{host}/dj/{tid}_{pg}.html",
            "{host}/dj/{tid}-{pg}.html",
            "{host}/dj/{tid}/page/{pg}.html",
            "{host}/dj/{tid}.html?page={pg}",
        ]

    def _fetch(self, url, retry=3):
        if not self.s:
            return ""
        for i in range(retry):
            try:
                r = self.s.get(url, timeout=15)
                r.raise_for_status()
                r.encoding = "utf-8"
                return r.text
            except Exception:
                if i == retry - 1:
                    return ""
                time.sleep(1)
        return ""

    def _post(self, url, data=None, retry=3):
        if not self.s:
            return ""
        for i in range(retry):
            try:
                r = self.s.post(url, data=data, timeout=15)
                r.encoding = "utf-8"
                return r.text
            except Exception:
                if i == retry - 1:
                    return ""
                time.sleep(1)
        return ""

    def _clean_text(self, text):
        if not text:
            return ""
        text = html.unescape(str(text))
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _fix_url(self, url):
        if not url:
            return ""
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("/"):
            return self.host + url
        if url.startswith("http"):
            return url
        return self.host + "/" + url

    def _fix_pic(self, pic_url):
        return self._fix_url(pic_url) if pic_url else ""

    def _is_video(self, url):
        return any(ext in url.lower() for ext in [".m3u8", ".mp4", ".flv", ".ts", ".mkv"])

    def init(self, extend=""):
        if extend and extend.startswith("http"):
            self.host = extend.rstrip("/")
            self.headers["Referer"] = self.host + "/"
            if self.s:
                self.s.headers.update({"Referer": self.host + "/"})

    def getName(self):
        return self.name

    def isVideoFormat(self, url):
        return self._is_video(url)

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        try:
            url = unquote(param.get("url", ""))
            if not url.startswith("http"):
                return [404, "text/plain", b"not found"]
            r = self.s.get(url, headers={
                "User-Agent": self.headers["User-Agent"],
                "Referer": self.host + "/",
            }, timeout=20)
            ct = r.headers.get("Content-Type", "application/octet-stream")
            return [200, ct, r.content]
        except Exception:
            return [500, "text/plain", b"error"]

    def homeContent(self, filter):
        try:
            html = self._fetch(self.host + "/")
            classes = self._fetch_classes(html)
            return {"class": classes if classes else self._fallback_classes, "filters": {}}
        except Exception:
            return {"class": self._fallback_classes, "filters": {}}

    def _fetch_classes(self, html):
        if not html:
            return []
        cats = re.findall(
            r'href=["\'](/dj/(\d+)\.html)["\'][^>]*>\s*([^<]+)</a>',
            html
        )
        if not cats:
            cats = re.findall(
                r'href=["\'](/[^"\']*type[^"\']*/(\d+))["\'][^>]*>([^<]+)</a>',
                html
            )
        seen = set()
        classes = []
        for href, tid, name in cats:
            name = self._clean_text(name)
            if name and tid not in seen and not any(x in name for x in ["首页", "排行", "最新"]):
                seen.add(tid)
                classes.append({"type_id": tid, "type_name": name})
        return classes

    def categoryContent(self, tid, pg, filter, extend):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 24, "total": 0}
        try:
            html = ""
            for pat in self._page_patterns:
                url = pat.format(host=self.host, tid=tid, pg=pg)
                html = self._fetch(url)
                if html and "stui-vodlist__item" in html:
                    break
            if not html:
                return result

            videos = []
            items = re.findall(
                r'<li[^>]*class=["\']stui-vodlist__item["\'][^>]*>(.*?)</li>',
                html, re.S
            )
            for item in items:
                try:
                    a_match = re.search(
                        r'<a[^>]+class=["\']stui-vodlist__thumb["\'][^>]+href=["\']([^"\']+)["\'][^>]+title=["\']([^"\']*)["\']',
                        item
                    ) or re.search(
                        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*title=["\']([^"\']*)["\']',
                        item
                    )
                    if not a_match:
                        continue
                    href = a_match.group(1)
                    title = a_match.group(2)
                    img_match = re.search(
                        r'<mip-img[^>]+src=["\']([^"\']+)["\']', item
                    ) or re.search(
                        r'<img[^>]+src=["\']([^"\']+)["\']', item
                    ) or re.search(
                        r'<mip-img[^>]+data-original=["\']([^"\']+)["\']', item
                    ) or re.search(
                        r'<img[^>]+data-original=["\']([^"\']+)["\']', item
                    )
                    pic = img_match.group(1) if img_match else ""
                    status_match = re.search(
                        r'<span[^>]*class=["\']pic-text[^"\']*["\'][^>]*>([^<]+)</span>',
                        item
                    ) or re.search(
                        r'<span[^>]*class=["\']pic-tag[^"\']*["\'][^>]*>([^<]+)</span>',
                        item
                    )
                    status = status_match.group(1).strip() if status_match else ""
                    vid = re.search(r'/duanju/(\d+)\.html', href)
                    vid = vid.group(1) if vid else href
                    videos.append({
                        "vod_id": vid,
                        "vod_name": self._clean_text(title),
                        "vod_pic": self._fix_pic(pic),
                        "vod_remarks": status,
                    })
                except Exception:
                    continue

            result["list"] = videos
            has_next = re.search(
                r'href=["\'](/dj/\d+[_-]?\d+\.html)["\'][^>]*>[^<]*(?:下一页|&gt;|›)</a>',
                html
            ) or re.search(
                r'href=["\'](/dj/\d+\.html\?page=\d+)["\'][^>]*>[^<]*(?:下一页|&gt;|›)</a>',
                html
            )
            if has_next:
                result["pagecount"] = int(pg) + 1
            else:
                result["pagecount"] = 999 if len(videos) >= 24 else int(pg)

            if has_next and int(pg) < 50:
                next_pg = int(pg) + 1
                for pat in self._page_patterns:
                    next_url = pat.format(host=self.host, tid=tid, pg=next_pg)
                    threading.Thread(
                        target=lambda u: self._cache.update({u: self._fetch(u)}),
                        args=(next_url,), daemon=True
                    ).start()
                    break
            return result
        except Exception:
            return result

    def detailContent(self, ids):
        try:
            vid = ids[0] if isinstance(ids, list) else ids
            url = f"{self.host}/duanju/{vid}.html"
            html = self._fetch(url)
            if not html:
                return {"list": []}

            title = re.search(
                r'<h1[^>]*class=["\']title["\'][^>]*>.*?<a[^>]*>(.*?)</a>',
                html, re.S
            ) or re.search(
                r'<h1[^>]*>(.*?)</h1>', html, re.S
            ) or re.search(
                r'<title>(.*?)</title>', html
            )
            title = self._clean_text(title.group(1)) if title else "未知短剧"

            pic = re.search(
                r'<mip-img[^>]+src=["\']([^"\']+)["\']', html
            ) or re.search(
                r'<img[^>]+src=["\']([^"\']+)["\']', html
            ) or re.search(
                r'poster=["\']([^"\']+)["\']', html
            )
            pic = self._fix_pic(pic.group(1)) if pic else ""

            desc = re.search(
                r'<p[^>]*class=["\']desc["\'][^>]*>(.*?)</p>', html, re.S
            ) or re.search(
                r'<div[^>]*class=["\']stui-content__desc["\'][^>]*>(.*?)</div>', html, re.S
            )
            desc = self._clean_text(desc.group(1)) if desc else ""

            play_list = re.findall(
                r'<a[^>]+href=["\'](/play/(\d+)-(\d+)-(\d+)\.html)["\'][^>]*>(.*?)</a>',
                html, re.S
            )
            sources = []
            play_urls = []
            if play_list:
                source_map = {}
                for href, pid, sid, nid, text in play_list:
                    text = self._clean_text(text)
                    if not text or "播放" in text or not text.strip():
                        text = f"线路{int(sid)+1}"
                    if text not in source_map:
                        source_map[text] = []
                    source_map[text].append(
                        f"第{int(nid)+1}集${self.host}{href}"
                    )
                for sname, eps in source_map.items():
                    sources.append(sname)
                    play_urls.append("#".join(eps))
            else:
                sources.append("默认")
                play_urls.append(f"全集${self.host}/play/{vid}-0-0.html")

            return {
                "list": [{
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": pic,
                    "vod_content": desc,
                    "vod_play_from": "$$$".join(sources),
                    "vod_play_url": "$$$".join(play_urls),
                }]
            }
        except Exception:
            return {"list": []}

    def playerContent(self, flag, id, vipFlags=None):
        try:
            if self._is_video(id):
                return {
                    "parse": 0,
                    "url": id,
                    "header": json.dumps({
                        "Referer": self.host + "/",
                        "User-Agent": self.headers["User-Agent"],
                    }),
                }

            html = self._fetch(id) if id.startswith("http") else ""
            if not html:
                return {"parse": 0, "url": id, "header": ""}

            # 第1层：mip-iframe src参数提取
            m = re.search(
                r'<mip-iframe[^>]+src=["\'][^"\']*url=([^"\'\s>]+)["\'\s>]',
                html
            )
            if m:
                real_url = unquote(m.group(1))
                if real_url.startswith("http") and self._is_video(real_url):
                    return self._build_result(real_url)

            # 第2层：标准iframe src
            m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
            if m:
                iframe_src = self._fix_url(m.group(1))
                if self._is_video(iframe_src):
                    return self._build_result(iframe_src, referer=id)
                iframe_html = self._fetch(iframe_src)
                if iframe_html:
                    m2 = re.search(r'(https?://[^\s"<>]+\.m3u8[^\s"<>]*)', iframe_html)
                    if m2:
                        return self._build_result(m2.group(1), referer=iframe_src)

            # 第3层：直接匹配m3u8/mp4
            m = re.search(r'(https?://[^\s"<>]+\.m3u8[^\s"<>]*)', html)
            if m:
                return self._build_result(m.group(1))
            m = re.search(r'(https?://[^\s"<>]+\.mp4[^\s"<>]*)', html)
            if m:
                return self._build_result(m.group(1))

            # 第4层：player_xxxx变量
            m = re.search(r'var\s+(player_\w+)\s*=\s*(\{.*?\});', html, re.S)
            if m:
                try:
                    data = json.loads(m.group(2).replace("\\/", "/"))
                    url = data.get("url", "")
                    if url:
                        return self._build_result(url)
                except Exception:
                    pass

            # 第5层：video标签
            m = re.search(r'<video[^>]*src=["\']([^"\']+)["\']', html, re.I)
            if m:
                return self._build_result(m.group(1))

            # 第6层：source标签
            m = re.search(r'<source[^>]*src=["\']([^"\']+)["\']', html, re.I)
            if m:
                return self._build_result(m.group(1))

            # 第7层：var url/src
            m = re.search(r'var\s+(?:url|src|videoUrl)\s*=\s*["\']([^"\']+)["\']', html)
            if m:
                return self._build_result(m.group(1))

            # 第8层：Base64编码URL
            m = re.search(r'["\']([A-Za-z0-9+/=]{50,})["\']', html)
            if m:
                try:
                    decoded = base64.b64decode(m.group(1)).decode("utf-8")
                    if decoded.startswith("http") and self._is_video(decoded):
                        return self._build_result(decoded)
                except Exception:
                    pass

            # 第9层：location.href跳转
            m = re.search(r'location\.href\s*=\s*["\']([^"\']+)["\']', html)
            if m:
                return self._build_result(m.group(1))

            # 第10层：meta refresh
            m = re.search(r'<meta[^>]+refresh[^>]+url=([^"\']+)', html, re.I)
            if m:
                return self._build_result(m.group(1))

            # 第11层：eval混淆标记嗅探
            m = re.search(r'eval\((.*?)\)', html, re.S)
            if m:
                return {"parse": 1, "url": id, "header": ""}

            # 第12层：通用URL提取
            m = re.search(r'(https?://[^\s"<>]+\.(?:m3u8|mp4|flv))', html)
            if m:
                return self._build_result(m.group(1))

            # 第13层：TVBox嗅探兜底
            return {"parse": 1, "url": id, "header": ""}
        except Exception:
            return {"parse": 0, "url": id, "header": ""}

    def _build_result(self, url, referer=None):
        return {
            "parse": 0,
            "url": url,
            "header": json.dumps({
                "Referer": referer or self.host + "/",
                "User-Agent": self.headers["User-Agent"],
            }),
        }

    def searchContent(self, key, quick, pg="1"):
        result = {"list": [], "page": int(pg), "pagecount": 1, "limit": 24, "total": 0}
        try:
            url = f"{self.host}/search.php?searchtype=5&searchword={quote(key)}&page={pg}"
            html = self._fetch(url)
            if not html:
                return result

            items = re.findall(
                r'<li[^>]*class=["\']stui-vodlist__item["\'][^>]*>(.*?)</li>',
                html, re.S
            )
            for item in items:
                try:
                    a_match = re.search(
                        r'<a[^>]+class=["\']stui-vodlist__thumb["\'][^>]+href=["\']([^"\']+)["\'][^>]+title=["\']([^"\']*)["\']',
                        item
                    ) or re.search(
                        r'<a[^>]+href=["\']([^"\']+)["\'][^>]*title=["\']([^"\']*)["\']',
                        item
                    )
                    if not a_match:
                        continue
                    href = a_match.group(1)
                    title = a_match.group(2)
                    img_match = re.search(
                        r'<mip-img[^>]+src=["\']([^"\']+)["\']', item
                    ) or re.search(r'<img[^>]+src=["\']([^"\']+)["\']', item)
                    pic = img_match.group(1) if img_match else ""
                    status_match = re.search(
                        r'<span[^>]*class=["\']pic-text[^"\']*["\'][^>]*>([^<]+)</span>',
                        item
                    )
                    status = status_match.group(1).strip() if status_match else ""
                    vid = re.search(r'/duanju/(\d+)\.html', href)
                    vid = vid.group(1) if vid else href
                    result["list"].append({
                        "vod_id": vid,
                        "vod_name": self._clean_text(title),
                        "vod_pic": self._fix_pic(pic),
                        "vod_remarks": status,
                    })
                except Exception:
                    continue
            return result
        except Exception:
            return result

    def homeVideoContent(self):
        return self.categoryContent("1", "1", False, {})

    def _clean_m3u8(self, text, base_url=""):
        if not text:
            return ""
        lines = text.splitlines()
        cleaned = []
        skip_next = False
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            if any(kw in line_stripped.lower() for kw in self.AD_KEYWORDS):
                skip_next = True
                continue
            if skip_next and line_stripped.startswith("#EXTINF"):
                skip_next = False
                continue
            if not line_stripped.startswith("#") and not line_stripped.startswith("http"):
                if base_url:
                    line = urljoin(base_url, line_stripped)
            cleaned.append(line)
        return "\n".join(cleaned)

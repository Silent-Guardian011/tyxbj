# coding=utf-8
import sys
import json
import urllib.parse
import re
import requests
from lxml import etree
from Crypto.Cipher import AES
import base64

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "XP天堂18+"

    def init(self, extend=""):
        # 多个备用站点，默认使用第一个可直连的
        self.sites = [
            'https://dzsx5k01kgm6y.cloudfront.net',
            'https://attack.bjidvlyog.com',
            'https://agency.bjidvlyog.com/'
        ]
        self.host = self.sites[0]
        self.UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        self.headers = {
            'User-Agent': self.UA,
            'Referer': self.host + '/'
        }
        # 缓存分类和筛选
        self.cached_classes = []
        self.cached_filters = {}
        self.has_parsed = False
        # 图片解密用的固定密钥（来自 JS）
        self.aes_key = b"f5d965df75336270"   # 16字节 ASCII
        self.aes_iv = b"97b60394abc2fbe1"    # 16字节 ASCII
        requests.packages.urllib3.disable_warnings()

    # ---------- 辅助函数 ----------
    def _fetch(self, url, headers=None, buffer=False):
        """请求页面，返回文本或二进制内容"""
        try:
            h = headers or self.headers
            resp = requests.get(url, headers=h, timeout=10, verify=False)
            if resp.status_code == 200:
                return resp.content if buffer else resp.text
        except:
            pass
        return None

    def _aes_decrypt(self, encrypted_b64):
        """AES/CBC/NoPadding 解密，返回解密后的字节（图片数据）"""
        try:
            raw = base64.b64decode(encrypted_b64)
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.aes_iv)
            decrypted = cipher.decrypt(raw)
            # 去掉填充（NoPadding 但数据可能包含 pkcs7 填充，尝试移除）
            # 这里根据 JS 行为，可能直接返回，但为了保险，我们尝试去掉 PKCS7 填充
            pad_len = decrypted[-1]
            if pad_len < 16:
                decrypted = decrypted[:-pad_len]
            return decrypted
        except:
            return b''

    def _get_real_imgurl(self, imgurl):
        """解密图片地址，返回 data:image 格式的 base64"""
        if not imgurl:
            return ""
        try:
            # 第一步请求加密图片，得到 base64 密文
            enc_data = self._fetch(imgurl, headers={
                "User-Agent": self.UA,
                "Referer": "https://wuabeza.gyqspl.cn/"
            }, buffer=True)
            if not enc_data:
                return ""
            # 解密
            dec_data = self._aes_decrypt(enc_data)
            if not dec_data:
                return ""
            # 转为 base64
            b64 = base64.b64encode(dec_data).decode('utf-8')
            # 判断扩展名
            ext = "jpeg"
            if '.gif' in imgurl.lower():
                ext = "gif"
            elif '.png' in imgurl.lower():
                ext = "png"
            return f"data:image/{ext};base64,{b64}"
        except:
            return ""

    def _fix_vod_name(self, name):
        """修正标题（去掉首尾空格并移除多余标记）"""
        if not name:
            return ""
        name = name.strip()
        # 去除类似 "XXX" 的引号标记（JS 中的逻辑）
        parts = name.split(" ")
        if len(parts) > 2:
            return "".join(parts[1:-1])
        return name

    def _parse_video_list(self, html):
        """通用解析视频列表，返回列表和分页信息"""
        root = etree.HTML(html)
        if root is None:
            return [], 0

        videos = []
        # 选择器 .col-6.col-sm-4.col-lg-3 内的视频卡片
        for el in root.xpath('//div[contains(@class, "col-6") and contains(@class, "col-sm-4") and contains(@class, "col-lg-3")]'):
            a = el.xpath('.//div[contains(@class, "video-img-box")]/a')
            if not a:
                continue
            a = a[0]
            href = a.get('href', '')
            if '/videos/' not in href:
                continue
            vod_id = href
            # 标题
            title_el = el.xpath('.//div[contains(@class, "title")]/a/text()')
            vod_name = self._fix_vod_name(title_el[0].strip() if title_el else "")
            # 图片
            img_el = el.xpath('.//img[contains(@class, "zximg")]')
            img_src = img_el[0].get('z-image-loader-url', '') if img_el else ''
            vod_pic = self._get_real_imgurl(img_src) if img_src else ""
            # 播放数
            watch_el = el.xpath('.//span[contains(@class, "interaction_watch_count_")]/text()')
            watch = watch_el[0].strip() if watch_el else ""
            vod_remarks = watch + "播放" if watch else ""
            # 年份标签
            year_el = el.xpath('.//span[contains(@class, "label")]/text()')
            vod_year = year_el[0].strip() if year_el else ""

            videos.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_year': vod_year,
                'vod_remarks': vod_remarks,
                'land': 1,
                'ratio': 1.78
            })

        # 分页
        page_ul = root.xpath('//ul[contains(@class, "dx-pager")]')
        total = 0
        per_page = 20
        if page_ul:
            total = int(page_ul[0].get('data-rec-total', 0))
            per_page = int(page_ul[0].get('data-rec-per-page', 20))
        pagecount = (total + per_page - 1) // per_page if total > 0 else 1
        return videos, pagecount

    def _parse_classes_and_filters(self, html):
        """解析首页分类和筛选，缓存到 self"""
        root = etree.HTML(html)
        if root is None:
            return [], {}

        classes = []
        filters = {}
        sort_filter = [
            {"key": "sort", "name": "排序", "value": [
                {"n": "最近更新", "v": "update"},
                {"n": "最高收藏", "v": "favorite"},
                {"n": "近期最佳", "v": "hot"},
                {"n": "最多观看", "v": "watch"}
            ]}
        ]

        # 遍历 .app-nav .container
        for container in root.xpath('//div[contains(@class, "app-nav")]//div[contains(@class, "container")]'):
            # 区块标题
            title_box = container.xpath('.//div[contains(@class, "title-box")]/h2/text()')
            if not title_box:
                continue
            block_title = title_box[0].strip()
            # 选片/主题块
            if "选片" in block_title or "主题" in block_title:
                for a in container.xpath('.//a[contains(@class, "tjtagmanager")]'):
                    name = a.text.strip() if a.text else ""
                    href = a.get('href', '')
                    # 去掉排序后缀
                    href = re.sub(r'/(favorite|update|hot|watch)/?$', '', href)
                    if href and name:
                        classes.append({'type_id': href, 'type_name': name})
                        filters[href] = sort_filter
            # 标签块（.tag）
            if container.xpath('.//a[contains(@class, "tag")]'):
                for a in container.xpath('.//a[contains(@class, "tag")]'):
                    name = a.text.strip() if a.text else ""
                    href = a.get('href', '')
                    href = re.sub(r'/(favorite|update|hot|watch)/?$', '', href)
                    if href and name:
                        classes.append({'type_id': href, 'type_name': f"🏷️ {name}"})
                        filters[href] = sort_filter

        # 过滤掉"资讯"和"回家"
        classes = [c for c in classes if "资讯" not in c['type_name'] and "回家" not in c['type_name']]
        return classes, filters

    # ---------- 对外接口 ----------
    def homeVideoContent(self):
        """返回分类列表"""
        if not self.has_parsed:
            html = self._fetch(self.host)
            if html:
                self.cached_classes, self.cached_filters = self._parse_classes_and_filters(html)
                self.has_parsed = True
        return {'class': self.cached_classes}

    def homeContent(self, filter=False):
        """首页内容（分类 + 视频列表）"""
        res = self.homeVideoContent()
        # 获取首页视频列表（实际上是第一个分类的列表，或者直接请求首页）
        # 这里模仿 JS，请求首页或默认分类
        html = self._fetch(self.host)
        if html:
            videos, _ = self._parse_video_list(html)
            res['list'] = videos
        else:
            res['list'] = []
        return res

    def categoryContent(self, tid, pg, filter=False, extend={}):
        """分类页内容"""
        if not tid:
            return {'list': []}
        pg = pg or 1
        sort = extend.get('sort', '')  # 排序参数
        url = f"{self.host}{tid}/{sort}/{pg}/"
        html = self._fetch(url)
        if not html:
            return {'list': []}
        videos, pagecount = self._parse_video_list(html)
        return {'list': videos, 'page': pg, 'pagecount': pagecount, 'limit': 20, 'total': 9999}

    def searchContent(self, key, quick=False, pg="1"):
        """搜索"""
        page = int(pg)
        url = f"{self.host}/search/{urllib.parse.quote(key)}/{page}/"
        html = self._fetch(url)
        if not html:
            return {'list': []}
        root = etree.HTML(html)
        videos = []
        for el in root.xpath('//div[contains(@class, "video-img-box")]'):
            a = el.xpath('.//div[contains(@class, "img-box")]/a')
            if not a:
                continue
            a = a[0]
            vod_id = a.get('href', '')
            img_el = a.xpath('.//img[contains(@class, "zximg")]')
            vod_pic = img_el[0].get('z-image-loader-url', '') if img_el else ''
            vod_pic = self._get_real_imgurl(vod_pic) if vod_pic else ""
            vod_name = img_el[0].get('alt', '') if img_el else ''
            vod_name = self._fix_vod_name(vod_name)
            remarks_el = el.xpath('.//div[contains(@class, "absolute-bottom-right")]//span[contains(@class, "label")]/text()')
            vod_remarks = remarks_el[0].strip() if remarks_el else ""
            videos.append({
                'vod_id': vod_id,
                'vod_name': vod_name,
                'vod_pic': vod_pic,
                'vod_remarks': vod_remarks
            })
        # 分页
        page_ul = root.xpath('//ul[contains(@class, "dx-pager")]')
        total = 0
        per_page = 20
        if page_ul:
            total = int(page_ul[0].get('data-rec-total', 0))
            per_page = int(page_ul[0].get('data-rec-per-page', 20))
        pagecount = (total + per_page - 1) // per_page if total > 0 else 1
        return {'list': videos, 'page': page, 'pagecount': pagecount, 'limit': 20, 'total': 9999}

    def detailContent(self, ids):
        """详情"""
        vid = ids[0]
        url = self.host + vid
        html = self._fetch(url)
        if not html:
            return {'list': []}
        root = etree.HTML(html)
        # 标题
        title_el = root.xpath('//h1[contains(@class, "my-foldable-content")]/text()')
        vod_name = title_el[0].strip() if title_el else ""
        # 图片
        player_el = root.xpath('//*[@id="player"]')
        vod_pic = player_el[0].get('data-src', '') if player_el else ''
        vod_pic = self._get_real_imgurl(vod_pic) if vod_pic else ""
        # 标签
        tags = []
        for a in root.xpath('//h5[contains(@class, "tags")]/a'):
            tag = a.text.strip() if a.text else ""
            if tag:
                tags.append(tag)
        vod_actor = '/'.join(tags) if tags else ""
        vod_class = ' '.join(tags) if tags else ""
        # 简介（包含标签快捷搜索）
        vod_content = "(todo)标签快捷搜索：\n"
        for tag in tags:
            vod_content += f'[a=cr:{{"action":"category","key":"{tag}"}}/]【{tag}】[/a]   '
        # 播放地址 (提取 m3u8)
        m3u8_match = re.search(r'https?://[^\s"\'`]+\.m3u8(?:\?[^\s"\'`]+)?', html)
        hls_url = m3u8_match.group(0) if m3u8_match else ""
        vod_play_from = "hls线路"
        vod_play_url = f"正片${hls_url}" if hls_url else ""
        # 播放量和收藏
        watch_el = root.xpath('//div[contains(@class, "video-info")]//span[contains(@class, "interaction_watch_count_")]/text()')
        watch = watch_el[0].strip() if watch_el else ""
        fav_el = root.xpath('//*[@id="bind_collect_count"]/text()')
        fav = fav_el[0].strip() if fav_el else ""
        vod_remarks = (watch + "播放") if watch else ""
        if fav:
            vod_remarks += f" | {fav}收藏"

        return {'list': [{
            'vod_id': vid,
            'vod_name': vod_name,
            'vod_pic': vod_pic,
            'vod_content': vod_content,
            'vod_actor': vod_actor,
            'vod_class': vod_class,
            'vod_play_from': vod_play_from,
            'vod_play_url': vod_play_url,
            'vod_remarks': vod_remarks
        }]}

    def playerContent(self, flag, id, vipFlags):
        """播放"""
        # id 即为 m3u8 地址（由 detail 提供）
        return {
            'parse': 0,
            'url': id,
            'header': json.dumps({
                "User-Agent": self.UA,
                "Referer": self.host + '/'
            })
        }

    # 为了兼容性，保留旧方法名（可选）
    def home(self, filter):
        return self.homeContent(filter)

    def category(self, tid, pg, filter, extend):
        return self.categoryContent(tid, pg, filter, extend)

    def detail(self, ids):
        return self.detailContent(ids)

    def search(self, key, quick, page):
        return self.searchContent(key, quick, page)

    def play(self, flag, id, vipFlags):
        return self.playerContent(flag, id, vipFlags)
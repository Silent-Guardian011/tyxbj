# -*- coding: utf-8 -*-
# !/usr/bin/python
import requests
import base64
import random
import re
import json
import sys
import urllib.parse
import ssl
import urllib3
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

urllib3.disable_warnings()
sys.path.append('..')
from base.spider import Spider


class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ciphers = (
            'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:'
            'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:'
            'ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:'
            'DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384'
        )
        context = create_urllib3_context(ciphers=ciphers)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(TLSAdapter, self).init_poolmanager(*args, **kwargs)


class Spider(Spider):
    def __init__(self):
        super(Spider, self).__init__()
        self.session = requests.Session()
        self.session.verify = False
        self.session.mount('https://', TLSAdapter())
        self.host = "https://www.tjtcdl.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'Referer': f'{self.host}/',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }

    def getName(self):
        return "茶杯狐-TJTCDL"

    def init(self, extend):
        pass

    def homeContent(self, filter):
        classes = [
            {"type_id": "1", "type_name": "电影"},
            {"type_id": "2", "type_name": "电视剧"},
            {"type_id": "4", "type_name": "动漫"},
            {"type_id": "3", "type_name": "综艺"},
            {"type_id": "5", "type_name": "热门短剧"},
        ]

        filter_dict = {}


        years = [{"n": "全部", "v": ""}] + [{"n": str(y), "v": str(y)} for y in range(2026, 2003, -1)]
        orders = [
            {"n": "按最新", "v": "time"},
            {"n": "按最热", "v": "hits"},
            {"n": "按评分", "v": "score"}
        ]


        movie_classes = ["动作", "喜剧", "爱情", "科幻", "恐怖", "剧情", "战争", "惊悚", "悬疑", "犯罪", "奇幻", "冒险",
                         "动画", "武侠"]
        movie_areas = ["大陆", "香港", "台湾", "美国", "韩国", "日本", "泰国", "新加坡", "马来西亚", "印度", "英国",
                       "法国", "加拿大", "西班牙", "俄罗斯", "其它"]


        tv_classes = ["古装", "战争", "青春偶像", "喜剧", "家庭", "犯罪", "动作", "奇幻", "剧情", "历史", "经典",
                      "乡村", "情景", "商战", "网剧", "其他"]
        tv_areas = ["内地", "韩国", "香港", "台湾", "日本", "美国", "泰国", "英国", "新加坡", "其他"]


        comic_classes = ["科幻", "热血", "推理", "搞笑", "冒险", "萝莉", "校园", "动作", "机战", "运动", "战争", "少年",
                         "少女"]


        show_classes = ["脱口秀", "真人秀", "搞笑", "访谈", "生活", "晚会", "美食", "游戏", "亲子", "旅游", "音乐",
                        "舞蹈"]

        def create_filter(classes_list, areas_list):
            return [
                {"key": "class", "name": "类型",
                 "value": [{"n": "全部", "v": ""}] + [{"n": c, "v": c} for c in classes_list]},
                {"key": "area", "name": "地区",
                 "value": [{"n": "全部", "v": ""}] + [{"n": a, "v": a} for a in areas_list]},
                {"key": "year", "name": "年份", "value": years},
                {"key": "by", "name": "排序", "value": orders}
            ]

        # 绑定筛选到各个分类 ID
        filter_dict["1"] = create_filter(movie_classes, movie_areas)
        filter_dict["2"] = create_filter(tv_classes, tv_areas)
        filter_dict["4"] = create_filter(comic_classes, tv_areas)
        filter_dict["3"] = create_filter(show_classes, tv_areas)
        filter_dict["5"] = create_filter(["女频", "男频", "复仇", "甜宠", "穿越", "逆袭", "战神", "脑洞"],
                                         ["内地", "其他"])

        return {
            "class": classes,
            "filters": filter_dict
        }

    def homeVideoContent(self):
        return {'list': []}

    def categoryContent(self, cid, pg, filter, ext):
        page = int(pg)


        ext = ext or {}
        area = ext.get('area', '')
        by = ext.get('by', '')
        class_name = ext.get('class', '')
        lang = ext.get('lang', '')
        letter = ext.get('letter', '')
        year = ext.get('year', '')


        if class_name: class_name = urllib.parse.quote(class_name)
        if area: area = urllib.parse.quote(area)
        if lang: lang = urllib.parse.quote(lang)


        url = f"{self.host}/cupfox-list/{cid}-{area}-{by}-{class_name}-{lang}-{letter}---{page}---{year}.html"

        res = self.session.get(url, headers=self.headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        videos = []
        items = soup.select('.public-list-box')

        for item in items:
            link = item.select_one('.public-list-exp')
            if not link: continue

            href = link.get('href', '')
            vid_match = re.search(r'/chabeihu/(\d+)\.html', href)
            if not vid_match: continue
            vod_id = vid_match.group(1)

            name = link.get('title', '').strip()

            pic_img = link.select_one('img')
            pic = pic_img.get('data-src') or pic_img.get('src') or '' if pic_img else ''

            note_tag = item.select_one('.public-list-prb')
            note = note_tag.text.strip() if note_tag else ''

            videos.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": note
            })

        return {
            'list': videos,
            'page': page,
            'pagecount': 9999,
            'limit': 90,
            'total': 999999
        }

    def detailContent(self, ids):
        did = ids[0]
        url = f"{self.host}/chabeihu/{did}.html"
        res = self.session.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        name, state, actor, director, year, content = "", "", "", "", "", ""

        info_list = soup.select('.info-parameter li')
        for li in info_list:
            em = li.select_one('em')
            if not em: continue

            em_text = em.text.strip()
            val = li.text.replace(em_text, '').replace('\xa0', ' ').strip()

            if '片名' in em_text:
                name = val
            elif '状态' in em_text:
                state = val
            elif '主演' in em_text:
                actor = val
            elif '导演' in em_text:
                director = val
            elif '年份' in em_text:
                year = val
            elif '简介' in em_text:
                content = val

        if not name:
            title_tag = soup.select_one('.this-desc-title')
            name = title_tag.text.strip() if title_tag else ''

        play_from, play_url = [], []
        source_tags = soup.select('.anthology-tab .swiper-slide')
        sources = []
        for s in source_tags:
            badge = s.select_one('.badge')
            if badge: badge.decompose()
            sources.append(s.text.strip())

        play_boxes = soup.select('.anthology-list-box')

        for idx, box in enumerate(play_boxes):
            source_name = sources[idx] if idx < len(sources) else f"线路{idx + 1}"
            ep_tags = box.select('li a')
            eps = []

            for a in ep_tags:
                ep_name = a.text.strip()
                ep_href = a.get('href', '')
                if ep_href:
                    ep_link = ep_href if ep_href.startswith('http') else self.host + ep_href
                    eps.append(f"{ep_name}${ep_link}")

            if eps:
                eps.reverse()
                play_from.append(source_name)
                play_url.append('#'.join(eps))

        return {'list': [{
            "vod_id": did,
            "vod_name": name,
            "vod_actor": actor,
            "vod_director": director,
            "vod_content": content,
            "vod_remarks": state,
            "vod_year": year,
            "vod_play_from": '$$$'.join(play_from),
            "vod_play_url": '$$$'.join(play_url)
        }]}

    def playerContent(self, flag, id, vipFlags):
        res = self.session.get(id, headers=self.headers)
        try:
            text_json = re.findall(r'var player_aaaa=(.*?)</script>', res.text)[0]
            player_data = json.loads(text_json)

            durl = player_data.get('url', '')
            encrypt = player_data.get('encrypt', 0)

            if encrypt == 1:
                durl = urllib.parse.unquote(durl)
            elif encrypt == 2:
                durl = urllib.parse.unquote(durl)
                durl = base64.b64decode(durl).decode('utf-8')
                durl = urllib.parse.unquote(durl)

            return {'parse': 0, 'url': durl}
        except Exception:
            return {'parse': 0, 'url': ''}

    def searchContent(self, key, quick, pg="1"):
        search_url = f'{self.host}/cupfox-search/-------------.html'
        res = self.session.get(search_url, params={'wd': key}, headers=self.headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        videos = []
        items = soup.select('.public-list-box')

        for item in items:
            link = item.select_one('.public-list-exp')
            if not link: continue

            href = link.get('href', '')
            vid_match = re.search(r'/chabeihu/(\d+)\.html', href)
            if not vid_match: continue

            vod_id = vid_match.group(1)
            name = link.get('title', '').strip()

            pic_img = link.select_one('img')
            pic = pic_img.get('data-src') or pic_img.get('src') or '' if pic_img else ''

            note_tag = item.select_one('.public-list-prb')
            note = note_tag.text.strip() if note_tag else ''

            videos.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": note
            })

        return {'list': videos, 'page': int(pg), 'pagecount': 1, 'limit': len(videos), 'total': len(videos)}


if __name__ == '__main__':
    spider = Spider()
    spider.init("")

    print("=================== 分类测试 ===================")
    result = spider.categoryContent(cid="13", pg="1", filter=False, ext={})
    print(json.dumps(result, ensure_ascii=False, indent=2)[:1000] + "\n...")

    print("\n=================== 详情页测试 ===================")
    result = spider.detailContent(["87477"])
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n=================== 播放测试 ===================")
    result = spider.playerContent(flag="PPTV", id="https://www.tjtcdl.com/play/87477-3-1.html", vipFlags=[])
    print(result)
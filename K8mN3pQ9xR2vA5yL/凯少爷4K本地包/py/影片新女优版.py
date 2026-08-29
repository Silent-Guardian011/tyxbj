#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re, os, time, json, sqlite3, threading, random
from datetime import datetime
from urllib.parse import unquote
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

HOST = "https://whos.tv"
OUTPUT_DIR = "/storage/emulated/0/私藏视频/女优库/"
JSON_DIR = os.path.join(OUTPUT_DIR, "女优详情")
VIDEO_LIB_JSON_DIR = os.path.join(OUTPUT_DIR, "影片库详情")
SCAN_CACHE_DIR = os.path.join(OUTPUT_DIR, "扫描缓存")
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': HOST,
    'Cookie': 'user_language=zh-cn;',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}
REQUEST_TIMEOUT = (10, 20)
MAX_RETRY_PER_REQ = 5
DELAY_BETWEEN_REQUESTS = (0.3, 1.0)

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(VIDEO_LIB_JSON_DIR, exist_ok=True)
os.makedirs(SCAN_CACHE_DIR, exist_ok=True)

PBAR_FMT = '{desc}: {n_fmt}/{total_fmt} |{bar}| {percentage:3.0f}%'


class WhosTVCrawlerV3:
    def __init__(self):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.aq = Queue()          # 女优队列
        self.vlq = Queue()         # 影片库队列
        self.rkq = Queue()         # 排行榜队列
        self.ap = None
        self.vdp = None
        self.vlp = None
        self.lk = threading.Lock()
        self.slk = threading.Lock()
        self.json_lk = threading.Lock()
        self.db = os.path.join(OUTPUT_DIR, "whostv.db")
        self.af = os.path.join(OUTPUT_DIR, "actress_avatars.json")
        self.am = self._load_avatars()
        self.c = sqlite3.connect(self.db, check_same_thread=False)
        self._init_db()
        self.ev = set(r[0] for r in self.c.execute("SELECT vod_id FROM videos"))
        self.et = set(r[0] for r in self.c.execute("SELECT tag_name FROM tags"))
        self.tp = self.pa = self.pv = self.tvl = self.pvl = 0
        self.pa_updated = 0    # 女优库更新的影片数
        self.pvl_updated = 0   # 影片库更新的影片数
        self.ab = self.vb = None
        self.err_actress = []
        self.err_vlib = []

    # ---------- 头像 ----------
    def _load_avatars(self):
        if os.path.exists(self.af):
            try:
                with open(self.af, encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_avatars(self):
        try:
            with open(self.af, 'w', encoding='utf-8') as f:
                json.dump(self.am, f, ensure_ascii=False, indent=2)
        except:
            pass

    # ---------- 数据库 ----------
    def _init_db(self):
        self.c.executescript("""
            CREATE TABLE IF NOT EXISTS videos(
                vod_id TEXT PRIMARY KEY,
                title TEXT,
                pic_url TEXT,
                m3u8_url TEXT,
                vod_remarks TEXT,
                vod_pubdate TEXT,
                vod_area TEXT,
                vod_year TEXT,
                vod_content TEXT,
                vod_play_from TEXT,
                vod_play_url TEXT,
                type_name TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS actresses(
                cate_id TEXT PRIMARY KEY,
                name TEXT,
                avatar TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tags(
                tag_name TEXT PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS video_actress(
                vod_id TEXT,
                cate_id TEXT,
                PRIMARY KEY(vod_id, cate_id)
            );
            CREATE TABLE IF NOT EXISTS video_tag(
                vod_id TEXT,
                tag_name TEXT,
                PRIMARY KEY(vod_id, tag_name)
            );
            CREATE TABLE IF NOT EXISTS actor_ranking(
                vod_id TEXT,
                cate_id TEXT,
                PRIMARY KEY(vod_id, cate_id)
            );
            CREATE TABLE IF NOT EXISTS video_ranking(
                vod_id TEXT,
                cate_id TEXT,
                PRIMARY KEY(vod_id, cate_id)
            );
            CREATE TABLE IF NOT EXISTS video_category(
                vod_id TEXT PRIMARY KEY,
                main_category TEXT
            );
            CREATE TABLE IF NOT EXISTS index_categories(
                category_type TEXT,
                category_name TEXT,
                video_count INTEGER DEFAULT 0,
                cover_image TEXT,
                output_dir TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(category_type, category_name)
            );
            CREATE INDEX IF NOT EXISTS idx_va_c ON video_actress(cate_id);
            CREATE INDEX IF NOT EXISTS idx_va_v ON video_actress(vod_id);
            CREATE INDEX IF NOT EXISTS idx_vt_t ON video_tag(tag_name);
            CREATE INDEX IF NOT EXISTS idx_vt_v ON video_tag(vod_id);
            CREATE INDEX IF NOT EXISTS idx_ic_type ON index_categories(category_type);
            CREATE INDEX IF NOT EXISTS idx_vc_main ON video_category(main_category);
        """)
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('actor_ranking','演员榜',0)")
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('video_ranking','影片榜',0)")
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('actress','AV女优库',0)")
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('tag','AV影片库',0)")
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('cate','有码',0)")
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('cate','无码',0)")
        self.c.execute("INSERT OR IGNORE INTO index_categories(category_type, category_name, video_count) VALUES('cate','4K',0)")
        self.c.commit()

    # ---------- ★ 分类判定 ----------
    @staticmethod
    def classify_video(vod_id, title, detail_tags, card_tags):
        combined_text = f"{vod_id} {title} {' '.join(detail_tags)} {' '.join(card_tags)}".lower()
        if any(kw in combined_text for kw in ['4k', '2160p', 'uhd', '超高清', '四k']):
            return '4K'
        uncensored_kw = ['无码流出', 'uncensored', '无修正', '无码破解', 'fc2', 'fc-2',
                          'fc2-ppv', 'heyzo', 'caribbeancom', '1pondo', '一本道',
                          'カリビアンコム', '加勒比', '东京热', 'tokyo-hot', '天然むすめ']
        if any(kw in combined_text for kw in uncensored_kw):
            return '无码'
        if any(tag in detail_tags + card_tags for tag in ['无码', '無碼', 'uncensored', '无码流出']):
            return '无码'
        if any(tag in detail_tags + card_tags for tag in ['有码', '有碼', 'censored']):
            return '有码'
        if any(tag in detail_tags + card_tags for tag in ['4K', '4k', '2160p']):
            return '4K'
        return '有码'

    def assign_category(self, vod_id, title, detail_tags, card_tags):
        cat = self.classify_video(vod_id, title, detail_tags, card_tags)
        with self.lk:
            self.c.execute("INSERT OR REPLACE INTO video_category VALUES(?,?)", (vod_id, cat))

    # ---------- 网络 ----------
    def fetch(self, url, retries=MAX_RETRY_PER_REQ):
        for i in range(retries):
            try:
                time.sleep(random.uniform(*DELAY_BETWEEN_REQUESTS))
                r = self.s.get(url, timeout=REQUEST_TIMEOUT)
                if r.status_code == 200:
                    return r.text
                elif r.status_code in (429, 503):
                    time.sleep(3 + i * 2)
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
        return ""

    # ---------- 数据库写入 ----------
    def iv(self, v):
        vid = v['vod_id']
        with self.lk:
            if vid in self.ev:
                return False
            try:
                self.c.execute(
                    "INSERT INTO videos VALUES(?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'))",
                    (vid, v.get('vn',''), v.get('vp',''), v.get('m8',''),
                     v.get('vr',''), v.get('vd',''), v.get('va',''),
                     v.get('vy',''), v.get('vc',''), v.get('vf',''),
                     v.get('vu',''), v.get('vt','成人影片')))
                self.ev.add(vid)
                return True
            except:
                return False

    def _update_video(self, v):
        """更新已存在的影片数据，用于关联后补充详情"""
        vid = v['vod_id']
        with self.lk:
            try:
                self.c.execute(
                    """UPDATE videos SET title=?, pic_url=?, m3u8_url=?, vod_remarks=?,
                       vod_pubdate=?, vod_area=?, vod_year=?, vod_content=?,
                       vod_play_from=?, vod_play_url=?, type_name=?
                       WHERE vod_id=?""",
                    (v.get('vn',''), v.get('vp',''), v.get('m8',''),
                     v.get('vr',''), v.get('vd',''), v.get('va',''),
                     v.get('vy',''), v.get('vc',''), v.get('vf',''),
                     v.get('vu',''), v.get('vt','成人影片'), vid))
            except:
                pass

    def lkva(self, vid, cid):
        with self.lk:
            self.c.execute("INSERT OR IGNORE INTO video_actress VALUES(?,?)", (vid, cid))

    def lkvt(self, vid, tag):
        with self.lk:
            if tag not in self.et:
                self.c.execute("INSERT OR IGNORE INTO tags VALUES(?,datetime('now'))", (tag,))
                self.et.add(tag)
            self.c.execute("INSERT OR IGNORE INTO video_tag VALUES(?,?)", (vid, tag))

    def ua(self, cid, nm, av=""):
        with self.lk:
            self.c.execute("INSERT OR REPLACE INTO actresses VALUES(?,?,?,datetime('now'))", (cid, nm, av))

    def update_index_category(self, category_type, category_name, video_count, cover_image="", output_dir=""):
        with self.lk:
            self.c.execute(
                "INSERT OR REPLACE INTO index_categories VALUES(?,?,?,?,?,datetime('now'))",
                (category_type, category_name, video_count, cover_image, output_dir))

    def cmt(self):
        with self.lk:
            self.c.commit()

    # ---------- 解析 ----------
    def _extract_tags(self, soup):
        tags = []
        for c in soup.find_all(class_=re.compile(r'tag', re.I)):
            for a in c.find_all('a'):
                t = a.get_text(strip=True)
                if t and len(t) < 30 and t not in tags:
                    tags.append(t)
        if not tags:
            for a in soup.find_all('a', href=re.compile(r'/videos\?tag=|/tags/')):
                t = a.get_text(strip=True)
                if t and len(t) < 30 and t not in tags:
                    tags.append(t)
        return tags

    def _extract_pic(self, soup):
        og = soup.find('meta', property='og:image')
        if og and og.get('content'):
            return og['content']
        vt = soup.find('video')
        if vt and vt.get('poster'):
            return vt['poster']
        im = soup.find('img', src=re.compile(r'\.(jpg|jpeg|png|webp)'))
        if im and im.get('src'):
            s = im['src']
            return 'https:' + s if s.startswith('//') else s
        return ""

    def pvd(self, vid, title, html):
        soup = BeautifulSoup(html, 'html.parser')
        m8 = re.search(r'https?://[^\s"\'<>]*\.m3u8[^\s"\'<>]*', html)
        m8 = m8.group(0).replace('\\/', '/').replace('\\', '') if m8 else ""
        pic = self._extract_pic(soup)
        tags = self._extract_tags(soup)
        desc = "<p>暂无介绍</p>"
        md = soup.find('meta', attrs={'name': 'description'})
        if md and md.get('content'):
            desc = f"<p>{md['content']}</p>"
        if tags:
            desc += f'<p style="margin-top:8px;color:#666;font-size:12px;"><b>标签：</b>{" | ".join(tags)}</p>'
        pm = re.search(r'(\d{4}-\d{2}-\d{2})', html)
        pd = pm.group(1) if pm else datetime.now().strftime("%Y-%m-%d")
        return {
            "vn": title, "vp": pic, "vr": "HD高清", "vd": pd,
            "va": "日本", "vy": pd[:4], "vc": desc,
            "vf": "whos.tv", "vu": m8, "m8": m8,
            "vt": "成人影片", "tags": tags, "vod_id": vid,
            "vd_director": "whos.tv"
        }

    # ---------- 排行榜 ----------
    def scan_rankings(self):
        print("[排行榜] 正在扫描...")
        html = self.fetch(f"{HOST}/ranking/video")
        if html:
            sp = BeautifulSoup(html, 'html.parser')
            for item in sp.select('a[href*="/actresses/"]')[:100]:
                name = item.get_text(strip=True)
                href = item.get('href', '')
                if name and href:
                    self.rkq.put(('actor', name, href))
            for item in sp.select('a[href*="/videos/"]')[:100]:
                title = item.get_text(strip=True)
                href = item.get('href', '')
                vid = href.split('/')[-1] if '/' in href else ''
                if title and vid and '?' not in vid:
                    self.rkq.put(('video', title, vid))
        print(f"[排行榜] 入队 {self.rkq.qsize()} 项")

    def process_ranking_item(self, task_type, name, identifier):
        try:
            if task_type == 'actor':
                self.ua(identifier, name, "")
                self.c.execute("INSERT OR IGNORE INTO actor_ranking VALUES(?,?)", (identifier, identifier))
            else:
                if identifier not in self.ev:
                    detail_html = self.fetch(f"{HOST}/videos/{identifier}")
                    if detail_html:
                        vdata = self.pvd(identifier, name, detail_html)
                        if self.iv(vdata):
                            self.assign_category(identifier, name, vdata.get('tags', []), [])
                else:
                    # 已存在也要请求详情更新
                    detail_html = self.fetch(f"{HOST}/videos/{identifier}")
                    if detail_html:
                        vdata = self.pvd(identifier, name, detail_html)
                        self._update_video(vdata)
                self.c.execute("INSERT OR IGNORE INTO video_ranking VALUES(?,?)", (identifier, identifier))
        except:
            pass
        finally:
            self.cmt()

    def ranking_worker(self):
        while True:
            try:
                task_type, name, identifier = self.rkq.get_nowait()
            except Empty:
                break
            try:
                self.process_ranking_item(task_type, name, identifier)
            except:
                pass
            finally:
                self.rkq.task_done()

    # ---------- 影片库 ----------
    def scan_video_library(self):
        cache = self._load_scan_cache("video_lib_pages.json")
        if cache:
            print(f"[影片库] 加载扫描缓存：{len(cache)} 页")
            for item in cache:
                self.vlq.put((item['pn'], item['url']))
            self.tvl = len(cache)
            return self.tvl

        print("[影片库] 正在扫描首页...")
        html = self.fetch(f"{HOST}/videos")
        if not html:
            return 0
        sp = BeautifulSoup(html, 'html.parser')
        tag_links = []
        for a in sp.select('a[href*="?tag="]'):
            href = a.get('href','')
            if '/videos?tag=' in href:
                tag_name = href.split('?tag=')[-1]
                if tag_name:
                    tag_links.append(tag_name)
        print(f"[影片库] 发现标签 {len(tag_links)} 个")
        for t in tag_links:
            if t not in self.et:
                self.c.execute("INSERT OR IGNORE INTO tags VALUES(?,datetime('now'))", (t,))
                self.et.add(t)
        self.cmt()

        page_links = sp.select('a[href*="/videos/page-"]')
        if page_links:
            pages = [int(re.search(r'/videos/page-(\d+)', a['href']).group(1))
                     for a in page_links if re.search(r'/videos/page-(\d+)', a['href'])]
            self.tvl = max(pages) if pages else 1
        else:
            self.tvl = 1

        print(f"[影片库] 共 {self.tvl} 页")
        cache_data = []
        for pn in range(1, self.tvl + 1):
            url = f"{HOST}/videos/page-{pn}" if pn > 1 else f"{HOST}/videos"
            self.vlq.put((pn, url))
            cache_data.append({"pn": pn, "url": url})
        self._save_scan_cache("video_lib_pages.json", cache_data)
        return self.tvl

    def _load_scan_cache(self, filename):
        path = os.path.join(SCAN_CACHE_DIR, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return None

    def _save_scan_cache(self, filename, data):
        path = os.path.join(SCAN_CACHE_DIR, filename)
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except:
            pass

    def pvc(self, card):
        try:
            lk = card.find('a', href=re.compile(r'/videos/'))
            if not lk: return None
            vid = lk['href'].split('/')[-1]
            if '?' in vid: return None
            h3, im = card.find('h3'), card.find('img')
            t = h3.get_text(strip=True) if h3 else (im['alt'] if im and im.get('alt') else None)
            if not t: return None
            t = t.replace('$','').replace('#','').replace(',','，').strip()
            pic = ""
            if im:
                ps = im.get('src') or im.get('data-src') or ''
                pic = 'https:' + ps if ps.startswith('//') else ps
            rm = ""
            ts = card.find('span', class_=re.compile(r'time|duration', re.I))
            if ts: rm = ts.get_text(strip=True)
            else:
                tm = re.search(r'(\d+)\s*分钟', card.get_text())
                if tm: rm = f"{tm.group(1)}分钟"
            an = "未知女优"
            al = card.find('a', href=re.compile(r'/actresses/'))
            if al: an = al.get_text(strip=True)
            tags = []
            for sp in card.find_all(['span','div'], class_=re.compile(r'tag|label|badge', re.I)):
                tt = sp.get_text(strip=True)
                if tt and len(tt) < 20 and tt != t and '分钟' not in tt:
                    tags.append(tt)
            return {"vod_id": vid, "vn": t, "vp": pic, "vr": rm, "an": an, "tags": list(set(tags))}
        except:
            return None

    def process_vlib_page(self, pn, url):
        saved = 0
        updated = 0
        page_data = []
        try:
            html = self.fetch(url)
            if not html: return
            sp = BeautifulSoup(html, 'html.parser')
            cards = sp.select('a[href^="/videos/"]')
            seen = set()
            for cd in cards:
                hr = cd.get('href','')
                if hr in seen: continue
                seen.add(hr)
                pr = cd.find_parent('div') or cd.find_parent('li') or cd
                item = self.pvc(pr if pr.name != 'a' else cd)
                if not item: continue

                # 请求详情页（无论是否已存在）
                detail_html = self.fetch(f"{HOST}/videos/{item['vod_id']}")
                if detail_html:
                    vdata = self.pvd(item['vod_id'], item['vn'], detail_html)
                else:
                    vdata = {"vod_id": item['vod_id'], "vn": item['vn'], "vp": item['vp'],
                             "vr": item.get('vr',''), "vd": "", "va": "日本", "vy": "",
                             "vc": "", "vf": "whos.tv", "vu": "", "m8": "",
                             "vt": "成人影片", "tags": item.get('tags', []),
                             "vd_director": "whos.tv"}
                vdata['an'] = item.get('an', '')

                is_new = item['vod_id'] not in self.ev
                if is_new:
                    if self.iv(vdata):
                        saved += 1
                else:
                    self._update_video(vdata)
                    updated += 1

                # 补关联
                if item.get('an','') != "未知女优":
                    self.ua(item['an'], item['an'])
                    self.lkva(item['vod_id'], item['an'])
                for tg in vdata.get('tags', []):
                    self.lkvt(item['vod_id'], tg)
                self.assign_category(item['vod_id'], item['vn'],
                                     vdata.get('tags', []),
                                     item.get('tags', []))
                if is_new:
                    page_data.append({"video": vdata, "tags": vdata.get('tags', [])})

            self.cmt()
            self._save_video_lib_json(page_data)
            print(f"[影片库] 第{pn}页 → 新增{saved}部, 更新{updated}部")
        except:
            self.err_vlib.append((pn, url))
        if self.vb: self.vb.update(1)

    def vlib_worker(self):
        while True:
            try:
                pn, url = self.vlq.get_nowait()
            except Empty:
                break
            try:
                self.process_vlib_page(pn, url)
            except:
                self.err_vlib.append((pn, url))
            finally:
                self.vlq.task_done()

    # ---------- 女优库 ----------
    def scan_actresses(self):
        cache = self._load_scan_cache("actress_list.json")
        if cache:
            print(f"[女优库] 加载扫描缓存：{len(cache)} 人")
            for item in cache:
                self.aq.put((item['cid'], item['name'], item.get('pn',0)))
            self.tp = len(cache)
            return self.tp

        print("[女优库] 正在扫描...")
        html = self.fetch(f"{HOST}/actresses")
        if not html:
            return
        pgs = re.findall(r'/page-(\d+)', html)
        self.tp = max(int(p) for p in pgs) if pgs else 1
        print(f"[女优库] 共 {self.tp} 页")
        cache_data = []
        for pn in range(1, self.tp + 1):
            url = f"{HOST}/actresses" if pn == 1 else f"{HOST}/actresses/page-{pn}"
            ph = self.fetch(url)
            if not ph:
                continue
            sp = BeautifulSoup(ph, 'html.parser')
            for a in sp.find_all('a', href=re.compile(r'/actresses/([^/]+)')):
                cid = re.search(r'/actresses/([^/]+)', a['href']).group(1)
                if cid.lower() == 'actresses' or cid.startswith('page-'):
                    continue
                h3, im = a.find('h3'), a.find('img')
                av, nm = "", ""
                if im:
                    av = im.get('src') or im.get('data-src') or ''
                    if av.startswith('//'): av = 'https:' + av
                nm = h3.get_text(strip=True) if h3 else (im['alt'] if im and im.get('alt') else "")
                if not nm: nm = unquote(cid).replace('-',' ').title()
                if av and cid not in self.am:
                    self.am[cid] = av
                cache_data.append({"cid": cid, "name": nm, "pn": pn})
                self.aq.put((cid, nm, pn))
            self._save_avatars()
            print(f"[女优库] 第{pn}页 → 入队{len(cache_data)}人")
        self._save_scan_cache("actress_list.json", cache_data)
        self.cmt()

    def process_actress(self, cid, nm, pidx):
        try:
            base = f"{HOST}/actresses/{cid}"
            html = self.fetch(base)
            if not html: raise Exception("主页失败")
            pgs = re.findall(r'/page-(\d+)', html)
            mx = max(int(p) for p in pgs) if pgs else 1
            vl = {}
            def parse_list(ph):
                sp = BeautifulSoup(ph, 'html.parser')
                for a in sp.select('a[href^="/videos/"]'):
                    vid = a['href'].split('/')[-1]
                    if '?' in vid: continue
                    h3, im = a.find('h3'), a.find('img')
                    t = h3.get_text(strip=True) if h3 else (im['alt'] if im and im.get('alt') else vid.upper())
                    vl[vid] = t.replace('$','').replace('#','').replace(',','，').strip()
            parse_list(html)
            if mx > 1:
                for p in range(2, mx + 1):
                    ph = self.fetch(f"{base}/page-{p}")
                    if ph: parse_list(ph)
            if not vl:
                with self.slk: self.pa += 1
                if self.ab: self.ab.update(1)
                return
            avatar_url = self.am.get(cid, "")
            self.ua(cid, nm, avatar_url)
            saved = 0
            updated = 0
            saved_vids = []
            for vid, title in vl.items():
                detail_html = self.fetch(f"{HOST}/videos/{vid}")
                if not detail_html:
                    continue
                vdata = self.pvd(vid, title, detail_html)

                is_new = vid not in self.ev
                if is_new:
                    if self.iv(vdata):
                        saved += 1
                else:
                    self._update_video(vdata)
                    updated += 1

                self.lkva(vid, cid)
                for tg in vdata.get('tags', []):
                    self.lkvt(vid, tg)
                self.assign_category(vid, title, vdata.get('tags', []), [])
                if is_new:
                    saved_vids.append(vdata)

            self.cmt()
            self._save_actress_json(cid, nm, saved_vids)
            with self.slk:
                self.pa += 1
                self.pv += saved
                self.pa_updated += updated
            if self.ab: self.ab.update(1)
            msg = f"[女优库] 第{self.pa}/{self.tp}人 → 新增{saved}部"
            if updated > 0:
                msg += f", 更新{updated}部"
            print(msg)
        except:
            self.err_actress.append((cid, nm, pidx))

    def actress_worker(self):
        while True:
            try:
                cid, nm, pidx = self.aq.get_nowait()
            except Empty:
                break
            try:
                self.process_actress(cid, nm, pidx)
            except:
                pass
            finally:
                self.aq.task_done()

    # ---------- JSON ----------
    def _save_json_with_merge(self, base_dir, key_name, key_value, videos):
        if not videos:
            return
        safe_key = re.sub(r'[\\/*?:"<>|]', '_', key_value)[:80]
        json_path = os.path.join(base_dir, f"{safe_key}.json")
        items = [{
            "vod_id": v["vod_id"],
            "vod_name": v.get("vn",""),
            "vod_pic": v.get("vp",""),
            "vod_actor": v.get("an","") or v.get("vod_actor",""),
            "vod_director": v.get("vd_director","whos.tv"),
            "vod_remarks": v.get("vr",""),
            "vod_pubdate": v.get("vd",""),
            "vod_area": v.get("va",""),
            "vod_year": v.get("vy",""),
            "vod_tags": v.get("tags",[]),
            "vod_content": v.get("vc",""),
            "vod_play_from": v.get("vf","whos.tv"),
            "vod_play_url": v.get("vu",""),
            "type_name": v.get("vt","成人影片"),
            "actress_avatar": v.get("actress_avatar","")
        } for v in videos]
        with self.json_lk:
            existing = []
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            existing = data.get('list', [])
                        elif isinstance(data, list):
                            existing = data
                except:
                    pass
            eids = {it['vod_id'] for it in existing}
            for it in items:
                if it['vod_id'] not in eids:
                    existing.append(it)
                    eids.add(it['vod_id'])
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({key_name: key_value, "list": existing, "count": len(existing)},
                              f, ensure_ascii=False, indent=2)
            except:
                pass
            cover = items[0]["vod_pic"] if items else ""
            cat_type = "actress" if base_dir == JSON_DIR else "tag"
            self.update_index_category(cat_type, key_value, len(existing), cover, json_path)

    def _save_actress_json(self, cate_id, cate_name, videos):
        avatar = self.am.get(cate_id, "")
        for v in videos:
            v['actress_avatar'] = avatar
            v['an'] = cate_name
        self._save_json_with_merge(JSON_DIR, "actress", cate_name, videos)

    def _save_video_lib_json(self, videos_with_tags):
        if not videos_with_tags:
            return
        tag_map = {}
        for item in videos_with_tags:
            video = item["video"]
            tags = item.get("tags", [])
            for tag in (tags if tags else ["其他"]):
                tag_map.setdefault(tag, []).append(video)
        for tag, vlist in tag_map.items():
            for v in vlist:
                v['actress_avatar'] = self.am.get(v.get('an',''), '')
            self._save_json_with_merge(VIDEO_LIB_JSON_DIR, "tag", tag, vlist)

    # ---------- 重试 ----------
    def retry_errors(self, max_retry=5):
        retry_a = self.err_actress[:]
        self.err_actress.clear()
        for attempt in range(1, max_retry + 1):
            if not retry_a: break
            next_a = []
            for cid, nm, pidx in retry_a:
                try: self.process_actress(cid, nm, pidx)
                except: next_a.append((cid, nm, pidx))
            retry_a = next_a
        self.err_actress = retry_a
        retry_v = self.err_vlib[:]
        self.err_vlib.clear()
        for attempt in range(1, max_retry + 1):
            if not retry_v: break
            next_v = []
            for pn, url in retry_v:
                try: self.process_vlib_page(pn, url)
                except: next_v.append((pn, url))
            retry_v = next_v
        self.err_vlib = retry_v

    # ---------- 主入口 ----------
    def run(self):
        print("=" * 60)
        print("  WhosTV v3 完整爬取版")
        print("  演员榜 | 影片榜 | AV女优库 | AV影片库")
        print("  不去重，关联后更新数据")
        print("=" * 60)

        t1 = threading.Thread(target=self.scan_actresses)
        t2 = threading.Thread(target=self.scan_video_library)
        t3 = threading.Thread(target=self.scan_rankings)
        t1.start(); t2.start(); t3.start()
        t1.join(); t2.join(); t3.join()
        print("[扫描] 完成")

        self.ap = ThreadPoolExecutor(10)
        self.vdp = ThreadPoolExecutor(50)
        self.vlp = ThreadPoolExecutor(50)

        at = self.aq.qsize()
        vlt = self.tvl
        rkt = self.rkq.qsize()

        if vlt > 0:
            self.vb = tqdm(total=vlt, desc="影片库", unit="页", position=1, bar_format=PBAR_FMT)
        if at > 0:
            self.ab = tqdm(total=at, desc="女优库", unit="人", position=0, bar_format=PBAR_FMT)

        fa, fl, fr = [], [], []
        if at:
            for _ in range(10):
                fa.append(self.ap.submit(self.actress_worker))
        if vlt:
            for _ in range(50):
                fl.append(self.vlp.submit(self.vlib_worker))
        if rkt:
            for _ in range(5):
                fr.append(self.ap.submit(self.ranking_worker))

        print("\n[等待] 多通道爬取中...")
        for f in fa:
            try: f.result()
            except: pass
        print("[女优库] 完成")
        for f in fl:
            try: f.result()
            except: pass
        print("[影片库] 完成")
        for f in fr:
            try: f.result()
            except: pass
        print("[排行榜] 完成")

        self.ap.shutdown(wait=True)
        self.vdp.shutdown(wait=True)
        self.vlp.shutdown(wait=True)

        self.retry_errors()
        self.cmt()

        cur = self.c.execute("SELECT main_category, COUNT(*) FROM video_category GROUP BY main_category")
        for row in cur.fetchall():
            self.update_index_category('cate', row[0], row[1])
        self.cmt()

        self.c.close()
        if self.ab: self.ab.close()
        if self.vb: self.vb.close()

        print(f"\n{'='*60}")
        print(f"  最终统计：")
        print(f"  女优库新增入库: {self.pv} 部")
        print(f"  影片库新增入库: {self.pvl} 部")
        print(f"  女优库更新入库: {self.pa_updated} 部（已存在，更新详情）")
        print(f"  影片库更新入库: {self.pvl_updated} 部（已存在，更新详情）")
        print(f"  影片总计（去重）: {len(self.ev)} 部")
        print(f"{'='*60}")


if __name__ == "__main__":
    WhosTVCrawlerV3().run()
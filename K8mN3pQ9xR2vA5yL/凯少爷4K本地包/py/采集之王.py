# -*- coding: utf-8 -*-
import json
import re
import time
import warnings
import concurrent.futures
import requests
from urllib.parse import unquote

try:
    warnings.filterwarnings('ignore')
    requests.packages.urllib3.disable_warnings()
except Exception:
    pass

from base.spider import Spider

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')

SOURCES = [
    {'key': 'lzi', 'name': '量子', 'api': 'https://cj.lziapi.com/api.php/provide/vod'},
    {'key': 'dyttzy', 'name': '天堂', 'api': 'https://caiji.dyttzyapi.com/api.php/provide/vod'},
    {'key': 'ruyi', 'name': '如意', 'api': 'https://cj.rycjapi.com/api.php/provide/vod'},
    {'key': 'bfzy', 'name': '暴风', 'api': 'https://bfzyapi.com/api.php/provide/vod'},
    {'key': 'ffzy', 'name': '非凡', 'api': 'https://ffzy5.tv/api.php/provide/vod'},
    {'key': 'zy360', 'name': '360', 'api': 'https://360zy.com/api.php/provide/vod'},
    {'key': 'jisu', 'name': '极速', 'api': 'https://jszyapi.com/api.php/provide/vod'},
    {'key': 'zuid', 'name': '最大', 'api': 'https://api.zuidapi.com/api.php/provide/vod'},
    {'key': 'ty', 'name': '天涯', 'api': 'https://tyyszyapi.com/api.php/provide/vod'},
    {'key': 'hhzy', 'name': '火狐', 'api': 'https://hhzyapi.com/api.php/provide/vod'},
    {'key': 'hwzy', 'name': '华为', 'api': 'https://cjhwba.com/api.php/provide/vod'},
    {'key': 'mtzy', 'name': '茅台', 'api': 'https://caiji.maotaizy.cc/api.php/provide/vod'},
    {'key': 'myzy', 'name': '猫眼', 'api': 'https://api.maoyanapi.top/api.php/provide/vod'},
    {'key': 'wsyzy', 'name': '无水印', 'api': 'https://api.wsyzy.net/api.php/provide/vod'},
    {'key': '1080zy', 'name': '1080', 'api': 'https://api.1080zyku.com/inc/api_mac10.php'},
    {'key': '155zy', 'name': '155', 'api': 'https://155api.com/api.php/provide/vod'},
    {'key': 'sdzy', 'name': '闪电', 'api': 'https://sdzyapi.com/api.php/provide/vod'},
    {'key': 'suoni', 'name': '索尼', 'api': 'https://suoniapi.com/api.php/provide/vod'},
    {'key': 'hnzy', 'name': '红牛', 'api': 'https://www.hongniuzy2.com/api.php/provide/vod'},
    {'key': 'hyzy', 'name': '虎牙', 'api': 'https://www.huyaapi.com/api.php/provide/vod'},
    {'key': 'dbzy', 'name': '豆瓣', 'api': 'https://caiji.dbzy.tv/api.php/provide/vod'},
    {'key': 'hhzy2', 'name': '豪华', 'api': 'https://hhzyapi.com/api.php/provide/vod'},
    {'key': 'uku', 'name': '优酷', 'api': 'https://api.ukuapi.com/api.php/provide/vod'},
    {'key': 'ikun', 'name': '爱坤', 'api': 'https://ikunzyapi.com/api.php/provide/vod'},
    {'key': 'wujin', 'name': '无尽', 'api': 'https://api.wujinapi.cc/api.php/provide/vod'},
    {'key': 'guangsu', 'name': '光速', 'api': 'https://api.guangsuapi.com/api.php/provide/vod'},
    {'key': 'wolong', 'name': '卧龙', 'api': 'https://collect.wolongzyw.com/api.php/provide/vod'},
    {'key': 'xinlang', 'name': '新浪', 'api': 'https://api.xinlangapi.com/xinlangapi.php/provide/vod'},
    {'key': 'wwzy', 'name': '旺旺', 'api': 'https://api.wwzy.tv/api.php/provide/vod'},
    {'key': 'yhzy', 'name': '樱花', 'api': 'https://m3u8.apiyhzy.com/api.php/provide/vod'},
    {'key': 'nnzy', 'name': '牛牛', 'api': 'https://api.niuniuzy.me/api.php/provide/vod'},
    {'key': 'baiduyun', 'name': '百度', 'api': 'https://api.apibdzy.com/api.php/provide/vod'},
    {'key': 'subo', 'name': '速播', 'api': 'https://subocaiji.com/api.php/provide/vod'},
    {'key': 'jinying', 'name': '金鹰', 'api': 'https://jinyingzy.com/api.php/provide/vod'},
    {'key': 'piaoling', 'name': '飘零', 'api': 'https://p2100.net/api.php/provide/vod'},
    {'key': 'mozhua', 'name': '魔爪', 'api': 'https://mozhuazy.com/api.php/provide/vod'},
    {'key': 'modu', 'name': '魔都', 'api': 'https://www.mdzyapi.com/api.php/provide/vod'},
    {'key': 'xgzy', 'name': '西瓜', 'api': 'https://caiji.xgzyapi.com/api.php/provide/vod'},
    {'key': '98zy', 'name': '98', 'api': 'https://98zy.vip/api.php/provide/vod'},
    {'key': 'dzzy', 'name': '大众', 'api': 'https://cdn.dzzyapi.com/api.php/provide/vod'},
]

TIMEOUT = 5
MAX_WORKERS = 20
LINE_BATCH = 8
AUX_TIMEOUT = 2
HOME_SOURCES = 3      
CATEGORY_SOURCES = 10 
SEARCH_RESULT_LIMIT = 100 
MAX_RETRIES = 2

CATEGORIES = ['短剧', 'AI漫剧', '国产剧', '香港剧', '韩国剧', '欧美剧', '日本剧', '台湾剧', '泰国剧', '海外剧', '动作片', '喜剧片', '爱情片', '科幻片', '恐怖片', '剧情片', '战争片', '动画片', '纪录片', '电影解说', '大陆综艺', '港台综艺', '日韩综艺', '欧美综艺', '国产动漫', '日韩动漫', '欧美动漫', '伦理片']

_TAG = re.compile(r'<[^>]+>')

def _clean(text):
    if not text:
        return ''
    text = _TAG.sub('', str(text))
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    text = text.replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
    return re.sub(r'\s+', ' ', text).strip()

def _is_direct(url):
    if not url:
        return False
    u = str(url).split('?')[0].lower()
    return u.endswith('.m3u8') or u.endswith('.mp4')

def _same_name(a, b):
    def norm(s):
        s = re.sub(r'[\s·•：:，,。！？!?（）()【】\[\]]', '', _clean(s)).lower()
        return re.sub(r'(国语版|高清版|完整版|全集|正片)$', '', s)
    x, y = norm(a), norm(b)
    return bool(x and y and (x == y or x in y or y in x))

def _category_same(a, b):
    aliases = {'纪录片': '记录片', '记录片': '纪录片', '动漫': '动漫片', '动漫片': '动漫'}
    x = _clean(a)
    y = _clean(b)
    return x == y or aliases.get(x) == y

def _is_blocked(name):
    if not name:
        return False
    name_lower = name.lower()
    block_patterns = [
        r'番外篇?$', r'预告片?$', r'花絮$', r'幕后$',
        r'特辑$', r'先导$', r'宣传片$', r'片段$',
        r'采访$', r'制作特辑$', r'拍摄花絮$'
    ]
    for pattern in block_patterns:
        if re.search(pattern, name_lower):
            return True
    return False

class Spider(Spider):

    def getName(self):
        return '采集之王'

    def init(self, extend=''):
        self.header = {'User-Agent': UA}
        self.timeout = TIMEOUT
        self.session = requests.Session()
        self.session.headers.update(self.header)
        self.sources = SOURCES
        try:
            if extend:
                cfg = json.loads(extend) if isinstance(extend, str) else extend
                enabled = cfg.get('enabled')
                if isinstance(enabled, list) and enabled:
                    keep = [s for s in SOURCES if s['key'] in enabled]
                    if keep:
                        self.sources = keep
        except Exception:
            pass
        self.by_key = {s['key']: s for s in self.sources}
        self._executor = None

    def _get_executor(self):
        if self._executor is None:
            self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
        return self._executor

    def _fetch(self, source, retry=True, timeout=None, **params):
        attempts = MAX_RETRIES if retry else 1
        
        for attempt in range(attempts):
            try:
                api = source['api'].split('?', 1)[0]
                r = self.session.get(api, params=params,
                                   timeout=timeout or self.timeout, verify=False)
                if r.status_code == 200:
                    j = r.json()
                    if isinstance(j, dict):
                        return j
            except Exception:
                pass
            
            if attempt < attempts - 1:
                time.sleep(0.3 * (attempt + 1))
                
        return None

    def _fetch_by_key(self, key, **params):
        src = self.by_key.get(key)
        if not src:
            return None
        return self._fetch(src, **params)

    def _fetch_matches(self, source, name):
        return self._fetch(source, retry=False, timeout=AUX_TIMEOUT, ac='detail', wd=name)

    def _parallel(self, jobs):
        if not jobs:
            return {}
        
        results = {}
        executor = self._get_executor()
        futures = {}
        
        for k, fn in jobs:
            future = executor.submit(self._safe_run, k, fn)
            futures[future] = k
        
        for future in concurrent.futures.as_completed(futures):
            k = futures[future]
            try:
                results[k] = future.result(timeout=self.timeout + 2)
            except Exception:
                results[k] = None
                
        return results

    def _safe_run(self, k, fn):
        try:
            return fn()
        except Exception:
            return None

    def _item(self, vod, src_key, is_search=False):
        prefix = 'search_' if is_search else ''
        return {
            'vod_id': '%s%s:%s' % (prefix, src_key, vod.get('vod_id', '')),
            'vod_name': _clean(vod.get('vod_name', '')) or '未知影片',
            'vod_pic': vod.get('vod_pic', '') or '',
            'vod_remarks': _clean(vod.get('vod_remarks', '')) or '',
        }

    def homeContent(self, filter):
        result = {'class': [{'type_id': name, 'type_name': name}
                            for name in CATEGORIES],
                  'list': []}
        try:
            result['list'] = self._home_list()
        except Exception:
            pass
        return result

    def homeVideoContent(self):
        try:
            return {'list': self._home_list()}
        except Exception:
            return {}

    def _home_list(self):
        if not self.sources:
            return []
        
        sources = self.sources[:HOME_SOURCES]
        jobs = [(s['key'], lambda s=s: self._fetch(s, retry=False, timeout=AUX_TIMEOUT, ac='detail', pg=1)) 
                for s in sources]
        data = self._parallel(jobs)
        
        items = []
        seen = set()
        for s in sources:
            j = data.get(s['key'])
            if not j or not j.get('list'):
                continue
            for v in j['list'][:30]:
                item = self._item(v, s['key'], is_search=False)
                mark = item['vod_id']
                if mark in seen:
                    continue
                seen.add(mark)
                items.append(item)
        return items[:30]

    def _category_fetch(self, source, name, page):
        try:
            meta = self._fetch(source, retry=False, timeout=AUX_TIMEOUT, ac='list', pg=1)
            source_tid = ''
            for item in (meta or {}).get('class', []):
                if _category_same(item.get('type_name', ''), name):
                    source_tid = str(item.get('type_id', '')).strip()
                    break
            if not source_tid:
                return None
            return self._fetch(source, retry=False, timeout=AUX_TIMEOUT,
                             ac='detail', t=source_tid, pg=page)
        except Exception:
            return None

    def categoryContent(self, tid, pg, filter, extend):
        try:
            category_name = unquote(str(tid or '')).strip()
            if not category_name or ':' in category_name:
                return {'list': [], 'page': 1, 'pagecount': 0,
                        'limit': 20, 'total': 0}
            known_names = CATEGORIES
            if category_name not in known_names:
                return {'list': [], 'page': 1, 'pagecount': 0,
                        'limit': 20, 'total': 0}
            page = int(pg) if str(pg).isdigit() else 1

            target_sources = self.sources[:CATEGORY_SOURCES]
            jobs = [(s['key'], lambda s=s: self._category_fetch(
                s, category_name, page)) for s in target_sources]

            data = self._parallel(jobs)
            items = []
            seen = set()
            pagecount = 0

            for s in target_sources:
                j = data.get(s['key'])
                if not j or not j.get('list'):
                    continue
                try:
                    pagecount = max(pagecount, int(j.get('pagecount', 0) or 0))
                except Exception:
                    pass
                for vod in j['list']:
                    try:
                        vid = str(vod.get('vod_id', ''))
                        unique_key = f"{s['key']}:{vid}"
                        if unique_key in seen:
                            continue
                        seen.add(unique_key)
                        items.append(self._item(vod, s['key'], is_search=False))
                    except Exception:
                        continue
            
            total = len(seen)
            limit = 20
            pagecount = max(pagecount, (total + limit - 1) // limit)
            
            return {
                'list': items,
                'page': page,
                'pagecount': pagecount,
                'limit': limit,
                'total': total,
            }
        except Exception:
            return {'list': [], 'page': 1, 'pagecount': 0,
                    'limit': 20, 'total': 0}

    def searchContent(self, key, quick, pg='1'):
        try:
            page = int(pg) if str(pg).isdigit() else 1
            
            if page > 1:
                return {'list': [], 'page': page}
            
            jobs = [(s['key'], lambda s=s: self._fetch(s, retry=False, timeout=3, 
                                                      ac='list', wd=key)) 
                    for s in self.sources]
            data = self._parallel(jobs)

            groups = {}
            order = []
            for s in self.sources:
                j = data.get(s['key'])
                if not j or not j.get('list'):
                    continue
                for v in j['list'][:3]:
                    name = _clean(v.get('vod_name', ''))
                    if not name:
                        continue

                    if _is_blocked(name):
                        continue

                    type_name = _clean(v.get('type_name', ''))
                    year = str(v.get('vod_year', '') or '')
                    gk = (name, year, type_name)
                    if gk not in groups:
                        groups[gk] = []
                        order.append(gk)
                    groups[gk].append((s['key'], v))

            def rank(entry):
                src_key, v = entry
                try:
                    score = float(v.get('vod_score', 0) or 0)
                except Exception:
                    score = 0.0
                remarks = _clean(v.get('vod_remarks', ''))
                bonus = 1 if any(w in remarks for w in ('完结', 'HD', '正片')) else 0
                return (bonus, score)

            result_list = []

            for gk in order:
                entries = groups[gk]
                entries.sort(key=rank, reverse=True)
                for src_key, v in entries:
                    item = self._item(v, src_key, is_search=True)
                    src_name = self.by_key.get(src_key, {}).get('name', src_key)
                    item['vod_remarks'] = f"{src_name} " + _clean(v.get('vod_remarks', ''))
                    result_list.append(item)

            if len(result_list) > SEARCH_RESULT_LIMIT:
                result_list = result_list[:SEARCH_RESULT_LIMIT]

            source_order = {s['key']: idx for idx, s in enumerate(self.sources)}
            result_list.sort(key=lambda x: source_order.get(x['vod_id'].split(':')[0].replace('search_', ''), 999))

            return {'list': result_list, 'page': page}
        except Exception:
            return {'list': [], 'page': 1}

    def detailContent(self, ids):
        try:
            if isinstance(ids, str):
                vid = ids
            else:
                vid = str(ids[0]) if ids else ''

            is_search_result = vid.startswith('search_')
            raw_vid = vid.replace('search_', '')
            key, sep, real_id = raw_vid.partition(':')

            source_map = {s['key']: s for s in self.sources}
            if not sep or not real_id or key not in source_map:
                return {'list': []}
            main_src = source_map[key]

            j = self._fetch(main_src, ac='detail', ids=real_id)
            if not j or not j.get('list'):
                return {'list': []}
            vod = j['list'][0]
            name = _clean(vod.get('vod_name', ''))

            play_froms = []
            play_urls = []
            self._collect_lines(key, vod, play_froms, play_urls)

            if is_search_result:
                play_froms, play_urls = self._deduplicate_playlists(play_froms, play_urls)
                return {'list': [self._build_detail_dict(vid, vod, play_froms, play_urls)]}

            others = [s for s in self.sources if s['key'] != key]
            max_others = 8
            if len(others) > max_others:
                others = others[:max_others]
            
            executor = self._get_executor()
            futures = {}
            
            for s in others:
                future = executor.submit(self._fetch_matches, s, name)
                futures[future] = s
            
            for future in concurrent.futures.as_completed(futures):
                if len(play_froms) >= LINE_BATCH:
                    break
                    
                s = futures[future]
                try:
                    j2 = future.result(timeout=AUX_TIMEOUT + 1)
                    if not j2 or not j2.get('list'):
                        continue
                        
                    for v2 in j2['list']:
                        n2 = _clean(v2.get('vod_name', ''))
                        if not _same_name(n2, name):
                            continue
                        f2, u2 = [], []
                        self._collect_lines(s['key'], v2, f2, u2)
                        if u2 and len(play_froms) < LINE_BATCH:
                            play_froms.extend(f2)
                            play_urls.extend(u2)
                        break
                except Exception:
                    continue

            play_froms, play_urls = self._deduplicate_playlists(play_froms, play_urls)
            
            return {'list': [self._build_detail_dict(vid, vod, play_froms, play_urls)]}
            
        except Exception:
            return {'list': []}

    def _deduplicate_playlists(self, play_froms, play_urls):
        unique_froms = []
        unique_urls = []
        seen_names = set()
        seen_groups = set()
        
        for pf, pu in zip(play_froms, play_urls):
            name_mark = _clean(pf).lower()
            url_mark = _clean(pu).lower()
            if not name_mark or not url_mark:
                continue
            if name_mark in seen_names or url_mark in seen_groups:
                continue
            seen_names.add(name_mark)
            seen_groups.add(url_mark)
            unique_froms.append(_clean(pf))
            unique_urls.append(pu)
            
        return unique_froms, unique_urls

    def _build_detail_dict(self, vid, vod, play_froms, play_urls):
        name = _clean(vod.get('vod_name', ''))
        pic = vod.get('vod_pic', '') or ''
        
        try:
            score = str(float(vod.get('vod_score', 0) or 0))
            if score.endswith('.0'):
                score = score[:-2]
        except Exception:
            score = ''
            
        d = {
            'vod_id': vid,
            'vod_name': name,
            'vod_pic': pic,
            'type_name': _clean(vod.get('type_name', '')),
            'vod_year': str(vod.get('vod_year', '') or ''),
            'vod_area': _clean(vod.get('vod_area', '')),
            'vod_actor': _clean(vod.get('vod_actor', '')),
            'vod_director': _clean(vod.get('vod_director', '')),
            'vod_content': _clean(vod.get('vod_content', '')),
            'vod_remarks': _clean(vod.get('vod_remarks', '')),
            'vod_play_from': '$$$'.join(play_froms),
            'vod_play_url': '$$$'.join(play_urls),
        }
        if score and score != '0':
            d['vod_score'] = score
        return d

    def _collect_lines(self, src_key, vod, play_froms, play_urls):
        src = self.by_key.get(src_key) or next((s for s in SOURCES if s.get('key') == src_key), {})
        src_name = _clean(src.get('name', src_key)) or src_key
        
        if src_name in play_froms:
            return
            
        from_raw = str(vod.get('vod_play_from', '') or '')
        from_raw = from_raw.replace('$$$', ',').replace('，', ',')
        froms = [x.strip() for x in from_raw.split(',') if x.strip()]
        urls = [x.strip() for x in str(vod.get('vod_play_url', '') or '').split('$$$') if x.strip()]
        
        episodes = []
        seen_episodes = set()
        
        for i, url_group in enumerate(urls):
            if not url_group:
                continue
            for episode in url_group.split('#'):
                parts = episode.split('$')
                if len(parts) < 2:
                    continue
                episode_name = _clean(parts[0]) or '第%d集' % (len(episodes) + 1)
                episode_url = parts[-1].strip()
                if not _is_direct(episode_url):
                    continue
                mark = episode_name.lower()
                if mark in seen_episodes:
                    continue
                seen_episodes.add(mark)
                episodes.append('%s$%s' % (episode_name, episode_url))
                
        if not episodes:
            return
            
        play_froms.append(src_name)
        play_urls.append('#'.join(episodes))

    def playerContent(self, flag, id, vipFlags):
        try:
            url = str(id or '').strip()
            if url.startswith('//'):
                url = 'https:' + url
            header = {'User-Agent': UA}
            if _is_direct(url):
                return {'parse': 0, 'playUrl': '', 'url': url, 'header': header}
            return {'parse': 1, 'playUrl': '', 'url': url, 'header': header}
        except Exception:
            return {'parse': 0, 'playUrl': '', 'url': id, 'header': {'User-Agent': UA}}

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        return False

    def destroy(self):
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except Exception:
                pass

    def localProxy(self, param):
        return None

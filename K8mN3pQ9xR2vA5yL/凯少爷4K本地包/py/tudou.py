import sys
sys.path.append('../..')
from base.spider import Spider as BaseSpider
import urllib.parse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

class Spider(BaseSpider):

    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
        ),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "sec-ch-ua-platform": "Windows",
        "sec-ch-ua": "Not)A;Brand;v=8, Chromium;v=138, Microsoft Edge;v=138",
        "sec-ch-ua-mobile": "?0",
        "api-token": "f76cf71d55122ed02d8d44e6a22b7150",
        "api-type": "WAP",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://ilitqxipof4.icu",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://ilitqxipof4.icu/",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6"
    }

    def init(self, extend=""):
        pass

    def getName(self):
        pass

    def isVideoFormat(self, url):
        pass

    def manualVideoCheck(self):
        pass

    def destroy(self):
        pass


    def homeContent(self, filter):
        result = {}
        classes = []
        filters = {}

        class_url = "https://apip.cydbkr.com/api/movie/index"
        list_url = "https://apip.cydbkr.com/api/movie/list"
        mdd_url = "https://apip.cydbkr.com/api/home/index"

  
        try:
            response = requests.post(class_url, headers=self.DEFAULT_HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('code') == 1 and data.get('data', {}).get('cates'):
                cates = data['data']['cates']
                classes = [
                    {'type_name': cate['name'], 'type_id': str(cate['id'])}
                    for cate in cates
                ]
            else:
                classes = [{'type_name': '穿越', 'type_id': '穿越'}]

        except Exception as e:
            print(f"请求失败或解析异常: {e}")
            classes = [{'type_name': '穿越', 'type_id': '穿越'}]

       

        result['class'] = classes

        # 筛选项获取函数
        def fetch_filters(type_id):
            if type_id == 'actor':
              
                return type_id, None

            if type_id == 'mdd':
                try:
                    res = requests.post(mdd_url, headers=self.DEFAULT_HEADERS, timeout=10)
                    res.raise_for_status()
                    data = res.json()
                    if data.get("code") == 1 and "cates" in data.get("data", {}):
                        cates = data["data"]["cates"]
                        values = [
                            {"n": cate.get("name", ""), "v": str(cate.get("id", ""))}
                            for cate in cates if cate.get("name") and cate.get("id") is not None
                        ]
                        return type_id, [{
                            "key": "filter_mdd",
                            "name": "麻豆筛选",
                            "value": values
                        }]
                except Exception as e:
                    print(f"获取麻豆专区筛选项失败: {e}")
                return type_id, None

          
            payload = {'page': "1", 'style': "0", 'cates': type_id}
            try:
                res = requests.post(list_url, data=payload, headers=self.DEFAULT_HEADERS, timeout=10)
                res.raise_for_status()
                data = res.json()

                if data.get("code") == 1 and "list" in data.get("data", {}):
                    group_list = data["data"]["list"]
                    values = [
                        {"n": item.get("name", ""), "v": item.get("id", "")}
                        for item in group_list
                    ]
                    return type_id, [{
                        "key": f"filter_{type_id}",
                        "name": "综合排序",
                        "value": values
                    }]
            except Exception as e:
                print(f"获取分类 {type_id} 的筛选项失败: {e}")
            return type_id, None

        with ThreadPoolExecutor(max_workers=20) as executor:
            future_to_type = {
                executor.submit(fetch_filters, cls['type_id']): cls['type_id']
                for cls in classes
            }
            for future in as_completed(future_to_type):
                tid = future_to_type[future]
                try:
                    _, fdata = future.result()
                    if fdata is not None:
                        filters[tid] = fdata
                except Exception as e:
                    print(f"处理分类 {tid} 异常: {e}")

        result['filters'] = filters
        return result

    def homeVideoContent(self):
        pass

    def categoryContent(self, tid, pg, filter, extend):
        filter_key = f'filter_{tid}'
        cate_id = extend.get(filter_key, '')  # 获取筛选值，例如 1002

        if tid == 'mdd':
         
            try:
                pg = int(pg)
                url = "https://apip.cydbkr.com/api/home/index"
                response = requests.post(url, headers=self.DEFAULT_HEADERS, timeout=10)
                response.raise_for_status()
                res_json = response.json()

                cates = res_json.get('data', {}).get('cates', [])
                matched_cate = next((c for c in cates if str(c.get('id')) == str(cate_id)), None)

                if not matched_cate:
                    print(f"未找到ID为 {cate_id} 的麻豆分类")
                    return {
                        'list': [],
                        'page': 1,
                        'pagecount': 1,
                        'limit': 90,
                        'total': 0
                    }                             

                sub_items = matched_cate.get('sub', [])
                videos = []
                for item in sub_items:
                    videos.append({
                        'vod_id': 'md_' + str(item.get('id', '')),  # 加前缀
                        'vod_name': item.get('name', ''),
                        'vod_pic': 'http://117.50.184.199:98/td.php?url=' + item.get('cover_url', ''),
                        'vod_tag': 'folder',
                        'vod_remarks': item.get('remark', '')
                    })

      
                limit = 90
                total = len(videos)
                start = (pg - 1) * limit
                end = start + limit
                paged_videos = videos[start:end]

                return {
                    'list': paged_videos,
                    'page': pg,
                    'pagecount': (total // limit) + (1 if total % limit else 0),
                    'limit': limit,
                    'total': total
                }

            except Exception as e:
                print(f"获取麻豆专区内容失败: {e}")
                return {
                    'list': [],
                    'page': 1,
                    'pagecount': 1,
                    'limit': 90,
                    'total': 0
                }
        elif tid == 'actor':
        
            try:
                pg = int(pg)
                url = "https://apip.cydbkr.com/api/home/getActorsList"
                payload = {
                    'page': str(pg),
                    'top': "0"
                }
                response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS, timeout=10)
                response.raise_for_status()
                res_json = response.json()

                data = res_json.get('data', {})
                items = data.get('list', [])
                page_info = data.get('page', {})

                videos = []
                for item in items:
                    videos.append({
                        'vod_id': 'yy_' + str(item.get('id', '')),
                        'vod_name': item.get('name', ''),
                        'vod_pic': 'http://117.50.184.199:98/td.php?url=' + item.get('cover_url', ''),
                        'vod_tag': 'folder',
                        'style': {
                        'type': 'oval',
                        'ratio': 1
                    },

                        'vod_remarks': item.get('remark', '')
                    })

                return {
                    'list': videos,
                    'page': int(page_info.get('current', pg)),
                    'pagecount': int(page_info.get('pages', 1)),
                    'limit': int(page_info.get('limit', 20)),
                    'total': int(page_info.get('total', len(videos)))
                }

            except Exception as e:
                print(f"获取传媒演员内容失败: {e}")
                return {
                    'list': [],
                    'page': 1,
                    'pagecount': 1,
                    'limit': 20,
                    'total': 0
                }

        elif tid.startswith("md_"):
          
            try:
                pg = int(pg)
                cate_id = tid.replace("md_", "")
                url = "https://apip.cydbkr.com/api/home/getCateList"
                payload = {
                    'page': str(pg),
                    'cates': str(cate_id),
                    'order': "id desc"
                }

                response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS, timeout=10)
                response.raise_for_status()
                res_json = response.json()

                data = res_json.get('data', {})
                items = data.get('list', [])
                page_info = data.get('page', {})

                videos = []
                for item in items:
                    videos.append({
                        'vod_id': str(item.get('id')),
                        'vod_name': item.get('title'),
                        'vod_pic': 'http://117.50.184.199:98/td.php?url=' + item.get('cover_url', ''),
                        "style": { "type":"rect", "ratio":1.33 },
                        'vod_remarks': item.get('actors_str', '')
                    })

                return {
                    'list': videos,
                    'page': int(page_info.get('current', pg)),
                    'pagecount': int(page_info.get('pages', 1)),
                    'limit': int(page_info.get('limit', 20)),
                    'total': int(page_info.get('total', len(videos)))
                }

            except Exception as e:
                print(f"获取麻豆子分类内容失败: {e}")
                return {
                    'list': [],
                    'page': 1,
                    'pagecount': 1,
                    'limit': 20,
                    'total': 0
                }


        elif tid.startswith("yy_"):

            try:

                pg = int(pg)

                aid = tid.replace("yy_", "")

                url = "https://apip.cydbkr.com/api/home/getActorsDetail"

                payload = {'page': str(pg), 'actors': aid}

                resp = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS, timeout=10)

                resp.raise_for_status()

                data = resp.json().get('data', {})

                items = data.get('list', [])

                page_info = data.get('page', {})

                videos = [{

                    'vod_id': str(item['id']),

                    'vod_name': item.get('title', ''),

                    'vod_pic': 'http://117.50.184.199:98/td.php?url=' + item.get('cover_url', ''),

                    "style": { "type":"rect", "ratio":1.33 },
                    
                    'vod_remarks': item.get('actors_str', '')

                } for item in items]

                return {

                    'list': videos,

                    'page': int(page_info.get('current', pg)),

                    'pagecount': int(page_info.get('pages', 1)),

                    'limit': int(page_info.get('limit', 20)),

                    'total': int(page_info.get('total', len(videos)))

                }


            except Exception as e:

                print(f"获取传媒演员详情失败: {e}")

                return {'list': [], 'page': 1, 'pagecount': 1, 'limit': 20, 'total': 0}

        else:
           
            url = "https://apip.cydbkr.com/api/movie/getCateMovieList"
            payload = {
                'page': str(pg),
                'id': str(cate_id),
                'order': "id desc"
            }

            try:
                response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS, timeout=10)
                res_json = response.json()

                videos = []
                for item in res_json.get('data', {}).get('list', []):
                    videos.append({
                        'vod_id': str(item.get('id')),
                        'vod_name': item.get('title'),
                        'vod_pic': 'http://117.50.184.199:98/td.php?url=' + item.get('cover_url', ''),
                        "style": { "type":"rect", "ratio":1.33 },
                        'vod_remarks': item.get('actors_str', '')
                    })

                page_info = res_json.get('data', {}).get('page', {})
                return {
                    'list': videos,
                    'page': int(page_info.get('current', pg)),
                    'pagecount': int(page_info.get('pages', 9999)),
                    'limit': int(page_info.get('limit', 90)),
                    'total': int(page_info.get('total', 999999))
                }

            except Exception as e:
                print(f"获取默认分类内容失败: {e}")
                return {
                    'list': [],
                    'page': 1,
                    'pagecount': 1,
                    'limit': 90,
                    'total': 0
                }

    def detailContent(self, ids):
        url = "https://apip.cydbkr.com/api/movie/detail"
        payload = {'id': ids}

        response = requests.post(url, data=payload, headers=self.DEFAULT_HEADERS)
        if response.status_code != 200:
            return {'list': []}

        data = response.json().get('data', {})
        vod = {
            'vod_name': data.get('title', ''),
            'vod_year': data.get('create_at', ''),
            'vod_remarks': data.get('remark', ''),
            'vod_content': ', '.join(data.get('marks', [])),
            'vod_play_from': '土豆视频',
            'vod_play_url': f"1${data.get('src_url', '')}"
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg="1"):
        url = (
            f"https://apip.cydbkr.com/api/movie/getSearchMovieList"
            f"?page={pg}&keyword={urllib.parse.quote(key)}"
        )

        response = requests.get(url, headers=self.DEFAULT_HEADERS)
        res_json = response.json()

        videos = []
        for item in res_json.get('data', {}).get('list', []):
            videos.append({
                'vod_id': str(item.get('id')),
                'vod_name': item.get('title'),
                'vod_pic': 'http://117.50.184.199:98/td.php?url=' + item.get('cover_url'),
                'vod_remarks': item.get('actors_str', '')
            })

        page_info = res_json.get('data', {}).get('page', {})
        return {
            'list': videos,
            'page': int(page_info.get('current', pg)),
            'pagecount': int(page_info.get('pages', 9999)),
            'limit': int(page_info.get('limit', 90)),
            'total': int(page_info.get('total', 999999))
        }

    def playerContent(self, flag, id, vipFlags):
        return {
            'parse': 0,
            'url': id
        }

    def localProxy(self, param):
        pass

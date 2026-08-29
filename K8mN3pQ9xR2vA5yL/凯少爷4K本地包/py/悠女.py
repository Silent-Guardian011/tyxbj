import requests
from bs4 import BeautifulSoup
import re
from base.spider import Spider
import sys
import json
import base64
import urllib.parse

sys.path.append('..')

xurl = "https://mmou0.younvpc01.top"
headerx = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36'
}

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

    def homeContent(self, filter):
        classes = [
            {"type_id": "7", "name": "幼女自拍"},
            {"type_id": "8", "name": "国产制作"},
            {"type_id": "9", "name": "主播网红"},
            {"type_id": "10", "name": "童颜巨乳"},
            {"type_id": "11", "name": "自拍偷拍"},
            {"type_id": "12", "name": "网曝系列"},
            {"type_id": "20", "name": "主播秀色"},
            {"type_id": "13", "name": "国产乱伦"},
            {"type_id": "14", "name": "国产丝袜"},
            {"type_id": "15", "name": "国产人妻"},
			{"type_id": "16", "name": "国产传媒 "},
			{"type_id": "21", "name": "国产自拍"},
			{"type_id": "22", "name": "欧美精品"},
			{"type_id": "24", "name": "欧美情色"}
        ]
        filters = {}
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):

        源码 = BeautifulSoup(requests.get(url=xurl, headers=headerx).text, "lxml")
        
        二次截取 = 源码.find_all('div', class_="video-box")
        
        videos = []
        for 数组 in 二次截取:
            数组 = 数组.find_all('li', class_="content-item")
        
            for 数组 in 数组:
                标题 = 数组.find('a')['title']

                链接 = 数组.find('a')['href']

                图片 = 数组.find('img')['data-original']
                if 'http' not in 图片:
                    图片 = xurl + 图片

                
                副标题 = 数组.find('span', class_="note text-bg-r")
                副标题 = 副标题.text.strip()
                
                video = {
                          "vod_id": 链接,
                          "vod_name": 标题,
                          "vod_pic": 图片,
                          "vod_remarks": 副标题
                                     }
                videos.append(video)
                
        result = {'list': videos}
        return result

    def categoryContent(self, cid, pg, filter, ext):
        result = {}
        videos = []
        if pg:
            page = int(pg)
        else:
            page = 1
        if page == '1':
            url = f'{xurl}/index.php/vod/type/id/{cid}/page/1.html'
        else:
            url = f'{xurl}/index.php/vod/type/id/{cid}/page/{str(page)}.html'
        源码 = BeautifulSoup(requests.get(url=url, headers=headerx).text, "lxml")

        
        二次截取 = 源码.find_all('div', class_="video-box")
        
        videos = []
        for 数组 in 二次截取:
            数组 = 数组.find_all('li', class_="content-item")
        
            for 数组 in 数组:
                标题 = 数组.find('a')['title']

                链接 = 数组.find('a')['href']

                图片 = 数组.find('img')['data-original']
                if 'http' not in 图片:
                    图片 = xurl + 图片

                副标题 = 数组.find('span', class_="note text-bg-r")
                副标题 = 副标题.text.strip()
                
                video = {
                          "vod_id": 链接,
                          "vod_name": 标题,
                          "vod_pic": 图片,
                          "vod_remarks": 副标题
                                     }
                videos.append(video)
                
        result = {'list': videos}
        result['page'] = pg
        result['pagecount'] = 99
        result['limit'] = 90
        result['total'] = 99
        return result

    def detailContent(self, ids):
        global pm    
        did = ids[0]
        result = {}
        videos = []
        playurl = ''
        if 'http' not in did:
            did = xurl + did
        源码 = BeautifulSoup(requests.get(url=did, headers=headerx).text, "lxml")
        
        vod = {}
        

        vod["vod_id"] = xurl
        
        vod["vod_name"] = 源码.select_one('h2').get_text()
        
        vod["type_name"] = 源码.select_one('.row p:-soup-contains(视频类型)').get_text().replace('视频类型：', '').strip()
        
        vod["vod_pic"] = 源码.select_one('.lazy').get('data-original', '') or 源码.select_one('').get('', '')
        
        vod["vod_remarks"] = 源码.select_one('.row p:-soup-contains(更新时间)').get_text().replace('更新时间：', '').strip()
              
            
        
        ktabs = []
        线路数组 = 源码.select('.nav.nav-tabs')
        for XL in 线路数组:
            线路标题 = XL.get_text()
            线路标题 = re.sub(r'\s*\d+$', '', 线路标题).strip()
            ktabs.append(线路标题)
        vod["vod_play_from"] = '$$$'.join(ktabs)
        
        klists = []
        播放数组 = 源码.select('.panel.clearfix')
        for BF in 播放数组:
            播放列表 = BF.select('a')
            klist = []
            for LB in 播放列表:
                播放标题 = LB.get('title', '')
                播放链接 = LB.get('href', '')
                剧集 = f'{播放标题}${播放链接}'
                klist.append(剧集)
            klists.append('#'.join(klist))
        
        vod["vod_play_url"] = '$$$'.join(klists)
        
        result = {'list': [vod]}
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}
        play_url = xurl + id
        try:

            resp = requests.get(url=play_url, headers=headerx)
            html = resp.text

            player_aaaa_match = re.search(r'var player_aaaa\s*=\s*({[^}]+})', html)
            if player_aaaa_match:
                try:
                    json_str = player_aaaa_match.group(1)
                    json_str = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', json_str)
                    json_str = json_str.replace("'", '"')
                    player_data = json.loads(json_str)

                    if player_data.get('url'):
                        url = player_data['url']
                        encrypt = player_data.get('encrypt', 0)

                        clean_url = ""
                        if encrypt == 3:
                            try:
                                decoded = base64.b64decode(url).decode('utf-8')
                                if decoded.startswith('nanke_'):
                                    decoded = decoded[6:]
                                if '=' in decoded:
                                    try:
                                        decoded = base64.b64decode(decoded).decode('utf-8')
                                    except:
                                        pass  
                                clean_url = urllib.parse.unquote(decoded)

                                if not clean_url.startswith('http'):
                                    if clean_url.startswith('//'):
                                        clean_url = 'https:' + clean_url
                                    elif clean_url.startswith('/'):
                                        clean_url = xurl.rstrip('/') + clean_url
                                    else:
                                        clean_url = xurl.rstrip('/') + '/' + clean_url
                            except Exception as e:
                                clean_url = url.replace('\\/', '/').replace('\\', '')
                        else:
                            clean_url = url.replace('\\/', '/').replace('\\', '')

                        result["parse"] = 0  
                        result["playUrl"] = ''
                        result["url"] = clean_url
                        result["header"] = headerx
                        return result
                except Exception as e:
                    print(f"解析 player_aaaa 失败: {e}")

            player_data_match = re.search(r'var player_data\s*=\*s*({[^}]+})', html)
            if player_data_match:
                try:
                    json_str = player_data_match.group(1)
                    json_str = re.sub(r'([{,]\s*)(\w+)\s*:', r'\1"\2":', json_str)
                    json_str = json_str.replace("'", '"')
                    player_data = json.loads(json_str)
                    if player_data.get('url'):
                        url = player_data['url']
                        try:
                            decoded = base64.b64decode(url).decode('utf-8')
                            clean_url = urllib.parse.unquote(decoded)
                            result["parse"] = 0
                            result["playUrl"] = ''
                            result["url"] = clean_url
                            result["header"] = headerx
                            return result
                        except:
                            clean_url = url.replace('\\', '')
                            result["parse"] = 0
                            result["playUrl"] = ''
                            result["url"] = clean_url
                            result["header"] = headerx
                            return result
                except Exception as e:
                    print(f"解析 player_data 失败: {e}")

            m3u8_patterns = [
                r'"url"\s*:\s*"([^"]+\.m3u8)"',
                r"'url'\s*:\s*'([^']+\.m3u8)'",
                r'url\s*=\s*[\'"]([^\'"]+\.m3u8)[\'"]',
                r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)'
            ]
            for pattern in m3u8_patterns:
                match = re.search(pattern, html)
                if match and match.group(1):
                    clean_url = match.group(1).replace('\\', '')
                    result["parse"] = 0
                    result["playUrl"] = ''
                    result["url"] = clean_url
                    result["header"] = headerx
                    return result

            video_patterns = [
                r'(https?://[^\s\'"]+\.(m3u8|mp4|flv|avi|mkv|mov|wmv|webm)[^\s\'"]*)',
                r'src\s*=\s*[\'"]([^\'"]+\.(m3u8|mp4|flv|avi|mkv|mov|wmv|webm)[^\'"]*)[\'"]',
                r'source\s+src\s*=\s*[\'"]([^\'"]+)[\'"]'
            ]
            for pattern in video_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match and match.group(1):
                    result["parse"] = 0
                    result["playUrl"] = ''
                    result["url"] = match.group(1)
                    result["header"] = headerx
                    return result

            iframe_match = re.search(r'<iframe[^>]+src\s*=\s*[\'"]([^\'"]+)[\'"][^>]*>', html, re.IGNORECASE)
            if iframe_match and iframe_match.group(1):
                result["parse"] = 1  
                result["playUrl"] = ''
                result["url"] = iframe_match.group(1)
                result["header"] = headerx
                return result

        except Exception as e:
            print(f"请求播放页或解密过程发生异常: {e}")

        result["parse"] = 1
        result["playUrl"] = ''
        result["url"] = play_url
        result["header"] = headerx
        return result

    def searchContentPage(self, key, quick, page):
        result = {}
        videos = []
        if not page:
            page = '1'
        if page == '1':
            url = f'{xurl}/index.php/vod/search.html?wd={key}'
        else:
            url = f'{xurl}/index.php/vod/search/page/{page}/wd/{key}.html'        
        源码 = BeautifulSoup(requests.get(url=url, headers=headerx).text, "lxml")

        二次截取 = 源码.find_all('div', class_="video-box")
        
        videos = []
        for 数组 in 二次截取:
            数组 = 数组.find_all('li', class_="content-item")

            for 数组 in 数组:
                标题 = 数组.find('a')['title']

                链接 = 数组.find('a')['href']

                图片 = 数组.find('img')['data-original']
                if 'http' not in 图片:
                    图片 = xurl + 图片  

                副标题 = 数组.find('span', class_="note text-bg-r")
                副标题 = 副标题.text.strip()
                
                video = {
                          "vod_id": 链接,
                          "vod_name": 标题,
                          "vod_pic": 图片,
                          "vod_remarks": 副标题
                                     }
                videos.append(video)
                
        result = {'list': videos}
        result['page'] = page
        result['pagecount'] = 60
        result['limit'] = 30
        result['total'] = 999999
        return result
        
    def searchContent(self, key, quick, page='1'):
        return self.searchContentPage(key, quick, page)

    def localProxy(self, params):
        if params['type'] == "m3u8":
            return self.proxyM3u8(params)
        elif params['type'] == "media":
            return self.proxyMedia(params)
        elif params['type'] == "ts":
            return self.proxyTs(params)
        return None
        
        
if __name__ == "__main__":
    spider = Spider()
    spider.init("")

    player_result = spider.playerContent("m3u8", "/play/4375-1-0.html", {})
    print(player_result)

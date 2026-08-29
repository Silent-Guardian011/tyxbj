import re
import requests
from urllib.parse import urljoin, quote

from base.spider import Spider

class Spider(Spider):
    """A123TV 爬虫 (https://a123tv.com) - 简化版"""

    def homeContent(self, filter):
        """获取首页数据"""
        # 直接在这里定义所有需要的属性
        host = "https://a123tv.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": host
        }
        
        result = {}
        
        # 获取首页HTML
        html = self.fetch_html(host, headers)
        if not html:
            return result

        # 解析分类
        classes = []
        # 从导航栏提取主分类
        class_pattern = r'<a[^>]+href="(/t/\d+\.html)"[^>]*>([^<]+)</a>'
        class_matches = re.findall(class_pattern, html)
        seen = set()
        for link, name in class_matches:
            if name not in seen and name not in ["首页", "福利"]:
                seen.add(name)
                type_id = re.search(r'/t/(\d+)\.html', link).group(1)
                classes.append({
                    "type_id": type_id,
                    "type_name": name
                })
        
        # 如果没提取到，使用默认分类
        if not classes:
            default_classes = [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "连续剧"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
            ]
            classes = default_classes
        
        result["class"] = classes

        # 解析首页视频列表
        videos = []
        # 匹配视频项 - 简化版
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items[:30]:
            videos.append({
                "vod_id": urljoin(host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(host, img) if img.startswith('http') else urljoin(host, img),
                "vod_remarks": ""
            })
        
        result["list"] = videos
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """获取分类列表数据"""
        host = "https://a123tv.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": host
        }
        
        result = {}
        
        # 构造分类页URL
        url = f"{host}/t/{tid}.html?page={pg}"
        html = self.fetch_html(url, headers)
        if not html:
            return result

        # 提取视频列表
        videos = []
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items:
            videos.append({
                "vod_id": urljoin(host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(host, img) if img.startswith('http') else urljoin(host, img),
                "vod_remarks": ""
            })

        # 提取分页信息
        page_total = 1
        # 尝试找最后一页
        last_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>尾页</a>'
        last_match = re.search(last_pattern, html)
        if last_match:
            page_total = int(last_match.group(1))
        else:
            # 找所有页码
            page_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>(\d+)</a>'
            page_matches = re.findall(page_pattern, html)
            if page_matches:
                page_total = max([int(p[1]) for p in page_matches] + [1])

        result["list"] = videos
        result["page"] = pg
        result["pagecount"] = page_total
        result["limit"] = 20
        result["total"] = len(videos)
        return result

    def detailContent(self, ids):
        """获取详情页数据"""
        host = "https://a123tv.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": host
        }
        
        result = []
        vod_url = ids[0] if isinstance(ids, list) else ids
        
        html = self.fetch_html(vod_url, headers)
        if not html:
            return result

        vod = {}
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if not title_match:
            title_match = re.search(r'<title>([^<]+) - [^<]+</title>', html)
        vod["vod_name"] = title_match.group(1).strip() if title_match else "未知标题"

        # 提取封面图
        pic_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        vod["vod_pic"] = pic_match.group(1) if pic_match else ""

        # 提取描述
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        vod["vod_content"] = desc_match.group(1) if desc_match else ""

        # 提取播放列表
        play_from = ["线路1"]
        
        # 提取所有播放链接（dl/格式）
        url_pattern = r'<a[^>]*href="(/dl/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
        url_matches = re.findall(url_pattern, html)
        
        if url_matches:
            play_url_list = []
            for href, name in url_matches:
                full_url = urljoin(host, href)
                play_url_list.append(f"{name}${full_url}")
            
            play_url = ["#".join(play_url_list)] if play_url_list else []
        else:
            # 备选：v/格式的链接
            url_pattern2 = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
            url_matches2 = re.findall(url_pattern2, html)
            if url_matches2:
                play_url_list = []
                for href, name in url_matches2:
                    full_url = urljoin(host, href)
                    play_url_list.append(f"{name}${full_url}")
                
                play_url = ["#".join(play_url_list)] if play_url_list else []
            else:
                play_url = []

        vod["vod_play_from"] = "$$$".join(play_from) if play_from else "线路1"
        vod["vod_play_url"] = "$$$".join(play_url) if play_url else "第1集$" + vod_url
        
        result.append(vod)
        return result

    def searchContent(self, key, quick, pg=1):
        """搜索内容"""
        host = "https://a123tv.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": host
        }
        
        result = []
        
        # 构造搜索URL
        search_url = f"{host}/search?wd={quote(key)}&page={pg}"
        html = self.fetch_html(search_url, headers)
        if not html:
            return result

        # 提取搜索结果
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items:
            result.append({
                "vod_id": urljoin(host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(host, img) if img.startswith('http') else urljoin(host, img),
                "vod_remarks": ""
            })

        return result

    def playerContent(self, flag, id, vipFlags):
        """获取播放地址"""
        host = "https://a123tv.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": host
        }
        
        # 获取播放页面HTML
        html = self.fetch_html(urljoin(host, id), headers)
        if not html:
            return ""

        # 尝试提取真正的播放地址
        # 1. 找iframe
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"[^>]*>', html)
        if iframe_match:
            return iframe_match.group(1)
        
        # 2. 找video标签的src
        video_match = re.search(r'<video[^>]*>.*?<source[^>]*src="([^"]+)"[^>]*>', html, re.DOTALL)
        if video_match:
            return video_match.group(1)
        
        # 3. 找可能的播放器配置
        url_match = re.search(r'url["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        if url_match:
            return url_match.group(1)
        
        # 4. 返回原链接
        return urljoin(host, id)

    def fetch_html(self, url, headers):
        """获取HTML内容的辅助方法"""
        try:
            import requests
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'utf-8'
            return r.text
        except:
            try:
                from urllib.request import urlopen, Request
                req = Request(url, headers=headers)
                with urlopen(req, timeout=10) as response:
                    return response.read().decode('utf-8', errors='ignore')
            except:
                return ""

    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.mov', '.wmv', '.rmvb']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in video_exts)

    def manualVideoCheck(self):
        """手动检查视频"""
        return True

    def init(self, extend=""):
        """TVBox框架要求的初始化方法 - 留空即可"""
        pass
import requests
from urllib.parse import urljoin, quote

from base.spider import Spider

class Spider(Spider):
    """A123TV 爬虫 (https://a123tv.com)"""

    def _ensure_init(self):
        """确保对象已初始化"""
        if not hasattr(self, 'host'):
            self.host = "https://a123tv.com"
        if not hasattr(self, 'headers'):
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": self.host
            }

    def init(self, extend=""):
        """TVBox框架要求的初始化方法"""
        self.host = "https://a123tv.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": self.host
        }
        return

    def homeContent(self, filter):
        """获取首页数据"""
        self._ensure_init()
        result = {}
        
        # 获取首页HTML
        html = self.fetch_html(self.host)
        if not html:
            return result

        # 解析分类
        classes = []
        # 从导航栏提取主分类
        class_pattern = r'<a[^>]+href="(/t/\d+\.html)"[^>]*>([^<]+)</a>'
        class_matches = re.findall(class_pattern, html)
        seen = set()
        for link, name in class_matches:
            if name not in seen and name not in ["首页", "福利"]:
                seen.add(name)
                type_id = re.search(r'/t/(\d+)\.html', link).group(1)
                classes.append({
                    "type_id": type_id,
                    "type_name": name
                })
        
        # 如果没提取到，使用默认分类
        if not classes:
            default_classes = [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "连续剧"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
            ]
            classes = default_classes
        
        result["class"] = classes

        # 解析首页视频列表
        videos = []
        # 匹配视频项 - 简化版
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items[:30]:
            videos.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": ""
            })
        
        result["list"] = videos
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """获取分类列表数据"""
        self._ensure_init()
        result = {}
        
        # 构造分类页URL
        url = f"{self.host}/t/{tid}.html?page={pg}"
        html = self.fetch_html(url)
        if not html:
            return result

        # 提取视频列表
        videos = []
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items:
            videos.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": ""
            })

        # 提取分页信息
        page_total = 1
        # 尝试找最后一页
        last_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>尾页</a>'
        last_match = re.search(last_pattern, html)
        if last_match:
            page_total = int(last_match.group(1))
        else:
            # 找所有页码
            page_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>(\d+)</a>'
            page_matches = re.findall(page_pattern, html)
            if page_matches:
                page_total = max([int(p[1]) for p in page_matches] + [1])

        result["list"] = videos
        result["page"] = pg
        result["pagecount"] = page_total
        result["limit"] = 20
        result["total"] = len(videos)
        return result

    def detailContent(self, ids):
        """获取详情页数据"""
        self._ensure_init()
        result = []
        vod_url = ids[0] if isinstance(ids, list) else ids
        
        html = self.fetch_html(vod_url)
        if not html:
            return result

        vod = {}
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if not title_match:
            title_match = re.search(r'<title>([^<]+) - [^<]+</title>', html)
        vod["vod_name"] = title_match.group(1).strip() if title_match else "未知标题"

        # 提取封面图
        pic_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        vod["vod_pic"] = pic_match.group(1) if pic_match else ""

        # 提取描述
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        vod["vod_content"] = desc_match.group(1) if desc_match else ""

        # 提取播放列表
        play_from = ["线路1"]
        
        # 提取所有播放链接（dl/格式）
        url_pattern = r'<a[^>]*href="(/dl/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
        url_matches = re.findall(url_pattern, html)
        
        if url_matches:
            play_url_list = []
            for href, name in url_matches:
                full_url = urljoin(self.host, href)
                play_url_list.append(f"{name}${full_url}")
            
            play_url = ["#".join(play_url_list)] if play_url_list else []
        else:
            # 备选：v/格式的链接
            url_pattern2 = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
            url_matches2 = re.findall(url_pattern2, html)
            if url_matches2:
                play_url_list = []
                for href, name in url_matches2:
                    full_url = urljoin(self.host, href)
                    play_url_list.append(f"{name}${full_url}")
                
                play_url = ["#".join(play_url_list)] if play_url_list else []
            else:
                play_url = []

        vod["vod_play_from"] = "$$$".join(play_from) if play_from else "线路1"
        vod["vod_play_url"] = "$$$".join(play_url) if play_url else "第1集$" + vod_url
        
        result.append(vod)
        return result

    def searchContent(self, key, quick, pg=1):
        """搜索内容"""
        self._ensure_init()
        result = []
        
        # 构造搜索URL
        search_url = f"{self.host}/search?wd={quote(key)}&page={pg}"
        html = self.fetch_html(search_url)
        if not html:
            return result

        # 提取搜索结果
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items:
            result.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": ""
            })

        return result

    def playerContent(self, flag, id, vipFlags):
        """获取播放地址"""
        self._ensure_init()
        
        # 获取播放页面HTML
        html = self.fetch_html(urljoin(self.host, id))
        if not html:
            return ""

        # 尝试提取真正的播放地址
        # 1. 找iframe
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"[^>]*>', html)
        if iframe_match:
            return iframe_match.group(1)
        
        # 2. 找video标签的src
        video_match = re.search(r'<video[^>]*>.*?<source[^>]*src="([^"]+)"[^>]*>', html, re.DOTALL)
        if video_match:
            return video_match.group(1)
        
        # 3. 找可能的播放器配置
        url_match = re.search(r'url["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        if url_match:
            return url_match.group(1)
        
        # 4. 返回原链接
        return urljoin(self.host, id)

    def fetch_html(self, url):
        """获取HTML内容的辅助方法"""
        try:
            import requests
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            return r.text
        except:
            try:
                from urllib.request import urlopen, Request
                req = Request(url, headers=self.headers)
                with urlopen(req, timeout=10) as response:
                    return response.read().decode('utf-8', errors='ignore')
            except:
                return ""

    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.mov', '.wmv', '.rmvb']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in video_exts)

    def manualVideoCheck(self):
        """手动检查视频"""
        return True
import requests
from urllib.parse import urljoin, quote

from base.spider import Spider

class Spider(Spider):
    """A123TV 爬虫 (https://a123tv.com)"""

    def __init__(self):
        """初始化方法 - 在对象创建时自动调用"""
        self.host = "https://a123tv.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": self.host
        }
        print(f"Spider initialized with host: {self.host}")

    def init(self, extend=""):
        """TVBox框架要求的初始化方法"""
        # 确保host和headers存在
        if not hasattr(self, 'host'):
            self.host = "https://a123tv.com"
        if not hasattr(self, 'headers'):
            self.headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Referer": self.host
            }
        return

    def homeContent(self, filter):
        """获取首页数据"""
        result = {}
        # 获取首页HTML
        html = self.fetch_html(self.host)
        if not html:
            return result

        # 解析分类
        classes = []
        # 从导航栏提取主分类
        class_pattern = r'<a[^>]+href="(/t/\d+\.html)"[^>]*>([^<]+)</a>'
        class_matches = re.findall(class_pattern, html)
        seen = set()
        for link, name in class_matches:
            if name not in seen and name not in ["首页", "福利"]:  # 过滤掉首页和福利分类
                seen.add(name)
                type_id = re.search(r'/t/(\d+)\.html', link).group(1)
                classes.append({
                    "type_id": type_id,
                    "type_name": name
                })
        
        # 如果上面没提取到，使用备选方案
        if not classes:
            # 手动定义常用分类
            default_classes = [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "连续剧"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
            ]
            classes = default_classes
        
        result["class"] = classes

        # 解析首页视频列表（每个分类区域取前几个）
        videos = []
        # 匹配视频项
        simple_pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(simple_pattern, html, re.DOTALL)
        
        for href, img, title in items[:30]:
            videos.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": ""
            })
        
        result["list"] = videos
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """获取分类列表数据"""
        result = {}
        # 构造分类页URL
        url = f"{self.host}/t/{tid}.html?page={pg}"
        html = self.fetch_html(url)
        if not html:
            return result

        # 提取视频列表
        videos = []
        # 匹配视频项
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items:
            videos.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": ""
            })

        # 提取分页信息
        page_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*class="[^"]*active[^"]*"[^>]*>'
        page_matches = re.findall(page_pattern, html)
        page_total = 1
        if page_matches:
            page_total = max([int(p) for p in page_matches] + [1])
        else:
            # 尝试找最后一页
            last_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>尾页</a>'
            last_match = re.search(last_pattern, html)
            if last_match:
                page_total = int(last_match.group(1))

        result["list"] = videos
        result["page"] = pg
        result["pagecount"] = page_total
        result["limit"] = 20
        result["total"] = len(videos)
        return result

    def detailContent(self, ids):
        """获取详情页数据"""
        result = []
        vod_url = ids[0] if isinstance(ids, list) else ids
        
        html = self.fetch_html(vod_url)
        if not html:
            return result

        vod = {}
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if not title_match:
            title_match = re.search(r'<title>([^<]+) - [^<]+</title>', html)
        vod["vod_name"] = title_match.group(1).strip() if title_match else "未知标题"

        # 提取封面图
        pic_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        vod["vod_pic"] = pic_match.group(1) if pic_match else ""

        # 提取描述
        desc_match = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]+)"', html)
        vod["vod_content"] = desc_match.group(1) if desc_match else ""

        # 提取播放列表 - 简化版
        play_from = ["线路1"]
        
        # 提取所有播放链接
        url_pattern = r'<a[^>]*href="(/dl/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
        url_matches = re.findall(url_pattern, html)
        
        if url_matches:
            play_url_list = []
            for href, name in url_matches:
                full_url = urljoin(self.host, href)
                play_url_list.append(f"{name}${full_url}")
            
            if play_url_list:
                play_url = ["#".join(play_url_list)]
        else:
            # 备选：提取v/格式的链接
            url_pattern2 = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
            url_matches2 = re.findall(url_pattern2, html)
            if url_matches2:
                play_url_list = []
                for href, name in url_matches2:
                    full_url = urljoin(self.host, href)
                    play_url_list.append(f"{name}${full_url}")
                
                play_url = ["#".join(play_url_list)] if play_url_list else []
            else:
                play_url = []

        vod["vod_play_from"] = "$$$".join(play_from) if play_from else "线路1"
        vod["vod_play_url"] = "$$$".join(play_url) if play_url else "第1集$" + vod_url
        
        result.append(vod)
        return result

    def searchContent(self, key, quick, pg=1):
        """搜索内容"""
        result = []
        # 构造搜索URL
        search_url = f"{self.host}/search?wd={quote(key)}&page={pg}"
        html = self.fetch_html(search_url)
        if not html:
            return result

        # 提取搜索结果（通常和列表页结构类似）
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title in items:
            result.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": ""
            })

        return result

    def playerContent(self, flag, id, vipFlags):
        """获取播放地址（处理dl/格式的链接）"""
        # id 可能是 /dl/xxx.html 或 /v/xxx.html
        html = self.fetch_html(urljoin(self.host, id))
        if not html:
            return ""

        # 尝试提取真正的播放地址（通常是iframe或video标签）
        # 先找iframe
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"[^>]*>', html)
        if iframe_match:
            return iframe_match.group(1)
        
        # 找video标签的src
        video_match = re.search(r'<video[^>]*>.*?<source[^>]*src="([^"]+)"[^>]*>', html, re.DOTALL)
        if video_match:
            return video_match.group(1)
        
        # 找可能的播放器配置
        url_match = re.search(r'url["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        if url_match:
            return url_match.group(1)
        
        # 如果都没找到，返回原链接（可能会被APP的解析器处理）
        return urljoin(self.host, id)

    def fetch_html(self, url):
        """获取HTML内容的辅助方法"""
        try:
            import requests
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            return r.text
        except:
            # 如果requests不可用，尝试使用urllib
            try:
                from urllib.request import urlopen, Request
                req = Request(url, headers=self.headers)
                with urlopen(req, timeout=10) as response:
                    return response.read().decode('utf-8', errors='ignore')
            except:
                return ""

    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.mov', '.wmv', '.rmvb']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in video_exts)

    def manualVideoCheck(self):
        """手动检查视频（TVBox框架需要）"""
        return True
import requests
from urllib.parse import urljoin, quote

from base.spider import Spider

class Spider(Spider):
    """A123TV 爬虫 (https://a123tv.com)"""

    def init(self, extend=""):
        """初始化方法"""
        self.host = "https://a123tv.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": self.host
        }
        print(f"Spider initialized with host: {self.host}")

    def homeContent(self, filter):
        """获取首页数据"""
        result = {}
        # 获取首页HTML
        html = self.fetch_html(self.host)
        if not html:
            return result

        # 解析分类
        classes = []
        # 从导航栏提取主分类
        class_pattern = r'<a[^>]+href="(/t/\d+\.html)"[^>]*>([^<]+)</a>'
        class_matches = re.findall(class_pattern, html)
        seen = set()
        for link, name in class_matches:
            if name not in seen and name not in ["首页", "福利"]:  # 过滤掉首页和福利分类
                seen.add(name)
                type_id = re.search(r'/t/(\d+)\.html', link).group(1)
                classes.append({
                    "type_id": type_id,
                    "type_name": name
                })
        
        # 如果上面没提取到，使用备选方案
        if not classes:
            # 手动定义常用分类
            default_classes = [
                {"type_id": "1", "type_name": "电影"},
                {"type_id": "2", "type_name": "连续剧"},
                {"type_id": "3", "type_name": "综艺"},
                {"type_id": "4", "type_name": "动漫"},
            ]
            classes = default_classes
        
        result["class"] = classes

        # 解析首页视频列表（每个分类区域取前几个）
        videos = []
        # 匹配分类区块
        block_pattern = r'<div[^>]*class="[^"]*w4-list[^"]*"[^>]*>.*?<div[^>]*class="[^"]*w4-item-wrap[^"]*"[^>]*>.*?</div>.*?</div>'
        blocks = re.findall(block_pattern, html, re.DOTALL)
        
        for block in blocks[:8]:  # 只取前8个区块
            # 提取区块标题
            title_match = re.search(r'<h2[^>]*>([^<]+)</h2>', block)
            block_title = title_match.group(1) if title_match else "推荐"
            
            # 提取视频项
            item_pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>.*?<div[^>]*class="[^"]*w4-item-desc[^"]*"[^>]*>([^<]+)</div>'
            items = re.findall(item_pattern, block, re.DOTALL)
            
            for href, img, title, desc in items:
                videos.append({
                    "vod_id": urljoin(self.host, href),
                    "vod_name": title.strip(),
                    "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                    "vod_remarks": desc.strip()
                })
        
        # 如果上面没提取到，用简单方法提取
        if not videos:
            simple_pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>'
            items = re.findall(simple_pattern, html, re.DOTALL)
            for href, img, title in items[:20]:
                videos.append({
                    "vod_id": urljoin(self.host, href),
                    "vod_name": title.strip(),
                    "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                    "vod_remarks": ""
                })
        
        result["list"] = videos
        return result

    def categoryContent(self, tid, pg, filter, extend):
        """获取分类列表数据"""
        result = {}
        # 构造分类页URL
        url = f"{self.host}/t/{tid}.html?page={pg}"
        html = self.fetch_html(url)
        if not html:
            return result

        # 提取视频列表
        videos = []
        # 匹配视频项
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>.*?<div[^>]*class="[^"]*w4-item-desc[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title, desc in items:
            videos.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": desc.strip()
            })

        # 提取分页信息
        page_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*class="[^"]*active[^"]*"[^>]*>'
        page_matches = re.findall(page_pattern, html)
        page_total = 1
        if page_matches:
            page_total = max([int(p) for p in page_matches] + [1])
        else:
            # 尝试找最后一页
            last_pattern = r'<a[^>]*href="[^"]*page=(\d+)"[^>]*>尾页</a>'
            last_match = re.search(last_pattern, html)
            if last_match:
                page_total = int(last_match.group(1))

        result["list"] = videos
        result["page"] = pg
        result["pagecount"] = page_total
        result["limit"] = 20
        result["total"] = len(videos)
        return result

    def detailContent(self, ids):
        """获取详情页数据"""
        result = []
        vod_url = ids[0] if isinstance(ids, list) else ids
        
        html = self.fetch_html(vod_url)
        if not html:
            return result

        vod = {}
        
        # 提取标题
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if not title_match:
            title_match = re.search(r'<title>([^<]+) - [^<]+</title>', html)
        vod["vod_name"] = title_match.group(1).strip() if title_match else "未知标题"

        # 提取封面图
        pic_match = re.search(r'<img[^>]*src="([^"]+)"[^>]*class="[^"]*w4-video-pic[^"]*"[^>]*>', html)
        if not pic_match:
            pic_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]+)"', html)
        vod["vod_pic"] = pic_match.group(1) if pic_match else ""

        # 提取类型/年份等信息
        info_pattern = r'<div[^>]*class="[^"]*w4-video-info[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>.*?<span[^>]*>([^<]+)</span>'
        info_match = re.search(info_pattern, html, re.DOTALL)
        if info_match:
            vod["vod_content"] = f"{info_match.group(1)} / {info_match.group(2)}"

        # 提取播放列表
        play_from = []
        play_url = []
        
        # 匹配所有线路组
        # 这个网站可能使用多个播放源，每个源下有多个集数
        # 先找所有线路组标题
        from_pattern = r'<div[^>]*class="[^"]*w4-episode-head[^"]*"[^>]*>.*?<span[^>]*>([^<]+)</span>'
        from_matches = re.findall(from_pattern, html, re.DOTALL)
        
        if from_matches:
            # 有多个播放源
            # 按线路组提取
            play_from = [f"线路{i+1}" for i in range(len(from_matches))]
            
            # 提取所有播放链接
            url_pattern = r'<a[^>]*href="(/dl/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
            url_matches = re.findall(url_pattern, html)
            
            if url_matches:
                # 将所有链接合并到一个源中（或者可以按源分组，但这里简化处理）
                play_url_list = []
                for href, name in url_matches:
                    full_url = urljoin(self.host, href)
                    play_url_list.append(f"{name}${full_url}")
                
                if play_url_list:
                    play_url = ["#".join(play_url_list)]
            else:
                # 备选：提取v/格式的链接
                url_pattern2 = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
                url_matches2 = re.findall(url_pattern2, html)
                if url_matches2:
                    play_url_list = []
                    for href, name in url_matches2:
                        full_url = urljoin(self.host, href)
                        play_url_list.append(f"{name}${full_url}")
                    
                    if play_url_list:
                        play_url = ["#".join(play_url_list)]
        else:
            # 只有一个播放源
            play_from = ["线路1"]
            
            # 提取所有播放链接
            url_pattern = r'<a[^>]*href="(/dl/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
            url_matches = re.findall(url_pattern, html)
            
            if url_matches:
                play_url_list = []
                for href, name in url_matches:
                    full_url = urljoin(self.host, href)
                    play_url_list.append(f"{name}${full_url}")
                
                if play_url_list:
                    play_url = ["#".join(play_url_list)]
            else:
                # 备选：提取v/格式的链接
                url_pattern2 = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-episode-item[^"]*"[^>]*>([^<]+)</a>'
                url_matches2 = re.findall(url_pattern2, html)
                if url_matches2:
                    play_url_list = []
                    for href, name in url_matches2:
                        full_url = urljoin(self.host, href)
                        play_url_list.append(f"{name}${full_url}")
                    
                    if play_url_list:
                        play_url = ["#".join(play_url_list)]

        # 如果没提取到任何播放链接，使用简单方法
        if not play_url:
            # 尝试从线路切换区域提取
            line_pattern = r'<div[^>]*class="[^"]*w4-line[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*class="[^"]*w4-line-item[^"]*"[^>]*>([^<]+)</a>'
            line_matches = re.findall(line_pattern, html, re.DOTALL)
            if line_matches:
                play_from = ["线路1"]
                play_url_list = []
                for href, name in line_matches:
                    full_url = urljoin(self.host, href)
                    play_url_list.append(f"{name}${full_url}")
                
                if play_url_list:
                    play_url = ["#".join(play_url_list)]

        vod["vod_play_from"] = "$$$".join(play_from) if play_from else "线路1"
        vod["vod_play_url"] = "$$$".join(play_url) if play_url else "第1集$" + vod_url
        
        result.append(vod)
        return result

    def searchContent(self, key, quick, pg=1):
        """搜索内容"""
        result = []
        # 构造搜索URL
        search_url = f"{self.host}/search?wd={quote(key)}&page={pg}"
        html = self.fetch_html(search_url)
        if not html:
            return result

        # 提取搜索结果（通常和列表页结构类似）
        pattern = r'<a[^>]*href="(/v/[^"]+\.html)"[^>]*class="[^"]*w4-item[^"]*"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*>.*?<div[^>]*class="[^"]*w4-item-title[^"]*"[^>]*>([^<]+)</div>.*?<div[^>]*class="[^"]*w4-item-desc[^"]*"[^>]*>([^<]+)</div>'
        items = re.findall(pattern, html, re.DOTALL)
        
        for href, img, title, desc in items:
            result.append({
                "vod_id": urljoin(self.host, href),
                "vod_name": title.strip(),
                "vod_pic": urljoin(self.host, img) if img.startswith('http') else urljoin(self.host, img),
                "vod_remarks": desc.strip()
            })

        return result

    def playerContent(self, flag, id, vipFlags):
        """获取播放地址（处理dl/格式的链接）"""
        # id 可能是 /dl/xxx.html 或 /v/xxx.html
        html = self.fetch_html(urljoin(self.host, id))
        if not html:
            return ""

        # 尝试提取真正的播放地址（通常是iframe或video标签）
        # 先找iframe
        iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"[^>]*>', html)
        if iframe_match:
            return iframe_match.group(1)
        
        # 找video标签的src
        video_match = re.search(r'<video[^>]*>.*?<source[^>]*src="([^"]+)"[^>]*>', html, re.DOTALL)
        if video_match:
            return video_match.group(1)
        
        # 找可能的播放器配置
        url_match = re.search(r'url["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
        if url_match:
            return url_match.group(1)
        
        # 如果都没找到，返回原链接（可能会被APP的解析器处理）
        return urljoin(self.host, id)

    def fetch_html(self, url):
        """获取HTML内容的辅助方法"""
        try:
            import requests
            r = requests.get(url, headers=self.headers, timeout=10)
            r.encoding = 'utf-8'
            return r.text
        except:
            # 如果requests不可用，尝试使用urllib
            try:
                from urllib.request import urlopen, Request
                req = Request(url, headers=self.headers)
                with urlopen(req, timeout=10) as response:
                    return response.read().decode('utf-8', errors='ignore')
            except:
                return ""

    def isVideoFormat(self, url):
        """判断是否为视频格式"""
        # 检查URL是否以常见视频扩展名结尾
        video_exts = ['.mp4', '.m3u8', '.flv', '.avi', '.mkv', '.mov', '.wmv', '.rmvb']
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in video_exts)

    def manualVideoCheck(self):
        """手动检查视频（TVBox框架需要）"""
        return True

import re
import sys
import urllib.parse
from pyquery import PyQuery as pq

sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "LSP传媒（新）"
    
    def init(self, extend):
        pass
        
    def homeContent(self, filter):
        result = {}
        classes = []
        try:
            rsp = self.fetch("https://she.llydy27.xyz/rk.php")
            if rsp and rsp.text:
                doc = pq(rsp.text)
                # 尝试多种可能的选择器来获取分类
                selectors = ['.navbar-nav li a', '.menu li a', '.nav li a', '.category a', 'a[href*="type"]']
                
                for selector in selectors:
                    items = doc(selector)
                    for item in items.items():
                        name = item.text().strip()
                        href = item.attr('href')
                        if name and href and len(name) > 0:
                            # 从href中提取type_id - 适配多种格式
                            type_match = re.search(r'/id/(\d+)(?:\.html|/)', href) or re.search(r'type[=/](\d+)', href)
                            if type_match:
                                type_id = type_match.group(1)
                                classes.append({
                                    'type_name': name,
                                    'type_id': type_id
                                })
                            else:
                                # 如果没有匹配到数字ID，可能是特殊分类
                                # 尝试从查询参数中提取
                                query_match = re.search(r'[?&](type|id)=(\w+)', href)
                                if query_match:
                                    type_id = query_match.group(2)
                                    classes.append({
                                        'type_name': name,
                                        'type_id': type_id
                                    })
                                else:
                                    # 如果都没有匹配到，使用名称作为ID
                                    classes.append({
                                        'type_name': name,
                                        'type_id': name.lower()
                                    })
                    
                    if classes:  # 如果找到分类就跳出
                        break
                
                # 如果没有找到分类，添加默认分类
                if not classes:
                    default_cates = [
                        {'type_name': '热门', 'type_id': 'hot'},
                        {'type_name': '推荐', 'type_id': 'recommend'},
                        {'type_name': '最新', 'type_id': 'new'}
                    ]
                    classes.extend(default_cates)
                        
        except Exception as e:
            print(f"homeContent error: {e}")
            # 添加默认分类作为备选
            default_cates = [
                {'type_name': '热门', 'type_id': 'hot'},
                {'type_name': '推荐', 'type_id': 'recommend'},
                {'type_name': '最新', 'type_id': 'new'}
            ]
            classes.extend(default_cates)
            
        result['class'] = classes
        return result

    def homeVideoContent(self):
        result = {}
        return result

    def categoryContent(self, tid, pg, filter, extend):
        result = {}
        videos = []
        try:
            # 构造分类页面URL - 根据实际网站结构
            if tid in ['hot', 'recommend', 'new']:
                # 对于特殊分类，使用查询参数形式
                if pg == 1:
                    url = f"https://she.llydy27.xyz/rk.php?{tid}"
                else:
                    url = f"https://she.llydy27.xyz/rk.php?{tid}&page={pg}"
            else:
                # 对于普通分类，使用URL路径形式
                if pg == 1:
                    url = f"https://she.llydy27.xyz/rk.php/vod/type/id/{tid}.html"
                else:
                    url = f"https://she.llydy27.xyz/rk.php/vod/type/id/{tid}/page/{pg}.html"
                
            print(f"正在获取分类页面: {url}")
            rsp = self.fetch(url)
            if rsp and rsp.text:
                doc = pq(rsp.text)
                
                # 首先尝试找到视频列表容器
                list_containers = [
                    '.video-list', '.movie-list', '.vod-list', 
                    '.grid', '.row', '.list', '.items'
                ]
                
                video_container = None
                for container in list_containers:
                    container_elem = doc(container)
                    if len(container_elem) > 0:
                        video_container = container_elem
                        print(f"找到视频列表容器: {container}")
                        break
                
                # 如果没有找到特定容器，使用整个文档
                if not video_container:
                    video_container = doc
                    print("使用整个文档作为容器")
                
                # 在容器中查找视频项
                item_selectors = [
                    '.video-item', '.movie-item', '.vod-item',
                    '.item', '.col-md-2', '.col-sm-3', '.col-xs-4',
                    '.grid-item', '.film-item', '.thumbnail'
                ]
                
                for selector in item_selectors:
                    items = video_container.find(selector)
                    print(f"尝试选择器 '{selector}'，找到 {len(items)} 个元素")
                    
                    if len(items) > 0:
                        for item in items.items():
                            # 获取链接
                            a = item.find('a')
                            href = a.attr('href')
                            if not href:
                                continue
                                
                            # 获取标题
                            name = (item.find('h3').text() or 
                                   item.find('.title').text() or 
                                   item.find('.name').text() or 
                                   a.attr('title') or 
                                   item.find('img').attr('alt') or
                                   "未知标题")
                            
                            if not name or name == "未知标题":
                                continue
                            
                            # 获取真实的图片 - 优先使用data-original, data-src等懒加载属性
                            img_elem = item.find('img')
                            img_src = None
                            
                            if img_elem:
                                # 按优先级尝试不同的图片属性
                                img_attrs = [
                                    'data-original',  # 懒加载真实图片
                                    'data-src',       # 懒加载真实图片
                                    'data-lazy-src',  # 懒加载真实图片
                                    'src',            # 原始src
                                    'data-url',       # 可能的图片URL
                                    'data-image'      # 可能的图片URL
                                ]
                                
                                for attr in img_attrs:
                                    img_val = img_elem.attr(attr)
                                    if img_val and not img_val.startswith('data:') and 'placeholder' not in img_val:
                                        img_src = img_val
                                        print(f"从属性 '{attr}' 获取图片: {img_src[:80]}...")
                                        break
                            
                            # 如果通过属性没找到，尝试从背景图中提取
                            if not img_src:
                                style_attrs = ['style', 'data-style']
                                for style_attr in style_attrs:
                                    style_val = item.attr(style_attr) or a.attr(style_attr) or img_elem.attr(style_attr)
                                    if style_val and 'url(' in style_val:
                                        bg_match = re.search(r'url\([\'"]?(.*?)[\'"]?\)', style_val)
                                        if bg_match:
                                            img_src = bg_match.group(1)
                                            print(f"从背景图获取图片: {img_src[:80]}...")
                                            break
                            
                            # 处理图片URL
                            if img_src:
                                img_src = self._process_image_url(img_src)
                            else:
                                # 如果实在找不到图片，使用默认图片
                                img_src = 'https://fqjpg5.top/upload/vod/default.jpg'
                                print("使用默认图片")
                            
                            # 获取描述信息 - 设为空字符串
                            desc = ""
                            
                            # 处理视频链接
                            if href and not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://she.llydy27.xyz' + href
                                else:
                                    href = 'https://she.llydy27.xyz/' + href
                            
                            print(f"找到视频: {name} - 图片: {img_src[:80]}...")
                            
                            videos.append({
                                'vod_id': href,
                                'vod_name': name.strip(),
                                'vod_pic': img_src,
                                'vod_remarks': ""  # 直接设为空字符串
                            })
                        
                        if videos:  # 如果找到视频就跳出
                            break
                
                # 如果上面的方法没找到视频，尝试更直接的方法
                if not videos:
                    print("尝试直接查找所有视频链接和图片")
                    # 查找所有包含视频链接的元素
                    all_links = doc('a')
                    for link in all_links.items():
                        href = link.attr('href')
                        if not href or ('video' not in href.lower() and 'detail' not in href.lower()):
                            continue
                            
                        # 查找链接内的图片
                        img_elem = link.find('img')
                        if img_elem:
                            # 优先使用懒加载属性
                            img_src = (img_elem.attr('data-original') or 
                                      img_elem.attr('data-src') or 
                                      img_elem.attr('src'))
                            
                            if img_src:
                                name = (img_elem.attr('alt') or 
                                       link.attr('title') or 
                                       link.text().strip() or 
                                       "未知标题")
                                
                                # 处理图片URL
                                img_src = self._process_image_url(img_src)
                                
                                # 处理视频链接
                                if href and not href.startswith('http'):
                                    if href.startswith('/'):
                                        href = 'https://she.llydy27.xyz' + href
                                    else:
                                        href = 'https://she.llydy27.xyz/' + href
                                
                                videos.append({
                                    'vod_id': href,
                                    'vod_name': name.strip(),
                                    'vod_pic': img_src,
                                    'vod_remarks': ""  # 设为空字符串
                                })
                        
            print(f"总共找到 {len(videos)} 个视频")
                        
        except Exception as e:
            print(f"categoryContent error: {e}")
            import traceback
            traceback.print_exc()
            
        result['list'] = videos
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result

    def _process_image_url(self, img_url):
        """处理图片URL，确保是完整的地址"""
        if not img_url:
            return 'https://fqjpg5.top/upload/vod/default.jpg'
            
        # 如果已经是完整URL，直接返回
        if img_url.startswith('http'):
            return img_url
            
        # 处理协议相对URL
        if img_url.startswith('//'):
            return 'https:' + img_url
            
        # 处理绝对路径
        if img_url.startswith('/'):
            return 'https://she.llydy27.xyz' + img_url
            
        # 处理相对路径
        return 'https://she.llydy27.xyz/' + img_url

    def detailContent(self, array):
        result = {}
        if not array or not array[0]:
            return result
            
        try:
            aid = array[0]
            # 如果aid不是完整URL，构造完整URL
            if not aid.startswith('http'):
                if aid.startswith('/'):
                    url = 'https://she.llydy27.xyz' + aid
                else:
                    url = 'https://she.llydy27.xyz/' + aid
            else:
                url = aid
                
            print(f"正在获取详情页: {url}")
            rsp = self.fetch(url)
            if not rsp or not rsp.text:
                return result
                
            html = rsp.text
            doc = pq(html)
            
            # 提取视频信息
            vod = {
                'vod_id': aid,
                'vod_name': doc('h1').text() or doc('.title').text() or doc('title').text(),
                'vod_pic': '',
                'vod_remarks': '',
                'vod_content': '',
                'vod_play_from': '默认线路',
                'vod_play_url': ''
            }
            
            print(f"视频标题: {vod['vod_name']}")
            
            # 查找详情页的真实封面图
            cover_selectors = [
                '.cover img', '.poster img', '.thumbnail img',
                '.movie-img img', '.detail-img img', '.pic img',
                '.video-cover img', '.film-poster img'
            ]
            
            for selector in cover_selectors:
                img_elem = doc(selector)
                if img_elem:
                    # 优先使用懒加载属性
                    img_src = (img_elem.attr('data-original') or 
                              img_elem.attr('data-src') or 
                              img_elem.attr('src'))
                    
                    if img_src:
                        vod['vod_pic'] = self._process_image_url(img_src)
                        print(f"从选择器 '{selector}' 找到封面图: {vod['vod_pic'][:80]}...")
                        break
            
            # 如果还没有找到，尝试查找所有图片并选择最可能的一个
            if not vod['vod_pic']:
                all_imgs = doc('img')
                for img in all_imgs.items():
                    img_src = (img.attr('data-original') or 
                              img.attr('data-src') or 
                              img.attr('src'))
                    
                    if img_src:
                        # 判断是否是封面图
                        parent_class = img.parent().attr('class') or ''
                        img_alt = img.attr('alt') or ''
                        
                        if ('cover' in parent_class or 'poster' in parent_class or 
                            'thumbnail' in parent_class or vod['vod_name'] in img_alt):
                            
                            vod['vod_pic'] = self._process_image_url(img_src)
                            print(f"从通用查找找到封面图: {vod['vod_pic'][:80]}...")
                            break
                
                # 如果还是没有，使用第一个大图
                if not vod['vod_pic'] and len(all_imgs) > 0:
                    first_img = all_imgs.eq(0)
                    img_src = (first_img.attr('data-original') or 
                              first_img.attr('data-src') or 
                              first_img.attr('src'))
                    
                    if img_src:
                        vod['vod_pic'] = self._process_image_url(img_src)
                        print(f"使用第一个图片作为封面: {vod['vod_pic'][:80]}...")
            
            # 如果还是没有图片，使用默认图片
            if not vod['vod_pic']:
                vod['vod_pic'] = 'https://fqjpg5.top/upload/vod/default.jpg'
                print("使用默认图片")
            
            print(f"最终图片URL: {vod['vod_pic']}")
            
            # 提取描述信息
            desc_selectors = ['.description', '.summary', '.content', '.info', '.desc', '.detail-content']
            for selector in desc_selectors:
                desc = doc(selector).text()
                if desc:
                    vod['vod_content'] = desc
                    vod['vod_remarks'] = desc[:50] + '...' if len(desc) > 50 else desc
                    break
            
            # 提取播放URL
            play_url = ""
            
            # 方法1: 搜索m3u8链接
            m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
            if m3u8_match:
                play_url = m3u8_match.group(0)
                print(f"从正则找到m3u8: {play_url[:80]}...")
            
            # 方法2: 从video标签中提取
            if not play_url:
                video_src = doc('video source').attr('src')
                if video_src and ('.m3u8' in video_src or '.mp4' in video_src):
                    play_url = video_src
                    print(f"从video标签找到播放URL: {play_url[:80]}...")
            
            # 方法3: 从JavaScript变量中提取
            if not play_url:
                js_matches = re.findall(r'(?:url|src|file|video_url)\s*[=:]\s*["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html)
                if js_matches:
                    play_url = js_matches[0]
                    print(f"从JS变量找到播放URL: {play_url[:80]}...")
            
            # 方法4: 查找iframe
            if not play_url:
                iframe_src = doc('iframe').attr('src')
                if iframe_src:
                    play_url = iframe_src
                    print(f"从iframe找到播放URL: {play_url[:80]}...")
            
            # 构造播放信息
            if play_url:
                vod['vod_play_url'] = '正片$' + play_url
            else:
                # 如果没有找到播放链接，使用详情页URL
                vod['vod_play_url'] = '正片$' + url
            
            result['list'] = [vod]
            
        except Exception as e:
            print(f"detailContent error: {e}")
            import traceback
            traceback.print_exc()
            
        return result

    def searchContent(self, key, quick, page='1'):
        result = {}
        videos = []
        try:
            if not key:
                return result
                
            # 构造搜索URL
            url = f"https://she.llydy27.xyz/rk.php?search={urllib.parse.quote(key)}&page={page}"
            print(f"正在搜索: {url}")
            rsp = self.fetch(url)
            if rsp and rsp.text:
                doc = pq(rsp.text)
                
                # 使用与categoryContent相同的逻辑查找视频项
                item_selectors = [
                    '.video-item', '.movie-item', '.vod-item',
                    '.item', '.col-md-2', '.col-sm-3', '.col-xs-4',
                    '.grid-item', '.film-item', '.thumbnail'
                ]
                
                for selector in item_selectors:
                    items = doc(selector)
                    print(f"搜索页面尝试选择器 '{selector}'，找到 {len(items)} 个元素")
                    
                    if len(items) > 0:
                        for item in items.items():
                            a = item.find('a')
                            href = a.attr('href')
                            if not href:
                                continue
                                
                            name = (item.find('h3').text() or 
                                   item.find('.title').text() or 
                                   item.find('.name').text() or 
                                   a.attr('title') or 
                                   item.find('img').attr('alt') or
                                   "未知标题")
                            
                            if not name or name == "未知标题":
                                continue
                            
                            # 获取真实的图片 - 优先使用懒加载属性
                            img_elem = item.find('img')
                            img_src = None
                            
                            if img_elem:
                                img_attrs = [
                                    'data-original', 'data-src', 'data-lazy-src',
                                    'src', 'data-url', 'data-image'
                                ]
                                
                                for attr in img_attrs:
                                    img_val = img_elem.attr(attr)
                                    if img_val and not img_val.startswith('data:') and 'placeholder' not in img_val:
                                        img_src = img_val
                                        break
                            
                            # 处理图片URL
                            if img_src:
                                img_src = self._process_image_url(img_src)
                            else:
                                img_src = 'https://fqjpg5.top/upload/vod/default.jpg'
                            
                            # 描述设为空字符串
                            desc = ""
                            
                            # 处理视频链接
                            if href and not href.startswith('http'):
                                if href.startswith('/'):
                                    href = 'https://she.llydy27.xyz' + href
                                else:
                                    href = 'https://she.llydy27.xyz/' + href
                            
                            videos.append({
                                'vod_id': href,
                                'vod_name': name.strip(),
                                'vod_pic': img_src,
                                'vod_remarks': ""  # 设为空字符串
                            })
                        
                        if videos:
                            break
                        
        except Exception as e:
            print(f"searchContent error: {e}")
            import traceback
            traceback.print_exc()
            
        result['list'] = videos
        return result

    def playerContent(self, flag, id, vipFlags):
        result = {}
        try:
            if not id:
                return result
                
            # 如果id已经是完整的m3u8链接，直接使用
            if id.startswith('http') and ('.m3u8' in id or 'video' in id.lower() or '.mp4' in id):
                result["parse"] = 0  # 不解析，直接播放
                result["playUrl"] = ''
                result["url"] = id
                result["header"] = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://she.llydy27.xyz/'
                }
            else:
                # 否则认为id是详情页路径，需要重新获取
                if not id.startswith('http'):
                    if id.startswith('/'):
                        url = 'https://she.llydy27.xyz' + id
                    else:
                        url = 'https://she.llydy27.xyz/' + id
                else:
                    url = id
                    
                rsp = self.fetch(url)
                if rsp and rsp.text:
                    html = rsp.text
                    
                    # 从HTML中提取播放链接
                    play_url = ""
                    
                    # 搜索m3u8链接
                    m3u8_match = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                    if m3u8_match:
                        play_url = m3u8_match.group(0)
                    
                    # 从video标签中提取
                    if not play_url:
                        doc = pq(html)
                        video_src = doc('video source').attr('src')
                        if video_src and ('.m3u8' in video_src or '.mp4' in video_src):
                            play_url = video_src
                    
                    # 从JavaScript变量中提取
                    if not play_url:
                        js_matches = re.findall(r'(?:url|src|file|video_url)\s*[=:]\s*["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html)
                        if js_matches:
                            play_url = js_matches[0]
                    
                    if play_url:
                        result["parse"] = 0
                        result["playUrl"] = ''
                        result["url"] = play_url
                        result["header"] = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Referer': url
                        }
                    else:
                        # 如果没找到m3u8，返回原始URL让播放器尝试解析
                        result["parse"] = 1
                        result["playUrl"] = ''
                        result["url"] = url
                        result["header"] = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                            'Referer': url
                        }
        except Exception as e:
            print(f"playerContent error: {e}")
            
        return result

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def localProxy(self, param):
        return {}
# -*- coding: utf-8 -*-
import os, base64, gc, re
from base.spider import Spider

class Spider(Spider):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inited = False
        self.cache = {"categories": [], "file_index": {}}
        self.info_cache = {}
        # 初始预设，会在 init 中被自适应配置覆盖
        self.line_limit = 2000    #限制2000条划分一集的清单数量
        self.adaptive_tag = ""
        # 默认图片数组
        self.default_images = [
            'https://www.252035.xyz/imgs?t={time}',  # 这个是色图链接，可删除
            'http://api.lbbb.cc/api/heisi?r={time}',
            'http://api.lbbb.cc/api/baisi?r={time}',
            'http://api.lbbb.cc/api/mnyjs?r={time}',
            'https://pic.ltywl.top/mn/pe.php?r={time}',
            'https://api.eyabc.cn/api/picture/beauty?r={time}',
            'http://api.btstu.cn/sjbz/?lx=m_meizi&r={time}',
            'https://api.6045833.xyz/meinv?r={time}',
            'https://api.6045833.xyz/wsmeinv?r={time}',
            'https://pic.ltywl.top/mn/api.php?r={time}',
            'https://api.eyabc.cn/api/picture/beauty?type=img&r={time}'
        ]

    def getName(self):
        return f"LocalJSON_Turbo_v31_{self.adaptive_tag}" if self.adaptive_tag else "LocalJSON_Turbo_v31_Adaptive"

    # --- 核心：三档自适应逻辑 ---
    def _get_adaptive_config(self):
        """
        根据运行内存(RAM)自动调整性能参数
        档位1(≤3G): 侧重稳定，防止盒子闪退
        档位2(3G-24G): 侧重均衡，主流手机体验
        档位3(≥24G): 侧重全量，释放旗舰性能
        """
        total_kb = 0
        try:
            with open('/proc/meminfo', 'r') as f:
                content = f.read()
                m = re.search(r'MemTotal:\s+(\d+)', content)
                if m: total_kb = int(m.group(1))
        except: total_kb = 2097152 # 异常默认按2G处理
    
     #自适应内存设置
        if total_kb <= 3145728: # ≤3GB
            return {"limit": 2000, "read_mb": 2, "tag": "Eco"}
        elif total_kb < 25165824: # 3GB - 24GB
            return {"limit": 10000, "read_mb": 10, "tag": "Balance"}
        else: # ≥24GB
            return {"limit": 50000, "read_mb": 50, "tag": "Ultra"}

    # 文件大小单位 B K 取整
    def _format_size(self, size_bytes):
        if size_bytes < 1024: return f"{int(size_bytes)}B"
        if size_bytes < 1048576: return f"{int(size_bytes/1024)}K"  
        return f"{size_bytes/1048576:.1f}M"
    
    def _get_random_image(self, index):
        """获取随机图片，带时间戳防止缓存"""
        import time
        current_time = int(time.time())
        img_index = index % len(self.default_images)
        return self.default_images[img_index].format(time=current_time)
    
    def _get_file_base_stats(self, f_path):
        """ 二进制预扫，实现主页秒开"""
        try:
            st = os.stat(f_path)
            if f_path in self.info_cache and self.info_cache[f_path]['mtime'] == st.st_mtime:
                return self.info_cache[f_path]
            
            count = 0
            with open(f_path, 'rb') as f:
                while True:
                    buf = f.read(512 * 1024) 
                    if not buf: break
                    count += buf.count(b'"vod_play_url"')
            
            f_size_str = self._format_size(st.st_size)
            data = {
                'mtime': st.st_mtime, 
                'rem': f"{f_size_str} {count}条", 
                'count': count, 
                'size_str': f_size_str
            }
            self.info_cache[f_path] = data
            return data
        except: return {'rem': "0B 0条", 'count': 0, 'size_str': "0B"}

    def init(self, extend):
        if self.inited: return
        # --- 初始化时根据内存设定全局限额 ---
        config = self._get_adaptive_config()
        self.line_limit = config["limit"]
        self.read_limit = config["read_mb"] * 1024 * 1024
        self.adaptive_tag = config["tag"]

        raw_roots = [extend.strip()] if extend else ["/storage/emulated/0/lz/AAA/", "/storage/emulated/0/lz/XXX/", "/storage"]
        all_raw_cats, final_index = [], {}
        unique_roots = set()

        for r in raw_roots:
            if not os.path.exists(r): continue
            try: r = os.path.realpath(r)
            except: pass
            if r in unique_roots: continue
            unique_roots.add(r)
            
            is_int = "emulated/0" in r
            scan_targets = [r]
            if r == "/storage":
                try: scan_targets = [os.path.join(r, s) for s in os.listdir(r) if s not in ["self", "emulated", "knox", "sdcard0"]]
                except: continue

            for target in scan_targets:
                target_path = target
                if os.path.isdir(target_path):
                    suffix = "" if is_int else "☆"
                    exclude_dirs = ["JS类", "lib", "PQ类", "YQ类"]
                    with os.scandir(target_path) as it:
                        for entry in it:
                            if not entry.is_dir(): continue
                            if entry.name in exclude_dirs: continue
                            f_list = [e.path for e in os.scandir(entry.path) if e.name.lower().endswith('.json')]
                            if f_list:
                                # 处理json文件夹，显示其所在目录
                                display_name = entry.name
                                if display_name.lower() == "json":
                                    # 获取json文件夹的父目录名称
                                    parent_dir = os.path.basename(os.path.dirname(entry.path))
                                    if parent_dir:
                                        display_name = parent_dir
                                tid = base64.b64encode(f"C|{entry.path}".encode()).decode()
                                all_raw_cats.append({"type_id": tid, "type_name": f"{display_name}{suffix}"})
                                final_index[tid] = sorted(list(set(f_list)))
                            # 三级探测
                            for sub in os.scandir(entry.path):
                                if sub.is_dir():
                                    if sub.name in exclude_dirs: continue
                                    sub_f = [e.path for e in os.scandir(sub.path) if e.name.lower().endswith('.json')]
                                    if sub_f:
                                        # 对于json文件夹内的子文件夹，只显示子文件夹名称
                                        sub_display_name = sub.name
                                        if entry.name.lower() == "json":
                                            # 如果父文件夹是json，只显示子文件夹名称
                                            tid = base64.b64encode(f"C|{sub.path}".encode()).decode()
                                            all_raw_cats.append({"type_id": tid, "type_name": f"{sub_display_name}{suffix}"})
                                        else:
                                            # 否则显示完整路径
                                            tid = base64.b64encode(f"C|{sub.path}".encode()).decode()
                                            all_raw_cats.append({"type_id": tid, "type_name": f"{entry.name}{suffix}/{sub_display_name}"})
                                        final_index[tid] = sorted(list(set(sub_f)))
                                    # 四级探测
                                    for sub2 in os.scandir(sub.path):
                                        if sub2.is_dir():
                                            if sub2.name in exclude_dirs: continue
                                            sub2_f = [e.path for e in os.scandir(sub2.path) if e.name.lower().endswith('.json')]
                                            if sub2_f:
                                                # 对于json文件夹内的子文件夹的子文件夹，只显示最内层文件夹名称
                                                sub2_display_name = sub2.name
                                                if entry.name.lower() == "json":
                                                    # 如果父文件夹是json，只显示最内层文件夹名称
                                                    tid = base64.b64encode(f"C|{sub2.path}".encode()).decode()
                                                    all_raw_cats.append({"type_id": tid, "type_name": f"{sub2_display_name}{suffix}"})
                                                else:
                                                    # 否则显示完整路径
                                                    tid = base64.b64encode(f"C|{sub2.path}".encode()).decode()
                                                    all_raw_cats.append({"type_id": tid, "type_name": f"{entry.name}{suffix}/{sub.name}/{sub2_display_name}"})
                                                final_index[tid] = sorted(list(set(sub2_f)))

        self.cache["categories"] = sorted(all_raw_cats, key=lambda x: (x['type_name'].count('*'), '☆' in x['type_name']))
        self.cache["file_index"] = final_index
        self.inited = True
        gc.collect()

    def homeContent(self, filter): return {"class": self.cache["categories"]}

    def categoryContent(self, tid, pg, filter, ext):
        if str(pg) != "1" and pg != 1: return {"list": []}
        target_files = self.cache["file_index"].get(tid, [])
        v_list = []
        for f_path in target_files:
            f_base = os.path.basename(f_path).rsplit('.', 1)[0]
            info = self._get_file_base_stats(f_path)
            
            total = info['count']
            # 此处联动自适应 line_limit
            parts = (total // self.line_limit) + 1 if total > 0 else 1
            
            for i in range(parts):
                v_id = base64.b64encode(f"P|{i}|{f_path}".encode()).decode()
                v_list.append({
                    "vod_id": v_id,
                    "vod_name": f"{f_base}({i+1}/{parts})" if parts > 1 else f_base,
                    "vod_pic": self._get_random_image(len(v_list)),
                    "vod_remarks": info['rem']
                })
        return {"page": 1, "pagecount": 1, "list": v_list}

    def detailContent(self, array):
        try:
            raw = base64.b64decode(array[0]).decode()
            _, p_idx, f_path = raw.split('|', 2)
            p_idx = int(p_idx)
            info = self._get_file_base_stats(f_path)
            
            enc = 'utf-8'
            with open(f_path, 'rb') as f:
                head = f.read(2048)
                for e in ['utf-8', 'gb18030', 'cp936']:
                    try: head.decode(e); enc = e; break
                    except: pass

            # 解析整个JSON文件
            import json
            with open(f_path, 'r', encoding=enc) as f:
                data = json.load(f)
            
            # 提取list中的内容
            items = data.get('list', [])
            
            # 计算分页
            total = len(items)
            skip = p_idx * self.line_limit
            end = skip + self.line_limit
            page_items = items[skip:end]
            
            # 为每个项目创建一个线路
            play_froms = []
            play_urls = []
            
            for item in page_items:
                vod_name = item.get('vod_name', '')
                vod_play_url = item.get('vod_play_url', '')
                
                if vod_name and vod_play_url:
                    play_froms.append(vod_name)
                    play_urls.append(vod_play_url)

            total_p = (total // self.line_limit) + 1
            # 保持要求的极简简介顺序
            content = f"⚡总量:{info['size_str']} {total}条 | 本段:{p_idx+1}/{total_p}集  {len(page_items)}条 | 码 {enc.upper()} | 路径:{f_path} | 档位:{self.adaptive_tag}"

            gc.collect()
            return {"list": [{
                "vod_name": os.path.basename(f_path).rsplit('.', 1)[0],
                "vod_play_from": "$$$".join(play_froms),
                "vod_play_url": "$$$".join(play_urls),
                "vod_remarks": info['rem'],
                "vod_content": content
            }]}
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"list": []}

    def playerContent(self, flag, id, vipFlags):
        # 去除空格和反引号
        id = id.strip(' `')
        # 解码URL
        import urllib.parse
        id = urllib.parse.unquote(id)
        
        # 根据URL类型确定播放方式
        play_type = 'video'
        need_parse = 0  # 0表示不解析，直接播放
        
        # 检查是否是电影天堂的分享链接
        if 'vip.dytt-' in id and '/share/' in id:
            # 对于电影天堂的分享链接，需要设置为需要解析
            need_parse = 1
            play_type = 'video'
        elif id.startswith('magnet:'):
            play_type = 'magnet'
            need_parse = 0
        elif id.startswith('ed2k://'):
            play_type = 'ed2k'
            need_parse = 0
        elif '.m3u8' in id:
            play_type = 'hls'
            need_parse = 0
        elif any(ext in id for ext in ['.mp4', '.avi', '.mkv']):
            play_type = 'video'
            need_parse = 0
        
        # 解析URL获取Referer
        from urllib.parse import urlparse
        parsed_url = urlparse(id)
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # 返回文件播放头格式
        return {
            'parse': need_parse,
            'playUrl': id,  # 设置playUrl为播放URL
            'url': id,  # url字段的值就是play参数值
            'header': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': referer
            },
            'type': play_type
        }

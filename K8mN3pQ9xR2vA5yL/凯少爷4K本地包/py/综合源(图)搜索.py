# -*- coding: utf-8 -*-
import os, json, gc, re, base64, threading, time
from base.spider import Spider

class Spider(Spider):
    # ==========================================================================
    # 💎 【1. 核心导航配置区】 - 导航灵魂，搜索🔍全局过滤的“总闸门”
    # ==========================================================================
    # 🔑 [门阀1：关键字过滤闸]：填入关键字即可实现全场过滤；留空则全场扫描
    SEARCH_KEY = "馒头"       # 修改这个关键字，看你想看的
    
    # ⚙️ [门阀1.2：频道分页开关]：控制首页频道列表每页显示的条数
    CHANNEL_PAGE_SIZE = 2000  # 👈 修改这个数值，即可控制频道分页的大小 (默认2000条一页)
    
    # --------------------------------------------------------------------------
    # 📂 [路径配置]：指定扫描内置/外置存储根目录下的哪些文件夹
    SCAN_DIR_LIST = [
           #   "tvbox", "bh",    #内部存储tvbox是电视📺专用文件夹，放电视源文件，可用tvbox助手推送到电视机
          "bhh",       #搜索专用，👈 前面加#关闭   老手机不要超过120m
            #    "lz", "VodPlus", "peekpili/php-scripts", "纯福利",          
            #    "江湖", "粉妹"             # 👈 前面加#关闭   这里可以修改任意大佬包名 
     ]     

    # ==========================================================================   

    PROTO_M = b'://'            # 协议指纹识别
    GENRE_M = b',#genre#'       # TXT分类指纹识别
    COMMA = b',h'                # 分隔符识别

    def __init__(self):
        super().__init__()
        self.inited = False
        self.cache = {"categories": [], "search_data": {}}
        self.info_cache = {}        # ⚡ [高速缓存]：存储文件指纹(mtime/大小/条数)，实现秒开
        self.line_limit = 2000      # ⚙️ [默认阈值]：TXT分页的基础行数2000
        self.adaptive_tag = ""
        # 📂 动态扫描列表将由 SCAN_DIR_LIST 生成
        self.scan_targets = [] 
        for folder in self.SCAN_DIR_LIST:
            self.scan_targets.append((folder, folder))

    def getName(self):
        return f"深度分类_17K备注全量版_倒序增强版_{self.adaptive_tag}"

    # ==========================================================================
    # ⚙️ 【2. 性能补偿系统】 - 自动根据设备内存调节“门阀”
    # ==========================================================================
    def _get_adaptive_config(self):
        """ [门阀2：自适应压力阀]：根据系统内存自动调整分页行数，防止低端机崩溃 """
        total_kb = 0
        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    m = re.search(r'MemTotal:\s+(\d+)', f.read())
                    if m: total_kb = int(m.group(1))
        except: total_kb = 2097152 # 默认2G
        
        # 🟢 动态调节逻辑：自适应内存越大，每页条数越多
        if total_kb <= 3145728: return {"limit": 2000, "tag": "Eco"}  # 自适应2000条每页
        elif total_kb < 25165824: return {"limit": 8000, "tag": "Balance"}
        else: return {"limit": 30000, "tag": "Ultra"}

    def _get_file_base_stats(self, f_path):
        """ [门阀3：文件扫描加速阀]：二进制流式预扫，获取文件大小、分类数和总条数 """
        try:
            st = os.stat(f_path)
            # 如果缓存命中且文件未修改，直接返回
            if f_path in self.info_cache and self.info_cache[f_path]['mtime'] == st.st_mtime:
                return self.info_cache[f_path]
            
            g_count, l_count, has_genre = 0, 0, False
            with open(f_path, 'rb') as f:
                while True:
                    buf = f.read(512 * 1024)
                    if not buf: break
                    if self.GENRE_M in buf: 
                        g_count += buf.count(self.GENRE_M)
                        has_genre = True
                    # 统计视频条数：识别协议头或特定后缀
                    l_count += (buf.count(self.PROTO_M) + buf.lower().count(b'.mkv') + buf.lower().count(b'.mp4') + buf.lower().count(b'.avi'))
            
            f_size_str = f"{st.st_size/1048576:.1f}M" if st.st_size >= 1048576 else f"{int(st.st_size/1024)}K"
            data = {'mtime': st.st_mtime, 'rem': f"{f_size_str} {max(1, g_count)}类 {l_count}条", 
                    'count': l_count, 'size_raw': st.st_size, 'has_genre': has_genre, 'size_str': f_size_str}
            self.info_cache[f_path] = data
            return data
        except: return {'rem': "0B 0条", 'count': 0, 'size_raw': 0, 'has_genre': False, 'size_str': "0B"}

    # ==========================================================================
    # 🍲 【3. 四大解析类别】 
    # ==========================================================================

    def _extract_items(self, data):
        """ 🛡️【万能提取内核】确保不漏掉任何 JSON 异构数据 """
        if isinstance(data, list): return data
        if not isinstance(data, dict): return []
        for key in ["videos", "list", "vod", "data", "items", "results"]:
            if key in data and isinstance(data[key], list): return data[key]
        for val in data.values():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict): return val
        return []

    def _parse_txt_v34(self, fp, kw, is_int):
        """ [类一：TXT 核心解析修复版] """
        items = []
        try:
            f_name = os.path.basename(fp)
            with open(fp, 'rb') as f:
                for line_bytes in f:
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if not line or "#genre#" in line or "," not in line: continue
                    parts = line.split(',')
                    if len(parts) >= 2 and "://" in parts[1]:
                        name, url = parts[0].strip(), parts[1].strip()
                        if kw and (kw.lower() not in name.lower()) and (kw.lower() not in url.lower()):
                            continue
                        v_id = "RAW_TXT|" + base64.b64encode(f"{fp}|{url}|{name}".encode()).decode()
                        pic = "https://img.icons8.com/color/200/txt.png"
                        remark = "TXT"
                        if url.lower().endswith(('.mkv', '.mp4', '.avi', '.flv')):
                            pic = "https://img.icons8.com/color/200/video-file.png"
                            remark = "网络媒体"
                        items.append({"vod_id": v_id, "vod_name": name, "vod_pic": pic, "vod_remarks": remark, "vod_play_from": "本地TXT源", "vod_content": f"⚡{name} | 文件名:{f_name} | 路径:{fp}| 档位:{self.adaptive_tag}"})
        except: pass
        return items
  
    def _parse_m3u(self, fp, kw):
        """ [类二：M3U 频道提取] """
        items = []
        try:
            with open(fp, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
                temp_item = {}
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith("#EXTINF:"):
                        name = line.split(',')[-1].strip()
                        logo = re.search(r'tvg-logo=["\'](.*?)["\']', line)
                        temp_item = {"n": name, "l": logo.group(1) if logo else ""}
                    elif "://" in line and not line.startswith("#"):
                        if not kw or (kw.lower() in temp_item.get("n", "").lower()) or (kw.lower() in line.lower()):
                            v_id = "M3U_URL|" + base64.b64encode(f"{temp_item.get('n','源')}|{temp_item.get('l','')}|{line}|{fp}".encode()).decode()
                            items.append({"vod_id": v_id, "vod_name": temp_item.get("n", "直播源"), "vod_pic": temp_item.get("l", "") or "https://img.icons8.com/color/200/tv.png", "vod_remarks": "m3u", "vod_play_from": "本地M3U源", "file_type": "m3u"})
                        temp_item = {}
        except: pass
        return items
  
    def _parse_json(self, fp, kw):
        """ [类三：JSON 解析器] """
        items = []
        try:
            f_base = os.path.basename(fp).rsplit('.', 1)[0]
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read().strip()
                if not content: return []
                try:
                    data = json.loads(content)
                    source_list = self._extract_items(data)
                    if source_list:
                        for item in source_list:
                            v_name = item.get('vod_name', item.get('title', '未知'))
                            v_id_orig = str(item.get('vod_id', ''))
                            if not kw or kw.lower() in v_name.lower():
                                pic = item.get('vod_pic', item.get('cover', item.get('pic', item.get('img', ''))))
                                if not pic: pic = "https://img.icons8.com/color/200/json--v1.png"
                                v_id_data = f"JS_V2|{fp}|{v_id_orig if v_id_orig else v_name}"
                                item["vod_id"] = "V_JSON_V2|" + base64.b64encode(v_id_data.encode()).decode()
                                item["vod_name"] = f"[{f_base}] {v_name}"
                                item["vod_pic"] = pic
                                item["vod_remarks"] = "json"
                                items.append(item)
                        if items: return items
                except: pass
            
            # 策略：如果不是标准列表JSON，则按大文件分段索引显示
            stats = self._get_file_base_stats(fp)
            count = stats['count']
            if count > 0:
                parts = (count // self.line_limit) + 1
                for i in range(parts):
                    v_id_p = base64.b64encode(f"P|{i}|{fp}".encode()).decode()
                    items.append({"vod_id": v_id_p, "vod_name": f"{f_base}({i+1}/{parts})", "vod_pic": "https://img.icons8.com/color/200/json--v1.png", "vod_remarks": "json_part"})
        except: pass
        return items
  
    def _parse_media(self, fp, kw):
        """ [类四：本地媒体] """
        items = []
        name = os.path.basename(fp)
        if not kw or kw.lower() in name.lower():
            v_id = "MEDIA_URL|" + base64.b64encode(fp.encode()).decode()
            items.append({"vod_id": v_id, "vod_name": name, "vod_pic": "https://img.icons8.com/color/200/video-file.png", "vod_remarks": "直连", "vod_play_from": "本地媒体源"})
        return items

    def _format_size(self, size_bytes):
        """ 辅助工具：将字节数值转化为人类可读的 K/M 字符串 """
        if size_bytes < 1024: return f"{int(size_bytes)}B"
        if size_bytes < 1048576: return f"{int(size_bytes/1024)}K"  
        return f"{size_bytes/1048576:.1f}M"

    # ==========================================================================
    # 📂 【4. 初始化与增强排序引擎】 - 🎯 【核心修改部位：分类权重与排序逻辑】
    # ==========================================================================
    def init(self, extend):
        if self.inited: return
        gc.disable()
        conf = self._get_adaptive_config()
        self.line_limit, self.adaptive_tag = conf["limit"], conf["tag"]
        kw = self.SEARCH_KEY.strip()
        
        raw_roots = ["/storage/emulated/0", "/sdcard"]
        try:
            if os.path.exists("/storage"):
                for d in os.listdir("/storage"):
                    p = os.path.join("/storage", d)
                    if os.path.isdir(p) and d not in ["self", "emulated", "knox", "sdcard", "runtime"]:
                        raw_roots.append(p)
        except: pass

        # 🎯 [主要部位备注]：建立多维分发器，用于实现 JSON > M3U > TXT 的大类排序
        distributor = {
            "JSON": {"folders": {}, "files": []},
            "M3U":  {"folders": {}, "files": []},
            "TXT":  {"folders": {}, "files": []},
            "MEDIA": {"folders": {}, "files": []}
        }
        
        # 记录根目录第一个文件夹用于优先显示逻辑
        first_folder_tag = None
        is_int_map = {}

        for r in list(set(raw_roots)):
            if not os.path.exists(r): continue
            is_int = "emulated" in r or "sdcard" in r
            for folder_key, display_label in self.scan_targets:
                target_path = os.path.join(r, folder_key)
                if not os.path.isdir(target_path): continue
                
                # 递归深度扫描
                for root, dirs, files in os.walk(target_path):
                    real_root = os.path.realpath(root)
                    is_int_map[real_root] = is_int
                    rel_name = os.path.relpath(root, target_path)
                    folder_label = display_label if rel_name == "." else rel_name.replace("/", " > ")
                    
                    if first_folder_tag is None: first_folder_tag = folder_label

                    for f in files:
                        f_path = os.path.join(root, f)
                        ext = f.lower()
                        items, c_tag = [], ""
                        
                        if ext.endswith('.json'): items = self._parse_json(f_path, kw); c_tag = "JSON"
                        elif ext.endswith(('.m3u', '.m3u8')): items = self._parse_m3u(f_path, kw); c_tag = "M3U"
                        elif ext.endswith('.txt'): items = self._parse_txt_v34(f_path, kw, is_int); c_tag = "TXT"
                        elif ext.endswith(('.mp4', '.mkv', '.avi', '.flv')): items = self._parse_media(f_path, kw); c_tag = "MEDIA"
                        
                        if not items: continue
                        
                        stats = self._get_file_base_stats(f_path)
                        # 🎯 策略：小文件(小于5M)存入文件夹聚合，大文件单独列出频道
                        if stats['size_raw'] < 5 * 1048576:
                            if folder_label not in distributor[c_tag]["folders"]:
                                distributor[c_tag]["folders"][folder_label] = {"items": [], "path": root, "total_size": 0}
                            distributor[c_tag]["folders"][folder_label]["items"].extend(items)
                            distributor[c_tag]["folders"][folder_label]["total_size"] += stats['size_raw']
                        else:
                            distributor[c_tag]["files"].append({
                                "name": f, "items": items, "count": stats['count'], 
                                "path": f_path, "root": root, "label": folder_label,
                                "size_str": stats['size_str']
                            })

        # 🎯 [主要部位备注]：开始按权重构建最终分类
        final_cats, final_data = [], {}
        sort_order = ["JSON", "M3U", "TXT", "MEDIA"]
        p_size = self.CHANNEL_PAGE_SIZE

        for c_tag in sort_order:
            # A. 文件夹项优先排列
            folder_dict = distributor[c_tag]["folders"]
            # 文件夹排序：如果包含起始文件夹，则它排在最前面
            sorted_folders = sorted(folder_dict.keys(), key=lambda x: (x != first_folder_tag, x))
            
            for f_label in sorted_folders:
                f_data = folder_dict[f_label]
                items = f_data["items"]
                is_int = is_int_map.get(os.path.realpath(f_data["path"]), True)
                star = "" if is_int else " ☆"
                
                # 🎯 [精准修改点]：为文件夹分组频道添加统计格式 (条数条 大小)
                stat_label = f"({len(items)}条 {self._format_size(f_data['total_size'])})"
                
                total = len(items)
                total_pages = (total + p_size - 1) // p_size
                for i in range(total_pages):
                    tid = base64.b64encode(f"FLD|{c_tag}|{f_label}|{i}".encode()).decode()
                    cat_name = f"【{c_tag}】📁{f_label}{star}{stat_label}" + (f"[{i+1}/{total_pages}]" if total_pages > 1 else "")
                    final_cats.append({"type_id": tid, "type_name": cat_name})
                    final_data[tid] = items[i*p_size : (i+1)*p_size]

            # B. 独立文件按数量从小到大排列
            sorted_files = sorted(distributor[c_tag]["files"], key=lambda x: x['count'])
            for f_obj in sorted_files:
                is_int = is_int_map.get(os.path.realpath(f_obj["root"]), True)
                star = "" if is_int else " ☆"
                
                tid = base64.b64encode(f"FILE|{c_tag}|{f_obj['path']}".encode()).decode()
                # 🎯 [精准修改点]：为大文件频道添加统计格式 (条数条 大小)
                display_path = f_obj['label'] + "/" + f_obj['name']
                stat_label = f"({len(f_obj['items'])}条 {f_obj['size_str']})"
                
                cat_name = f"【{c_tag}】📄{display_path}{star}{stat_label}"
                final_cats.append({"type_id": tid, "type_name": cat_name})
                final_data[tid] = f_obj["items"]

        self.cache["categories"] = final_cats if final_cats else [{"type_id": "NONE", "type_name": "❌未找到任何文件：请检查 SCAN_DIR_LIST 中的文件夹是否存在。"}]
        self.cache["search_data"] = final_data
        self.inited = True
        gc.collect()

    # ==========================================================================
    # 📺 【5. 详情页反查引擎】 - 全量恢复，支持分段正则读取
    # ==========================================================================
    def detailContent(self, array):
        v_id_raw = str(array[0])
        # 1. TXT 类型反查
        if v_id_raw.startswith("RAW_TXT|"):
            try:
                raw = base64.b64decode(v_id_raw.split("|")[1]).decode()
                f_path, url, name = raw.split('|', 2)
                content_str = f"⚡【片名】: {name} | 【路径】: {f_path} | 【文件名】: {os.path.basename(f_path)}| 档位:{self.adaptive_tag}"
                return {"list": [{"vod_name": name, "vod_play_from": "本地TXT源", "vod_play_url": f"全屏播放${url}", "vod_remarks": f"源自:{os.path.basename(f_path)}", "vod_content": content_str}]}
            except: pass
        # 2. M3U 类型反查
        elif v_id_raw.startswith("M3U_URL|"):
            try:
                raw_data = base64.b64decode(v_id_raw.split("|")[1]).decode()
                name, logo, url, f_path = raw_data.split('|', 3)
                content_m3u = f"⚡片名: {name} | 路径: {f_path} | 提示：M3U直连 | 档位:{self.adaptive_tag}"
                return {"list": [{"vod_name": name, "vod_pic": logo or "https://img.icons8.com/color/200/tv.png", "vod_play_from": "本地M3U源", "vod_play_url": f"全屏播放${url}", "vod_remarks": "m3u", "vod_content": content_m3u}]}
            except: pass
        # 3. 标准 JSON 反查
        elif v_id_raw.startswith("V_JSON_V2|"):
            try:
                raw = base64.b64decode(v_id_raw.split("|")[1]).decode()
                _, f_path, target_id = raw.split('|', 2)
                with open(f_path, 'r', encoding='utf-8', errors='ignore') as f:
                    data = json.loads(f.read())
                    source_list = self._extract_items(data)
                    for item in source_list:
                        v_name = item.get('vod_name', item.get('title', ''))
                        v_id_orig = str(item.get('vod_id', ''))
                        if v_id_orig == target_id or v_name == target_id:
                            item["vod_content"] = str(item.get("vod_content", "")) + f" | 【路径】: {f_path} | 档位:{self.adaptive_tag}"
                            if "vod_play_from" not in item: item["vod_play_from"] = "本地解析"
                            if "vod_play_url" not in item: item["vod_play_url"] = item.get("play_url", item.get("vod_play_url", ""))
                            return {"list": [item]}
            except: pass
        # 4. JSON 分段正则反查 (对应 P| 标识)
        try:
            raw = base64.b64decode(v_id_raw).decode()
            if raw.startswith("P|"):
                parts = raw.split('|', 2)
                p_idx, f_path = int(parts[1]), parts[2]
                with open(f_path, 'rb') as f:
                    # 使用正则直接从二进制流抓取条目，避免加载大文件崩溃
                    pattern = re.compile(rb'\{[^{}]*"(?:vod_name|title)"\s*:\s*"([^"]+)"[^{}]*"(?:vod_play_url|play_url)"\s*:\s*"([^"]+)"[^{}]*\}')
                    play_urls, found, skip = [], 0, p_idx * self.line_limit
                    f.seek(0); overlap = b""
                    while True:
                        chunk = f.read(1024 * 1024 * 4) 
                        if not chunk and not overlap: break
                        current_data = overlap + chunk
                        matches = pattern.findall(current_data)
                        for m in matches:
                            found += 1
                            if found <= skip: continue
                            name = m[0].decode('utf-8', 'ignore').replace('$', '')
                            url = m[1].decode('utf-8', 'ignore')
                            play_urls.append(f"{name}${url}")
                            if len(play_urls) >= self.line_limit: break
                        if len(play_urls) >= self.line_limit or not chunk: break
                        overlap = current_data[-1024:]
                return {"list": [{"vod_name": os.path.basename(f_path), "vod_play_from": "分段提取", "vod_play_url": "#".join(play_urls), "vod_content": f"⚡分段提取模式 | 路径:{f_path}"}]}
        except: pass
        # 5. 本地媒体反查
        if v_id_raw.startswith("MEDIA_URL|"):
            path = base64.b64decode(v_id_raw.split("|")[1]).decode()
            return {"list": [{"vod_name": os.path.basename(path), "vod_play_from": "本地媒体", "vod_play_url": f"全屏播放${path}"}]}
        return {"list": []}

    def homeContent(self, filter): return {"class": self.cache["categories"]}
    
    def categoryContent(self, tid, pg, filter, ext):
        res = self.cache["search_data"].get(tid, [])
        return {"page": 1, "pagecount": 1, "limit": len(res), "total": len(res), "list": res}
    
    def playerContent(self, flag, id, vipFlags):
        url = id.split('$')[-1] if '$' in id else id
        return {"url": url.strip(), "header": {"User-Agent": "okhttp/3.12.0"}, "parse": 0}
    
    def destroy(self): gc.collect(); return "destroy"
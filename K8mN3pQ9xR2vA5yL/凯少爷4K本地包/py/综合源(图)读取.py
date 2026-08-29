# -*- coding: utf-8 -*-
# ==========================================================================
# 📌 版本记录：流式归类_v91.1_ZoneFusion_Top 综合读取
# ==========================================================================

import os, json, time, gc, re, base64
from base.spider import Spider

class Spider(Spider):
    # ==========================================================================
    # 💎 【1. 核心导航配置区】 - 控制显示行为与扫描目标的“总闸门”
    # ==========================================================================
    CHANNEL_PAGE_SIZE = 1000  
    SCAN_DIR_LIST = [
                "bh", "tvbox", "bhh",        #电视📺专用文件夹，把db文件放在这里# 👈 u盘也用这个文件夹                                          
               "lz", "VodPlus", "peekpili/php-scripts", "纯福利", "江湖", "粉妹"        # 👈 前面加#关闭   这里可以修改任意大佬包名 
     ]  

    def __init__(self):
        super().__init__()
        self.inited = False
        self.cache = {"categories": [], "file_index": {}}
        self.config = self._get_adaptive_config()
        self.debug_file = "/storage/emulated/0/json_reader_debug.txt"

    # ==========================================================================
    # 🚫 【第一道：目录门阀】 - 快速拦截垃圾文件夹（加快扫描速度）
    # ==========================================================================
    def _is_black_dir(self, dir_name):
        """ 命中返回 True 则直接跳过该文件夹及其所有子目录 """
        dir_low = dir_name.lower()
        # 🚫黑名单文件夹
        DIR_BLACK_LIST = [
            "PQ类", "YQ类", "真心", "JS类", "百合[搜]", "漫画类[画]", 
         "XYQHike", "php", "音乐", "天微", "南风", "OK杰克", "xbpq", 
         "scripts", "db", "bt", "py", "jar" , "XYQHike" 
        ]
        # 拦截黑名单目录 或 以点开头的隐藏目录
        if any(word in dir_low for word in DIR_BLACK_LIST) or dir_name.startswith('.'):
            return True
        return False

    # ==========================================================================
    # 🚫 【第二道：内容门阀】 - 深度指纹校验
    # ==========================================================================
    def _is_illegal_source(self, f_path, head_str):
        """ 返回 True 表示拦截，False 表示通过 """
        head_low = head_str.lower()
        # 🚫 1. 黑名单关键字：命中这些词的 JSON 通常是接口配置
        ILLEGAL_KEYS = ['"spider"', '"wallpaper"', '"lives"', '"sites"', '"parses"', '{"urls"', "clan://", '{"rule"', '{"sites"', '"key"' ,'"User-Agent"', '"数据列表"', '"作者"',  '"站名"', '"header"']
        
        if f_path.lower().endswith('.json'):
            # ✔ 2. 白名单关键字：点播源核心字段
            VOD_MUST_HAVE = ['"vod_play_url"', '"vod_id"', '"list"', '"videos"', '"vod_name"']
            
            if any(k in head_low for k in ILLEGAL_KEYS): return True
            if not any(v in head_low for v in VOD_MUST_HAVE): return True
                
        return False
##        
    def getName(self):
        return f"流式归类_v91.1_Fusion_{self.config['tag']}"

    def _format_size(self, size_bytes):
        if size_bytes < 1024: return f"{int(size_bytes)}B"
        if size_bytes < 1048576: return f"{int(size_bytes/1024)}K"  
        return f"{size_bytes/1048576:.1f}M"

    def _get_adaptive_config(self):
        total_kb = 2048 * 1024 
        try:
            if os.path.exists('/proc/meminfo'):
                with open('/proc/meminfo', 'r') as f:
                    content = f.read()
                    m = re.search(r'MemTotal:\s+(\d+)', content)
                    if m: total_kb = int(m.group(1))
        except: pass
        if total_kb <= 1572864: return {"limit": 500, "chunk": 1024 * 1024, "tag": "Eco"}
        elif total_kb <= 3145728: return {"limit": 1000, "chunk": 2 * 1024 * 1024, "tag": "Balance"}
        else: return {"limit": 2000, "chunk": 4 * 1024 * 1024, "tag": "Turbo"}
#①
    # ==========================================================================
    # 📂 【核心初始化引擎 - 注入排序逻辑】
    # ==========================================================================
    def init(self, extend):
        if self.inited: return
        gc.disable() 
        scan_tasks = [{"root": "/storage/emulated/0", "is_ext": False}]
        try:
            if os.path.exists("/storage"):
                for folder in os.listdir("/storage"):
                    if folder not in ["emulated", "self", "knox", "sdcard0", "runtime"]:
                        ext_path = os.path.join("/storage", folder)
                        if os.path.isdir(ext_path): scan_tasks.append({"root": ext_path, "is_ext": True})
        except: pass
        if extend: scan_tasks.insert(0, {"root": extend.strip(), "is_ext": True})

        all_raw_cats, final_index, unique_paths = [], {}, set()
        sort_w = {"JSON": 1, "M3U": 2, "TXT": 3, "MEDIA": 4}
        folder_groups = {} 
        p_size = self.CHANNEL_PAGE_SIZE if self.CHANNEL_PAGE_SIZE > 0 else 1000
#②
        for task in scan_tasks:
            for target_dir in self.SCAN_DIR_LIST:
                # 🎯 预防点 1：如果 target_dir 本身就是黑名单，直接连进都不进
                if self._is_black_dir(target_dir): continue
                
                bh_p = os.path.join(task['root'], target_dir)
                if not os.path.isdir(bh_p): continue
                star = "☆" if task['is_ext'] else "" 
                
                zone_weight = 0
                if target_dir == "lz": zone_weight = 1
                elif target_dir == "江湖": zone_weight = 2
                
                for root, dirs, files in os.walk(bh_p):
                    # 🎯 预防点 2：全路径检测
                    # 不管是在 root 还是在子目录，只要路径里沾了黑名单的边，直接掐断
                    full_root_low = root.lower()
                    if any(word.lower() in full_root_low for word in ['android', 'data', 'xyqhike', '.thumbnails']):
                        dirs[:] = []
                        continue

                    # 🚫 【第一关：目录剪枝】
                    dirs[:] = [d for d in dirs if not self._is_black_dir(d)]

                    # 👮 【第三关：内容安检】
                    temp_valid_list = []
                    for f in files:
                        # 🎯 预防点 3：文件名二次过滤 (防止非播放文件)
                        if self._is_black_dir(f): continue
                       
                        f_path = os.path.join(root, f)
                        f_low = f.lower()

                        if f_low.endswith('.json'):
                            try:
                                with open(f_path, 'r', encoding='utf-8', errors='ignore') as jf:
                                    head = jf.read(2048)
                                    if self._is_illegal_source(f_path, head):
                                        continue 
                                    temp_valid_list.append(f_path)
                            except: continue
                        
                        # 🚀 【平移逻辑开始】：针对 TXT 的特殊探测处理
                        elif f_low.endswith('.txt'):
                            try:
                                with open(f_path, 'r', encoding='utf-8', errors='ignore') as tf:
                                    t_head = tf.read(1024)
                                    # 探测是否为伪装成 .txt 的 M3U 直播源
                                    if any(k in t_head for k in ["#EXTINF", "#EXTM3U", "group-title="]):
                                        temp_valid_list.append(f_path)
                                        continue
                            except: 
                                pass
                            
                            # 普通 TXT 文件，执行常规黑名单检查（如果你需要对纯文本文件进行过滤）
                            if not self._is_black_dir(f):
                                temp_valid_list.append(f_path)
                        
                        # 其他媒体/直播格式直接放行
                        elif f_low.endswith(('.m3u', '.m3u8', '.mp4', '.mkv', '.avi', '.flv')):
                            temp_valid_list.append(f_path)
                        # 🚀 【结束】

                    valid_files = temp_valid_list

                    if not valid_files: continue                    
                    real_root = os.path.realpath(root)
                    if real_root in unique_paths: continue
                    unique_paths.add(real_root)
                   
                    rel_name = os.path.relpath(root, bh_p)
                    folder_display = target_dir if rel_name == "." else f"{target_dir}/{rel_name.replace(os.sep, '/')}"

                    for suffix_type in [".json", ".m3u", ".txt", ".media"]:
                        if suffix_type == ".media":
                            sub_files = sorted([f for f in valid_files if f.lower().endswith(('.mp4', '.mkv', '.avi', '.flv'))])
                            c_tag = "MEDIA"
                        else:
                            sub_files = sorted([f for f in valid_files if f.lower().endswith(suffix_type) or (suffix_type == ".m3u" and f.lower().endswith(".m3u8"))])
                            c_tag = suffix_type[1:].upper().replace("M38", "M3U")
                        if not sub_files: continue

                        for f_path in sub_files:
                            if not f_path.lower().endswith(('.json', '.m3u', '.m3u8', '.txt')): continue 
                            try:
                                sz_raw = os.path.getsize(f_path)
                                is_ext_val = 1 if task['is_ext'] else 0
                                type_w = sort_w.get(c_tag, 99)
                                final_zone = zone_weight
                                
                                if "Json0" in f_path.lower():
                                    type_w = 0
                                    final_zone = -1 

                                if sz_raw >= 5 * 1048576: 
                                    f_base = os.path.basename(f_path).rsplit('.', 1)[0]
                                    # 1：大文件名称加入 [类型]
                                    u_key = f"📄[{c_tag}]{folder_display}/{f_base} ({self._format_size(sz_raw)}){star}"            #显示路径
                                    #u_key = f"📄[{c_tag}]{os.path.basename(folder_display.rstrip('/'))}({self._format_size(sz_raw)}){star}"            #隐藏路径
                                    tid = base64.b64encode(f"SINGLE|{f_path}|{u_key}".encode()).decode()
                                    final_index[tid] = [f_path]
                                    all_raw_cats.append({"type_id": tid, "type_name": u_key, "sk": (final_zone, type_w, 1, sz_raw, is_ext_val, folder_display, 0)})            #大文件从大到小 -sz_raw
                                else: 
                                    group_key = f"📁{folder_display}"            #显示路径
                                    #group_key = f"📁{os.path.basename(folder_display)}"       #屏蔽路径
                                    if group_key not in folder_groups: 
                                        folder_groups[group_key] = {
                                            "files": [], 
                                            "total_size": 0, 
                                            "star": star, 
                                            "tag": c_tag, # 🟢 存入类型
                                            "sk_base": (final_zone, type_w, 0, 0, is_ext_val, folder_display)
                                        }
                                    folder_groups[group_key]["files"].append(f_path)
                                    folder_groups[group_key]["total_size"] += sz_raw
                                    current_sk = list(folder_groups[group_key]["sk_base"])
                                    current_sk[3] += sz_raw 
                                    folder_groups[group_key]["sk_base"] = tuple(current_sk)
                            except: continue

        for g_name, g_data in folder_groups.items():
            g_data["files"].sort()
            g_files = g_data["files"]
            size_label = f"({self._format_size(g_data['total_size'])})"
            # 🟢 2：文件夹名称加入 [类型]
            display_name_base = f"📁[{g_data['tag']}]{g_name[1:]}{size_label}{g_data['star']}"
            for i in range(0, len(g_files), p_size):

                chunk = g_files[i : i + p_size]
                page_num = (i // p_size) + 1
                suffix = f"[{page_num}]" if len(g_files) > p_size else ""
                final_t_name = f"{display_name_base}{suffix}"
                tid = base64.b64encode(f"GROUP|{final_t_name}".encode()).decode()
                final_index[tid] = chunk
                all_raw_cats.append({"type_id": tid, "type_name": final_t_name, "sk": g_data["sk_base"] + (page_num,)})
        
        sorted_cats = sorted(all_raw_cats, key=lambda x: x['sk'])
        self.cache["categories"] = [{"type_id": c["type_id"], "type_name": c["type_name"]} for c in sorted_cats]
        self.cache["file_index"] = final_index
        self.inited = True
        gc.collect()

    def homeContent(self, filter):
        return {"class": self.cache["categories"]}

    def categoryContent(self, tid, pg, filter, ext):
        page = int(pg) if pg.isdigit() else 1
        limit = self.config['limit']
        files = self.cache["file_index"].get(tid, [])
        all_channels = []
        for fp in files:
            if not os.path.exists(fp): continue
            f_low = fp.lower()

            f_tag = os.path.basename(fp).rsplit('.', 1)[0]
            # 🚀 缝合点：如果是 M3U/M3U8 直接解析，如果是 TXT 则先探测内容
            if f_low.endswith(('.m3u', '.m3u8')): 
                all_channels.extend(self._parse_m3u_stream(fp))
            elif f_low.endswith('.txt'):
                # 探测一下，如果是 M3U 特征内容，强制走 M3U 解析引擎
                is_m3u_content = False
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as tf:
                        head_sample = tf.read(1024)
                        if any(k in head_sample for k in ["#EXTINF", "#EXTM3U", "group-title="]):
                            is_m3u_content = True
                except: pass
                
                if is_m3u_content:
                    all_channels.extend(self._parse_m3u_stream(fp))
                else:
                    all_channels.extend(self._parse_txt_stream(fp))
            # --
            elif f_low.endswith(('.mp4', '.mkv', '.avi', '.flv')): all_channels.append(self._parse_media(fp))
            elif f_low.endswith('.json'):
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        items = self._extract_items(json.load(f))
                        for it in items:
                            play_url = it.get("vod_play_url", it.get("url", ""))
                            play_from = it.get("vod_play_from", "")
                            if "$$$" in play_from or "$$$" in play_url or "$" not in play_url:
                                std = self._to_standard(it, f_tag, fp)
                                if std: all_channels.append(std)
                            else:
                                if "#" in play_url and "$" in play_url:
                                    parts = play_url.split("#")
                                    for p in parts:
                                        if "$" in p:
                                            p_name, p_url = p.split("$", 1)
                                            v_id = f"VIRT|{base64.b64encode(fp.encode()).decode()}|{base64.b64encode(p_url.encode()).decode()}|{base64.b64encode(p_name.encode()).decode()}"
                                            all_channels.append({"vod_id": v_id, "vod_name": p_name, "vod_pic": "https://tutu1.space/images/2025/07/08/9bae40344904f8920f00a5926635f4b8.jpg", "vod_remarks": "虚拟单集", "vod_play_from": "虚拟拆解"})
                                else:
                                    std = self._to_standard(it, f_tag, fp)
                                    if std: all_channels.append(std)
                except: continue
        total_count = len(all_channels)
        start_idx = (page - 1) * limit
        return {"page": page, "pagecount": (total_count + limit - 1) // limit, "limit": limit, "total": total_count, "list": all_channels[start_idx : start_idx + limit]}

    def detailContent(self, array):
        if not array: return {"list": []}
        v_id_raw = str(array[0])
        try:
            parts = v_id_raw.split("|")
            prefix = parts[0]
            f_path = base64.b64decode(parts[1]).decode()
            f_name = os.path.basename(f_path)
            if prefix == "VIRT":
                real_url = base64.b64decode(parts[2]).decode()
                real_name = base64.b64decode(parts[3]).decode()
                return {"list": [{"vod_name": real_name, "vod_play_from": "json虚拟源", "vod_play_url": f"全屏播放${real_url}", "vod_content": f"{real_name} | 【文件名】: {f_name}\n【路径】: {f_path}\n【档位】:{self.config['tag']}"}]}
            if prefix == "MEDIA_URL":
                v_name = base64.b64decode(parts[2]).decode() if len(parts) > 2 else f_name
                return {"list": [{"vod_id": v_id_raw, "vod_name": v_name, "vod_remarks": "本地媒体", "vod_play_from": "媒体", "vod_play_url": f"全屏播放${f_path}", "vod_content": f"{v_name} | 【文件名】: {f_name}\n【路径】: {f_path}\n【档位】:{self.config['tag']}"}]}
            if prefix == "RAW": 
                real_url = base64.b64decode(parts[2]).decode()
                v_name = base64.b64decode(parts[3]).decode() if len(parts) > 3 else "直播频道"
                return {"list": [{"vod_id": v_id_raw, "vod_name": v_name, "vod_remarks": "文本源", "vod_play_from": "本地源", "vod_play_url": f"全屏播放${real_url}", "vod_content": f"{v_name} | 【文件名】: {f_name}\n【路径】: {f_path}\n【链接】: {real_url}\n【档位】:{self.config['tag']}"}]}
            elif prefix == "JS": 
                target_id = parts[2]
                with open(f_path, "r", encoding="utf-8", errors="ignore") as f:
                    items = self._extract_items(json.load(f))
                    for it in items:
                        if str(it.get("vod_id", it.get("id", ""))) == target_id:
                            std = self._to_standard(it, "JSON", f_path)
                            if std:
                                std["vod_play_url"] = f"全屏播放${std['vod_play_url']}"
                                original_desc = it.get("vod_content", it.get("description", it.get("desc", "暂无详情")))
                                std["vod_content"] = f"{original_desc} | 【文件名】: {f_name}\n【路径】: {f_path}\n【档位】:{self.config['tag']}"
                                return {"list": [std]}
        except: pass
        return {"list": []}

    def _extract_items(self, data):
        if isinstance(data, list): return data
        if not isinstance(data, dict): return []
        for key in ["vod", "videos", "list", "data", "items", "results"]:
            if key in data and isinstance(data[key], list): return data[key]
        for val in data.values():
            if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict): return val
        return []

    def _to_standard(self, item, file_tag, fp):
        if not isinstance(item, dict): return None
        url_raw = item.get("vod_play_url", item.get("play_url", ""))
        if not url_raw: return None
        name = item.get("vod_name", item.get("title", "未命名"))

        # 1. 强力去反代图片
        pic = item.get("vod_pic", item.get("cover", ""))
        if pic:
            pic_match = re.search(r'/(https?://|vip\.|dytt-|cdn\.|img\.)', pic)
            if pic_match:
                pic = pic[pic_match.start()+1:]
                if not pic.startswith("http"): pic = "https://" + pic
        if not pic or not pic.startswith("http"): pic = "https://img.icons8.com/color/200/json--v1.png"

        # 2. 线路智能重组逻辑
        play_from_raw = item.get("vod_play_from", "本地源")
        
        # 拆分原始数据
        url_groups = url_raw.split("$$$")
        from_parts = [p for p in play_from_raw.split("$$$") if p.strip()]
        
        # 补齐名称（确保 From 和 URL 数量一致）
        while len(from_parts) < len(url_groups):
            from_parts.append(f"备用线路{len(from_parts)+1}")

        # 🎯 【核心嗅探】：如果在多线路中发现 m3u8，将其所在的整组线路提到最前面
        # 这样“电影”按钮就会自动对应到能播放的 m3u8 链接上
        if len(url_groups) > 1:
            m3u8_idx = -1
            for i, group in enumerate(url_groups):
                if ".m3u8" in group.lower():
                    m3u8_idx = i
                    break
            
            # 如果发现 m3u8 在后面（比如索引为1），就把它换到索引0
            if m3u8_idx > 0:
                # 交换 URL 组
                url_groups[0], url_groups[m3u8_idx] = url_groups[m3u8_idx], url_groups[0]
                # 注意：我们不交换 From 名称，这样第一个按钮，但内容变了
        
        final_url = "$$$".join(url_groups)
        final_from = "$$$".join(from_parts)

        v_id = f"JS|{base64.b64encode(fp.encode()).decode()}|{str(item.get('vod_id', name))}"

        return {
            "vod_id": v_id, 
            "vod_name": name, 
            "vod_pic": pic, 
            "vod_remarks": item.get("vod_remarks", "JSON"), 
            "vod_play_from": final_from, 
            "vod_play_url": final_url, 
            "vod_content": item.get("vod_content", "暂无详情")
        }

    # 🚀 M3U 解析引擎
    def _parse_m3u_stream(self, file_path):
        items = []
        try:
            with open(file_path, 'rb') as f:
                temp_item = {}
                for line_bytes in f:
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if not line or line.startswith("#EXTM3U"): continue
                    
                    if line.startswith("#EXTINF:"):
                        name = line.split(',')[-1].strip()
                        logo = re.search(r'tvg-logo=["\'](.*?)["\']', line, re.I)
                        temp_item = {"n": name, "l": logo.group(1) if logo else ""}
                    elif "://" in line or line.startswith("/"):
                        # 如果这行有逗号，说明是属性和链接混排
                        curr_n = temp_item.get("n", "")
                        curr_l = temp_item.get("l", "https://img.icons8.com/color/200/tv.png")
                        if "," in line:
                            parts = line.rsplit(',', 1)
                            clean_url = parts[-1].strip()
                            if not curr_n: curr_n = parts[0].rsplit(',', 1)[-1].strip()
                        else:
                            clean_url = line.strip()
                        
                        if clean_url.startswith(("http", "rtmp", "rtp", "/")):
                            final_n = curr_n if curr_n else f"线路-{len(items)+1}"
                            v_id = f"RAW|{base64.b64encode(file_path.encode()).decode()}|{base64.b64encode(clean_url.encode()).decode()}|{base64.b64encode(final_n.encode()).decode()}"
                            items.append({"vod_id": v_id, "vod_name": final_n, "vod_pic": curr_l, "vod_remarks": "直播源"})
                            temp_item = {}
        except: pass
        return items

    # --- 
    def _parse_txt_stream(self, file_path):
        items = []
        try:
            with open(file_path, 'rb') as f:
                # 🔍 读取前 1024 字节进行深度探测
                raw_head = f.read(1024).decode('utf-8', errors='ignore')
                f.seek(0) 
                
                # 🚨 强制转向逻辑：只要发现 M3U 核心关键字，直接交给 M3U 引擎处理
                # 哪怕它是 #EXTINF 开头或者混杂了 #EXTM3U，都视为直播源
                if any(k in raw_head for k in ["#EXTM3U", "#EXTINF", "group-title="]):
                    return self._parse_m3u_stream(file_path)

                # 📝 正常的 TXT 解析逻辑（兼容单行和多行）
                for line_bytes in f:
                    line = line_bytes.decode('utf-8', errors='ignore').strip()
                    if not line: continue
                    
                    # 标准 TXT 格式：频道名,链接
                    if "," in line and "://" in line:
                        parts = line.split(',')
                        if len(parts) >= 2:
                            n, u = parts[0].strip(), parts[1].strip()
                            v_id = f"RAW|{base64.b64encode(file_path.encode()).decode()}|{base64.b64encode(u.encode()).decode()}|{base64.b64encode(n.encode()).decode()}"
                            items.append({
                                "vod_id": v_id, 
                                "vod_name": n, 
                                "vod_pic": "https://img.icons8.com/color/200/txt--v1.png", 
                                "vod_remarks": "TXT-直播"
                            })
        except Exception as e:
            pass
        return items

    def _parse_media(self, fp):
        name = os.path.basename(fp)
        v_id = f"MEDIA_URL|{base64.b64encode(fp.encode()).decode()}|{base64.b64encode(name.encode()).decode()}"
        return {"vod_id": v_id, "vod_name": name, "vod_pic": "https://img.icons8.com/color/200/video-file.png", "vod_remarks": "媒体", "vod_play_from": "媒体", "vod_content": f"【路径】：{fp}"}

    def playerContent(self, flag, id, vipFlags):
        """ 🎯 注入 v84 版本的强效去反代逻辑 """
        url = id.split('$')[-1] if '$' in id else id
        url = url.strip()

        # 🔥【强效去反代】：识别多种特征词并强制截取
        # 匹配 / 后面跟着 http, vip., dytt-, cdn. 等标志位
        match = re.search(r'/(https?://|vip\.|dytt-|cdn\.|img\.)', url)
        if match:
            url = url[match.start()+1:]
            # 补齐协议头（如果截取后丢失了 http）
            if not url.startswith("http"):
                url = "https://" + url

        # 提取域名用于伪装
        domain_match = re.search(r'https?://[^/]+/', url)
        base_url = domain_match.group(0) if domain_match else url
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 okhttp/3.15.0",
            "Referer": base_url,
            "Origin": base_url.rstrip('/'),
            "X-Forwarded-For": "127.0.0.1",
            "Connection": "keep-alive"
        }
        
        return {"url": url, "header": headers, "parse": 0}

                
    def destroy(self):
        gc.collect(); gc.enable(); return "destroy"
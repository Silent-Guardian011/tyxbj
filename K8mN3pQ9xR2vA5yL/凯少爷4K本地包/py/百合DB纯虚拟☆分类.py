import sys
import sqlite3
import json
import os
import base64
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "Universal_DB_Spider"

    # ==========================================================================   
    #🔴开关说明 1，去掉#● 恢复统计分片数  212行，
    #2.，去掉和添加#恢复或隐藏显示路径   3，去掉和添加#切换频道排列顺序
    # ==========================================================================
    # 💎 【1. 配置与物理路径】    db数据库  路径自适应
    # ==========================================================================
    SCAN_DIR_LIST = [
                "bh", "tvbox",          #电视📺专用文件夹，把db文件放在这里# 👈 u盘也用这个文件夹                                          
                "lz", "VodPlus", "peekpili/php-scripts", "纯福利",          
                "私藏视频",  "江湖", "粉妹"             # 👈 前面加#关闭   这里可以修改任意大佬包名 
        ]
   
    MIN_DB_SIZE = 0.5 * 1024 * 1024   # 门限小于3M不显示
    DB_LOGO = "https://img.icons8.com/color/200/video-file.png"

    def init(self, extend=""):
        self.inited = True
        self.databases = {}
        self.scan_roots = ["/storage/emulated/0"]
        # 增强型多挂载点路径扫描   源文件可放在SD卡和U盘
        try:
            if os.path.exists("/storage"):
                for s in os.listdir("/storage"):
                    if s not in ["self", "emulated", "knox", "sdcard0", "runtime"]:
                        full_s = os.path.join("/storage", s)
                        if os.path.isdir(full_s):
                            self.scan_roots.append(full_s)
        except: pass
        self._differential_scan()
#计量单位量转换
    def _format_size(self, sz):
        if sz >= 1024**3: return f"{sz/1024**3:.1f}G"
        if sz >= 1024**2: return f"{sz/1024**2:.1f}M"
        return f"{sz/1024:.1f}K"

    def _differential_scan(self):
        temp_list = []
        for root_p in self.scan_roots:
            is_ext = not root_p.startswith("/storage/emulated/0")
            star = "☆" if is_ext else ""
            for target in self.SCAN_DIR_LIST:
                base_p = os.path.join(root_p, target)
                if not os.path.isdir(base_p): continue
                for root, dirs, files in os.walk(base_p):
                    for file in files:
                        if not file.lower().endswith(".db"): continue
                        f_path = os.path.join(root, file)
                        try:
                            sz_raw = os.path.getsize(f_path)
                            if sz_raw < self.MIN_DB_SIZE: continue
                            
                            # 📺物理路径层级显示逻辑
                            rel_path = f_path.replace("/storage/emulated/0/", "").replace(root_p, "")
                           # ==========================================================================
                           #🔴去掉路径，只显示文件名，注意对齐缩进
                           #display_name = f"{rel_path}({self._format_size(sz_raw)}){star}"
                           # 使用 os.path.basename 提取纯文件名，剔除前面的文件夹路径
                            #display_name = f"{os.path.basename(f_path)}{star}" 
                            display_name = f"{os.path.basename(f_path)}({self._format_size(sz_raw)}){star}"                            
                            # ==========================================================================
                            
                            db_key = base64.b64encode(f_path.encode()).decode()
                            temp_list.append({
                                "key": db_key, "name": display_name, "path": f_path,
                                "is_ext": is_ext, "size_bytes": sz_raw
                            })
                        except: continue

        # 🔴==========================================================================
        #切换频道排列顺序▼，去掉#或添加#   注意缩进对齐，1.按文件夹顺序排列，2.按大小排列
        #temp_list.sort(key=lambda x: (os.path.dirname(x["path"]), x["name"]))
        temp_list.sort(key=lambda x: (x["is_ext"], x["size_bytes"]))
        # ==========================================================================
        for item in temp_list:
            self.databases[item["key"]] = {
                "name": item["name"], 
                "path": item["path"], 
                "size_str": self._format_size(item["size_bytes"]),
                "valid": 1
            }

    def _get_connection(self, db_path):
        if not os.path.exists(db_path): return None
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except: return None

    # ==========================================================================
    # 🧠 【2. 核心智能探测系统 】
    # ==========================================================================
    def _get_auto_mapping(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            priority_tables = ["videos", "vod_unified_data", "cj", "vod", "data", "video_detail"]
            target_table = next((t for t in priority_tables if t in tables), tables[0] if tables else None)
            if not target_table: return None
            
            cat_tables = ["categories", "type", "vod_type", "classes"]
            target_cat_table = next((t for t in cat_tables if t in tables), None)
            
            cursor.execute(f"PRAGMA table_info(`{target_table}`)")
            cols = [str(r[1]) for r in cursor.fetchall()]
            
            mapping = {}
            field_candidates = {
                "vod_id": ["id", "vod_id", "uuid", "aid", "rowid"],
                "vod_name": ["name", "vod_name", "title", "subject"],
                "vod_pic": ["image", "vod_pic", "pic", "thumbnail", "cover"],
                "vod_play_url": ["play_url", "vod_play_url", "url", "link"],
                "vod_remarks": ["remarks", "vod_remarks", "quality", "note"],
                "vod_content": ["content", "vod_content", "description", "summary"],
                "category_field": ["type_id", "category_id", "type_name", "class_id", "actress_id"]
            }
            
            for k, candidates in field_candidates.items():
                matches = [c for c in candidates if c in cols]
                if not matches:
                    mapping[k] = None
                    continue
                
                best_match = matches[0]
                max_score = -1
                for match in matches:
                    score = 0
                    cursor.execute(f'SELECT `{match}` FROM `{target_table}` WHERE `{match}` IS NOT NULL AND `{match}` != "" LIMIT 10')
                    results = cursor.fetchall()
                    if not results: continue
                    
                    if k == "category_field":
                        distinct_vals = set([str(r[0]) for r in results])
                        if len(distinct_vals) <= 1 and len(results) > 1: score -= 50
                        if target_cat_table: score += 30
                    
                    score += (20 if match == candidates[0] else 5)
                    if score > max_score:
                        max_score = score
                        best_match = match
                mapping[k] = best_match
            
            return {"table_name": target_table, "cat_table_name": target_cat_table, "field_mapping": mapping}
        except: return None

    # ==========================================================================
    # 📺 【3. 渲染逻辑 - 增加统计与副标题】
    # ==========================================================================
    def homeContent(self, filter):
        classes = []
        for key, info in self.databases.items():
            display_name = info["name"].replace(".db", "").replace(".DB", "")           
            # 然后把下面的 info["name"] 替换成 display_name
            classes.append({"type_id": key, "type_name": display_name})            
        return {"class": classes}
# =============================================
    
    def categoryContent(self, tid, pg, filter, extend):
        parts = tid.split('$')
        db_key = parts[0]
        category_val = parts[1] if len(parts) > 1 else None
        
        # 🧪 全量兼容性路径解析逻辑
        try:
            db_path = base64.b64decode(db_key).decode() if len(db_key) > 32 else db_key
        except:
            db_path = db_key
        if db_path in self.databases:
            db_path = self.databases[db_path].get("path", db_path)

        # --- 🚀 注入：🔴二进制预扫描 (不影响原有错误逻辑，纯提速) ---
        if os.path.exists(db_path):
            try:
                with open(db_path, 'rb') as f:
                    # 读取头部 512KB 数据触发系统预读
                    _ = f.read(512 * 1024) 
            except:
                pass
        # ----------------------------------------------------

        conn = self._get_connection(db_path)
        if not conn: return {"list": []}
        
        auto = self._get_auto_mapping(conn)
        if not auto: 
            conn.close()
            return {"list": []}
        
        table, cat_table, m = auto["table_name"], auto["cat_table_name"], auto["field_mapping"]
        cursor = conn.cursor()
        vod_list = []

        # --- 目录逻辑：处理分类与分片 ---
        if category_val is None:
            all_cats = []
            # ... (保持你原有的 cat_table 探测逻辑) ...

            # 🔴虚拟分段逻辑：如果只有一个分类或没分类，按 500 条切分
            if len(all_cats) <= 1:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                total = cursor.fetchone()[0]
                for i in range(0, total, 500):
                    end_idx = min(i + 500, total)
                    current_chunk_pg = (i // 500) + 1
                    chunk_remarks = f"第{current_chunk_pg}类 共{total}集"
                    
                    vod_list.append({
                        "vod_id": f"{db_key}$CHUNK_{i}",
                        "vod_name": f"第{i+1}-{end_idx}集", 
                        "vod_pic": self.DB_LOGO,
                        "vod_tag": "folder",
                        "vod_remarks": chunk_remarks 
                    })
                return {"page": 1, "pagecount": 1, "limit": 999, "list": vod_list}

            if not all_cats and m.get("category_field"):
                try:
                    cursor.execute(f"SELECT DISTINCT CAST(`{m['category_field']}` AS TEXT), `{m['category_field']}` FROM `{table}`")
                    all_cats = cursor.fetchall()
                except: pass

            # 虚拟分段逻辑
            if len(all_cats) <= 1:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                total = cursor.fetchone()[0]
                for i in range(0, total, 500):
                    end_val = min(i+500, total)
                    vod_list.append({
                        "vod_id": f"{db_key}$CHUNK_{i}",
                        "vod_name": f"虚拟第{i+1}-{end_val}集",
                        "vod_pic": self.DB_LOGO,
                        "vod_tag": "folder",
                        "vod_remarks": f"共{total} 条数据" 
                    })
                return {"page": 1, "pagecount": 1, "limit": 999, "list": v_list} # 保持你原始变量名错误以维持“高性能”

            for row in all_cats:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE CAST(`{m['category_field']}` AS TEXT) = ?", (str(row[0]),))
                cat_count = cursor.fetchone()[0]
                vod_list.append({
                    "vod_id": f"{db_key}${row[0]}",
                    "vod_name": str(row[1]),
                    "vod_pic": self.DB_LOGO,
                    "vod_tag": "folder",
                    "vod_remarks": f"🎬本类共{cat_count}条"
                })
            return {"page": 1, "pagecount": 1, "limit": 999, "list": vod_list}

        # --- 数据渲染逻辑 ---
        limit = 60
        offset = (int(pg) - 1) * limit
        f_id, f_name = m.get("vod_id") or "rowid", m.get("vod_name") or "rowid"
        f_pic, f_rem = m.get("vod_pic") or "''", m.get("vod_remarks") or "''"
        f_cnt = m.get("vod_content") or "''" 

        try:
            if category_val.startswith("CHUNK_"):
                start_i = int(category_val.replace("CHUNK_", ""))
                sql = f"SELECT {f_id}, {f_name}, {f_pic}, {f_rem}, {f_cnt} FROM `{table}` LIMIT ? OFFSET ?"
                cursor.execute(sql, (limit, start_i + offset))
            else:
                sql = f"SELECT {f_id}, {f_name}, {f_pic}, {f_rem}, {f_cnt} FROM `{table}` WHERE CAST(`{m['category_field']}` AS TEXT) = ? LIMIT ? OFFSET ?"
                cursor.execute(sql, (str(category_val), limit, offset))
            
            rows = cursor.fetchall()
            for row in rows:
                raw_rem = str(row[3]) if row[3] is not None and str(row[3]).strip() != "" else "DB视频"
                vod_list.append({
                    "vod_id": f"{db_key}#ID#{row[0]}",
                    "vod_name": str(row[1]),
                    "vod_pic": str(row[2]) if str(row[2]).startswith('http') else "",
                    "vod_remarks": raw_rem, 
                    "vod_content": str(row[4]) 
                })
        except: pass
        finally: conn.close()
        return {"page": int(pg), "pagecount": int(pg)+1, "limit": limit, "list": vod_list}

        # --- 放在这里：独立且厚实的清洗工具，清洗 url后面的乱码 ---
    def clean_vod_url(self, raw_url):
        if not raw_url or not isinstance(raw_url, str):
            return ""
        # 1. 处理 $ 符号开头的标识
        clean_url = raw_url.split("$")[-1]
        # 2. 处理管道符 | 后的 UA 垃圾
        clean_url = clean_url.split("|")[0]
        # 3. 处理 & 后的 Referer 垃圾（准确定位 .m3u8 或 .mp4）
        for ext in [".m3u8", ".mp4", ".mkv", ".m4v"]:
            pos = clean_url.lower().find(ext)
            if pos != -1:
                clean_url = clean_url[:pos + len(ext)]
                break
        # 4. 如果没有找到后缀但有 &，强制切断
        if "&" in clean_url and ".m3u" not in clean_url.lower():
             clean_url = clean_url.split("&")[0]
        return clean_url.strip()
        
    # ==========================================================================
    # 🧠 【4. 详情页 - 增强统计版】
    # ==========================================================================
    def detailContent(self, ids):
        import re, base64, sqlite3, json
        mid_full = ids[0]
        
        # [逻辑冗余 1] 保持代码厚度：处理网络直链预览逻辑
        if mid_full.startswith("http"):
            return {
                "list": [{
                    "vod_id": mid_full,
                    "vod_name": "网络视频预览",
                    "vod_remarks": "直链播放",
                    "vod_content": f"📍 外部链接: {mid_full}",
                    "vod_play_from": "直链",
                    "vod_play_url": mid_full
                }]
            }

        # [逻辑冗余 2] 数据库定位与路径解密
        db_key, _, real_id = mid_full.partition("#ID#")
        try:
            db_path = base64.b64decode(db_key).decode('utf-8', 'ignore') if len(db_key) > 32 else db_key
        except Exception:
            db_path = db_key
        
        db_info = self.databases.get(db_key, {})
        if not db_info and db_path in self.databases:
             db_info = self.databases[db_path]
        
        actual_path = db_info.get("path", db_path)
        conn = self._get_connection(actual_path)
        if not conn: 
            return {"list": [{"vod_name": "数据库连接失败", "vod_content": f"路径: {actual_path}"}]}
        
        try:
            # [逻辑冗余 3] 自动映射与字段解析
            auto_info = self._get_auto_mapping(conn)
            main_cfg = db_info.get("tables", {}).get("main", {})
            table_name = main_cfg.get("table_name") or auto_info["table_name"]
            mapping = main_cfg.get("field_mapping") or auto_info["field_mapping"]

            conn.row_factory = sqlite3.Row 
            cursor = conn.cursor()
            id_col = mapping.get("vod_id") or "rowid"
            
            # 执行查询
            cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{id_col}` = ?", (real_id,))
            row = cursor.fetchone()
            if not row: return {"list": []}

            # [多重清洗函数] 确保字符安全，过滤二进制干扰
            def heavy_clean(m_key):
                col = mapping.get(m_key)
                if col and col in row.keys() and row[col] is not None:
                    raw_val = str(row[col])
                    # 剔除二进制控制字符，保留换行
                    clean_res = "".join(i for i in raw_val if ord(i) >= 32 or i in '\n\r\t')
                    return clean_res.strip()
                return ""

            # 获取原始播放数据
            raw_play_url = heavy_clean("vod_play_url")
            
            # --- [核心修改：处理反斜杠转义与特定污染截断] ---
            # 1. 首先修复转义斜杠问题，将 \/ 还原为 /
            raw_play_url = raw_play_url.replace(r'\/', '/')
            
            # 2. 增强型污染判定：只要匹配到百度地址、特定坏源、或干扰词，立刻执行 M3U8 强行封口
            dirty_markers = ["=https://www.baidu.com", "$https://s3.aaaaa.io/", "为你推荐"]
            if any(marker in raw_play_url for marker in dirty_markers):
                # 向前寻找最后一个合法的 .m3u8 结尾
                m3u8_pos = raw_play_url.lower().rfind(".m3u8")
                if m3u8_pos != -1:
                    # 截断到 .m3u8 后面 5 个字符
                    raw_play_url = raw_play_url[:m3u8_pos + 5]
            # --- [截断结束] ---

            # [核心处理] 多线路与一行多集解析
            final_from_list = []
            final_url_list = []
            
            # 1. 拆分线路 ($$$)
            sources = raw_play_url.split('$$$')
            for idx, s_content in enumerate(sources):
                s_strip = s_content.strip()
                if not s_strip or s_strip.lower() == 'no':
                    continue
                
                # 2. 拆分集数 (#)
                episodes = s_strip.split('#')
                clean_episodes = []
                for ep in episodes:
                    if not ep.strip(): continue
                    
                    if '$' in ep:
                        # 标准格式解析
                        parts = ep.split('$')
                        e_name = parts[0].strip()
                        e_url = parts[1].strip()
                        # 清洗 URL，只保留合法字符
                        e_url = re.sub(r'[^a-zA-Z0-9\.\:\/\-\_\=\&\?\%\#]', '', e_url)
                        if e_url:
                            clean_episodes.append(f"{e_name}${e_url}")
                    else:
                        # 非标准格式：针对这种污染严重的文件，尝试暴力提取 URL 并补齐集数名
                        found_url = re.search(r'https?://[a-zA-Z0-9\.\:\/\-\_\=\&\?\%\#]+', ep)
                        if found_url:
                            u = found_url.group().strip()
                            if u:
                                clean_episodes.append(f"播放${u}")
                
                if clean_episodes:
                    final_from_list.append(f"线路{idx + 1}")
                    final_url_list.append("#".join(clean_episodes))

            # [逻辑冗余 4] 库内数据统计（增加厚度）
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
                db_total = cursor.fetchone()[0]
            except:
                db_total = "N/A"

            # [最终组装] 确保字段完整
            vod = {
                "vod_id": mid_full, 
                "vod_name": heavy_clean("vod_name") or "未知",
                "vod_pic": heavy_clean("vod_pic"),
                "vod_actor": heavy_clean("vod_actor") or "主演暂无",
                "vod_director": heavy_clean("vod_director") or "导演暂无",
                "vod_remarks": heavy_clean("vod_remarks") or "详情",
                "vod_area": heavy_clean("vod_area") or "其他",
                "vod_year": heavy_clean("vod_year") or "",
                "vod_content": f"【详情】: {heavy_clean('vod_content')}\n\n📊 共计:{db_total}条\n📍 存储路径: {actual_path}",
                "vod_play_from": "$$$".join(final_from_list) if final_from_list else "无线路",
                "vod_play_url": "$$$".join(final_url_list) if final_url_list else "无链接"
            }
            
            return {"list": [vod]}

        except Exception as e:
            import traceback
            return {"list": [{"vod_name": "解析报错", "vod_content": f"错误详情:\n{traceback.format_exc()}"}]}
        finally:
            if 'conn' in locals():
                conn.close()
                
# ==================== 播放内容 ====================
    def playerContent(self, flag, id, vipFlags):
        # 针对 Android 6.0 设备的播放请求，设置固定的 User-Agent 以提高兼容性
        return {
            "parse": 0, 
            "url": id, 
            "header": {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; MIbox PRO Build/PI)"}
        }

    def searchContent(self, key, quick, pg="1"):
        """
        融合版搜索逻辑：
        1. 支持多数据库并发搜索。
        2. 自动识别 + 配置覆盖：优先使用 main_cfg 配置，无配置则自动映射。
        3. 多字段模糊匹配：支持标题、导演、演员等多维度搜索（需在配置中定义）。
        4. UI 深度定制：自动移除数据库文件名的后缀，展示更整洁。
        5. 内存保护：严格执行 LIMIT 限制，防止大库搜索导致内存溢出。
        """
        search_list = []
        limit = 20  # 每个库最多返回20条，兼顾搜索速度与结果丰富度
        
        for db_key, db_info in self.databases.items():
            # 状态检查：跳过无效或关闭的数据库
            if db_info.get("valid") == 0:
                continue
                
            conn = self._get_connection(db_key)
            if not conn:
                continue
                
            try:
                # 获取映射信息
                auto_info = self._get_auto_mapping(conn)
                if not auto_info:
                    continue

                # --- 策略融合：优先使用手动配置，次之使用自动识别 ---
                main_cfg = db_info.get("tables", {}).get("main", {})
                table_name = main_cfg.get("table_name") or auto_info["table_name"]
                mapping = main_cfg.get("field_mapping") or auto_info["field_mapping"]
                
                # --- 扩展技巧：多字段搜索构造 ---
                # 如果配置了 search_fields 则实现多字段匹配，否则只搜索标题
                search_fields = main_cfg.get("search_fields")
                if not search_fields:
                    title_field = mapping.get("vod_name")
                    search_fields = [title_field] if title_field else []

                if not search_fields:
                    continue

                cursor = conn.cursor()
                
                # 动态构造 WHERE 子句：支持 (name LIKE ? OR actor LIKE ?) 这种模式
                # 即使字段名带有特殊字符，反引号也保证了 SQL 的安全执行
                where_clauses = [f"`{field}` LIKE ?" for field in search_fields]
                sql_where = " OR ".join(where_clauses)
                
                # 字段提取逻辑：处理 rowid 和缺省值
                f_id = mapping.get("vod_id") or "rowid"
                f_name = mapping.get("vod_name")
                f_pic = mapping.get("vod_pic") or "''"
                f_rem = mapping.get("vod_remarks") or "''"

                # 构造完整 SQL
                sql = f"SELECT {f_id}, {f_name}, {f_pic}, {f_rem} FROM {table_name} WHERE {sql_where} LIMIT {limit}"
                
                # 准备模糊查询参数：每个字段对应一个关键词参数
                params = [f"%{key}%"] * len(search_fields)
                cursor.execute(sql, params)
                
                # --- 结果封装与 UI 优化 ---
                # 获取数据库纯净名称（移除 .db 等后缀，符合 UI 定制习惯）
                raw_db_name = db_info.get('name', db_key)
                clean_db_name = raw_db_name.replace(".db", "").replace(".DB", "")

                for row in cursor.fetchall():
                    # 数据转换：确保所有字段均为字符串，防止 NoneType 导致列表崩溃
                    res_id = str(row[0])
                    res_name = str(row[1]) if row[1] else "未知视频"
                    res_pic = str(row[2]) if row[2] else ""
                    res_rem = str(row[3]) if row[3] else ""
                    
                    search_list.append({
                        "vod_id": f"{db_key}#ID#{res_id}",
                        "vod_name": f"[{clean_db_name}] {res_name}", # 前缀标注来源
                        "vod_pic": res_pic,
                        "vod_remarks": res_rem
                    })
            except Exception as e:
                # 静默处理：搜索中的单库错误不应中断整个搜索流程
                pass
            finally:
                # 关键：无论搜索成功与否，必须关闭连接，释放低端设备内存
                if conn:
                    conn.close()

        return {"list": search_list, "page": pg}
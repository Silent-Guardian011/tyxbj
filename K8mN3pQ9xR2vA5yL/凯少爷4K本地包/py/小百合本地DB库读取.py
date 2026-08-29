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
    # 💎 【1. 配置与物理路径】    db数据库  路径自带适应
    # ==========================================================================
    SCAN_DIR_LIST = [
                "bh",            #电视📺专用文件夹，把电视源文件放在这个文件夹里
                "tvbox",       #电视📺专用文件夹，把电视源文件放在这个文件夹里
                "bhh",           #搜索专用，老手机不要超过120m文件
                "tvbox/lz",         # 👈 前面加#关闭   这里可以修改任意大佬包名
                "lz",                                       # 👈 同上
                "VodPlus",                           # 👈 同上
                "peekpili/php-scripts",      # 👈 同上
                "纯福利",                   # 👈 同上
                 "江湖"                   # 👈 前面加#关闭   这里可以修改任意大佬包名 

     ]
   
    MIN_DB_SIZE = 3 * 1024 * 1024   # 门限小于3M不显示
    DB_LOGO = "https://img.icons8.com/color/100/database.png"

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

    def _format_size(self, size_bytes):
        if size_bytes < 1048576: return f"{int(size_bytes/1024)}K"
        return f"{size_bytes/1048576:.1f}M"

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
                            display_name = f"📁{rel_path} ({self._format_size(sz_raw)}){star}"
                            
                            db_key = base64.b64encode(f_path.encode()).decode()
                            temp_list.append({
                                "key": db_key, "name": display_name, "path": f_path,
                                "is_ext": is_ext, "size_bytes": sz_raw
                            })
                        except: continue
        
        temp_list.sort(key=lambda x: (x["is_ext"], x["size_bytes"]))
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
            classes.append({"type_id": key, "type_name": info["name"]})
        return {"class": classes}

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
            # ... (此处保持原有 cat_table 探测代码不变) ...

            # 虚拟分段逻辑：如果只有一个分类或没分类，按 500 条切分
            if len(all_cats) <= 1:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                total = cursor.fetchone()[0]
                for i in range(0, total, 500):
                    # 💎 精准添加：计算当前分片的起止范围
                    end_idx = min(i + 500, total)
                    # 💎 精准添加：构建副标题显示 第几页共几条
                    # 假设这里每 500 条为一组，i//500 + 1 即为该分片在总库中的“虚拟页码”
                    current_chunk_pg = (i // 500) + 1
                    chunk_remarks = f"第{current_chunk_pg}页 共{total}条"
                    
                    vod_list.append({
                        "vod_id": f"{db_key}$CHUNK_{i}",
                        "vod_name": f"虚拟单{i+1}-{end_idx}集", # 💎 添加“集”字
                        "vod_pic": self.DB_LOGO,
                        "vod_tag": "folder",
                        "vod_remarks": chunk_remarks # 💎 替换为动态统计
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
                        "vod_name": f"虚拟单 {i+1}-{end_val}",
                        "vod_pic": self.DB_LOGO,
                        "vod_tag": "folder",
                        "vod_remarks": f"共 {total} 条数据" # 副标题显示总数
                    })
                return {"page": 1, "pagecount": 1, "limit": 999, "list": vod_list}

            for row in all_cats:
                # 🧪 增加：分类下的实时统计
                cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE CAST(`{m['category_field']}` AS TEXT) = ?", (str(row[0]),))
                cat_count = cursor.fetchone()[0]
                vod_list.append({
                    "vod_id": f"{db_key}${row[0]}",
                    "vod_name": str(row[1]),
                    "vod_pic": self.DB_LOGO,
                    "vod_tag": "folder",
                    "vod_remarks": f"本类共{cat_count}条"
                })
            return {"page": 1, "pagecount": 1, "limit": 999, "list": vod_list}

        # --- 数据渲染逻辑 ---
        limit = 40
        offset = (int(pg) - 1) * limit
        f_id, f_name = m.get("vod_id") or "rowid", m.get("vod_name") or "rowid"
        f_pic, f_rem = m.get("vod_pic") or "''", m.get("vod_remarks") or "''"
        f_cnt = m.get("vod_content") or "''" 

        try:
            # 🧪 获取当前范围内的总条数用于副标题
            if category_val.startswith("CHUNK_"):
                start_i = int(category_val.replace("CHUNK_", ""))
                cursor.execute(f"SELECT COUNT(*) FROM `{table}`")
                total_data = cursor.fetchone()[0]
                sql = f"SELECT {f_id}, {f_name}, {f_pic}, {f_rem}, {f_cnt} FROM `{table}` LIMIT ? OFFSET ?"
                cursor.execute(sql, (limit, start_i + offset))
            else:
                cursor.execute(f"SELECT COUNT(*) FROM `{table}` WHERE CAST(`{m['category_field']}` AS TEXT) = ?", (str(category_val),))
                total_data = cursor.fetchone()[0]
                sql = f"SELECT {f_id}, {f_name}, {f_pic}, {f_rem}, {f_cnt} FROM `{table}` WHERE CAST(`{m['category_field']}` AS TEXT) = ? LIMIT ? OFFSET ?"
                cursor.execute(sql, (str(category_val), limit, offset))
            
            rows = cursor.fetchall()
            for row in rows:
                # 💎 直接获取数据库自带的备注字段内容 (HD高清、完结等)
                # 如果数据库里该字段为空，则显示为 "DB视频" 或 "正片"
                raw_rem = str(row[3]) if row[3] is not None and str(row[3]).strip() != "" else "DB视频"
                
                # 💎 直接使用自带信息，不进行分页字符串的拼接
                dynamic_remarks = raw_rem
                
                vod_list.append({
                    "vod_id": f"{db_key}#ID#{row[0]}",
                    "vod_name": str(row[1]),
                    "vod_pic": str(row[2]) if str(row[2]).startswith('http') else "",
                    "vod_remarks": dynamic_remarks, # 这样就会显示 "HD高清" 而不是统计信息
                    "vod_content": str(row[4]) 
                })
        except: pass
        finally: conn.close()
        return {"page": int(pg), "pagecount": int(pg)+1, "limit": limit, "list": vod_list}

    # ==========================================================================
    # 🧠 【4. 详情页 - 增强统计版】
    # ==========================================================================
    def detailContent(self, ids):
        mid_full = ids[0]
        db_key, _, real_id = mid_full.partition("#ID#")
        
        try:
            db_path = base64.b64decode(db_key).decode() if len(db_key) > 32 else db_key
        except:
            db_path = db_key
        
        db_info = self.databases.get(db_key, {})
        if not db_info and db_path in self.databases:
             db_info = self.databases[db_path]
        
        actual_path = db_info.get("path", db_path)
        conn = self._get_connection(actual_path)
        if not conn: return {"list": []}
        
        auto_info = self._get_auto_mapping(conn)
        main_cfg = db_info.get("tables", {}).get("main", {})
        table_name = main_cfg.get("table_name") or auto_info["table_name"]
        mapping = main_cfg.get("field_mapping") or auto_info["field_mapping"]

        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        id_col = mapping.get("vod_id") or "rowid"
        
        try:
            # 💎 【统计信息计算】
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            total_count = cursor.fetchone()[0]
            f_size_str = db_info.get("size_str", "未知")
            
            cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{id_col}` = ?", (real_id,))
            row = cursor.fetchone()
            if not row: return {"list": []}

            def get_val(m_key):
                col = mapping.get(m_key)
                if col and col in row.keys() and row[col] is not None:
                    return str(row[col])
                return ""

            raw_content = get_val("vod_content") or "暂无原始简介"
            
            # 💎 【缝合丰富简介统计】
            v_content = f"【原始简介】: {raw_content}\n"
            v_content += f"--------------------------\n"
            v_content += f"📊 数据统计: {total_count} 条有效数据\n"
            v_content += f"⚖️ 文件大小: {f_size_str}\n"
            v_content += f"✅ 索引位置: ID_{real_id}\n"
            v_content += f"⚡ 性能档位: {getattr(self, 'adaptive_tag', 'High-Speed SQLite')}\n"
            v_content += f"📍 物理路径: {actual_path}"

            play_url = get_val("vod_play_url")
            if not play_url: play_url = f"Play#{real_id}"

            vod = {
                "vod_id": mid_full,
                "vod_name": get_val("vod_name"),
                "vod_pic": get_val("vod_pic"),
                "vod_remarks": get_val("vod_remarks"),
                "vod_actor": get_val("vod_actor") or "未知",
                "vod_content": v_content, # 强制显示拼接后的丰富统计
                "vod_play_from": "DB数据库",
                "vod_play_url": play_url.replace('$$$高清', '#播放')
            }
            return {"list": [vod]}
        except: return {"list": []}
        finally: conn.close()

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0, 
            "url": id, 
            "header": {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; MIbox PRO Build/PI)"}
        }

    def searchContent(self, key, quick, pg="1"):
        return {"list": [], "page": pg}
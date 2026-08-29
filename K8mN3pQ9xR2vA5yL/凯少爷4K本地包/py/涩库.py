import sys
import sqlite3
import json
import os
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "Universal_DB_Spider"

    def init(self, extend=""):
        self._db_cache = {}
        self.databases = {}
        self._auto_scan_databases(["/storage/emulated/0/VodPlus/wwwroot/文件类[文]/db"])

        # 加载二级分类图标配置文件（作为备用）
        self.sub_icons = {}
        icon_config_path = "/storage/emulated/0/VodPlus/wwwroot/文件类[文]/db"
        if os.path.exists(icon_config_path):
            try:
                with open(icon_config_path, 'r', encoding='utf-8') as f:
                    self.sub_icons = json.load(f)
            except:
                pass

        # 跨库头像：从女优库.db 加载所有女优头像备用
        self.fallback_avatar_map = {}
        actress_db_path = "/storage/emulated/0/影视/头像/女优库.db"
        if os.path.exists(actress_db_path):
            try:
                conn = sqlite3.connect(actress_db_path)
                auto_info = self._get_auto_mapping(conn)
                if auto_info:
                    cursor = conn.cursor()
                    table = auto_info["table_name"]
                    mapping = auto_info["field_mapping"]
                    # 尝试找到女优名字段和头像字段
                    name_col = None
                    for candidate in ["cate_name", "type_name", "vod_actor"]:
                        if mapping.get(candidate) and mapping[candidate] in [r[1] for r in conn.execute(f"PRAGMA table_info(`{table}`)").fetchall()]:
                            name_col = mapping[candidate]
                            break
                    avatar_col = None
                    for candidate in ["actress_avatar", "avatar", "logo"]:
                        if mapping.get(candidate) and mapping[candidate] in [r[1] for r in conn.execute(f"PRAGMA table_info(`{table}`)").fetchall()]:
                            avatar_col = mapping[candidate]
                            break
                    if name_col and avatar_col:
                        cursor.execute(f"SELECT `{name_col}`, `{avatar_col}` FROM `{table}` WHERE `{avatar_col}` IS NOT NULL AND `{avatar_col}` != ''")
                        for name, avatar in cursor.fetchall():
                            if name and avatar:
                                if name not in self.fallback_avatar_map:
                                    self.fallback_avatar_map[name] = avatar
                conn.close()
            except:
                pass  # 静默失败

    def _auto_scan_databases(self, dirs):
        for d in dirs:
            if not os.path.exists(d): continue
            for file in os.listdir(d):
                if file.endswith(".db"):
                    full_path = os.path.join(d, file)
                    db_key = f"auto_{file}"
                    if db_key not in self.databases:
                        self.databases[db_key] = {"name": file, "path": full_path, "valid": 1}

    def _get_connection(self, db_key):
        db_info = self.databases.get(db_key)
        if not db_info: return None
        db_path = db_info.get("path")
        if not db_path or not os.path.exists(db_path): return None
        try:
            return sqlite3.connect(db_path)
        except: return None

    def _get_auto_mapping(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            target_table = next((t for t in ["videos", "vod_unified_data", "cj", "vod", "data", "list", "video_detail"] if t in tables), tables[0] if tables else None)
            if not target_table: return None
            cursor.execute(f"PRAGMA table_info(`{target_table}`)")
            cols = [str(r[1]) for r in cursor.fetchall()]

            mapping = {}
            field_candidates = {
                "vod_id": ["id", "vod_id", "uuid", "guid", "vid"],
                "vod_name": ["name", "vod_name", "title", "subject", "display_name"],
                "vod_pic": ["image", "vod_pic", "pic", "pic_url", "thumbnail", "img", "cover"],
                "vod_play_url": ["play_url", "vod_play_url", "url", "link", "m3u8_url"],
                "vod_remarks": ["vod_remarks", "remarks", "note", "desc"],
                "category_field": ["type_name", "category_id", "class_name", "cate_name", "actress_id", "tag", "type"],
                "vod_actor": ["vod_actor", "actor", "star", "actress", "artist", "performer"],
                "vod_content": ["vod_content", "description", "summary", "intro", "detail", "content"],
                "vod_pubdate": ["vod_pubdate", "pubdate", "release_date", "date"],
                "vod_area": ["vod_area", "area", "region", "country"],
                "vod_year": ["vod_year", "year"],
                "vod_tags": ["vod_tags", "tags", "keywords", "label"],
                "vod_play_from": ["vod_play_from", "play_from", "source"],
                "actress_avatar": ["actress_avatar", "avatar", "logo", "LOOG"],
                "cate_name": ["cate_name", "type_name"]
            }

            for target_field, candidates in field_candidates.items():
                matches = [cand for cand in candidates if cand in cols]
                if not matches:
                    mapping[target_field] = None
                    continue
                if len(matches) == 1:
                    mapping[target_field] = matches[0]
                    continue
                best_match = None
                for match in matches:
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM `{target_table}` WHERE `{match}` IS NOT NULL AND `{match}` != "" LIMIT 1')
                        if cursor.fetchone()[0] > 0:
                            best_match = match
                            break
                    except: continue
                mapping[target_field] = best_match if best_match else matches[0]

            return {
                "table_name": target_table,
                "field_mapping": mapping
            }
        except: return None

    def homeContent(self, filter):
        classes = []
        icon_url = "https://gitcode.com/gcw_OAaqxWb5/tu/releases/download/%E5%9B%BE%E7%89%87/%E5%90%88%E9%9B%86.png"
        for db_key, db_info in self.databases.items():
            if db_info.get("valid") != 0 and not db_info.get("hide"):
                db_path = db_info.get("path", "")
                if os.path.exists(db_path):
                    conn = self._get_connection(db_key)
                    if conn:
                        auto_info = self._get_auto_mapping(conn)
                        if auto_info:
                            try:
                                cursor = conn.cursor()
                                cursor.execute(f"SELECT COUNT(*) FROM `{auto_info['table_name']}`")
                                cursor.fetchone()
                            except: pass
                        conn.close()
                    raw_name = db_info.get('name', db_key)
                    clean_name = os.path.splitext(raw_name)[0]
                    classes.append({
                        "type_id": db_key,
                        "type_name": clean_name,
                        "type_pic": icon_url,
                        "pic": icon_url,
                        "icon": icon_url,
                        "vod_pic": icon_url
                    })
        return {"class": classes}

    def categoryContent(self, tid, pg, filter, extend):
        parts = tid.split('$')
        db_key = parts[0]
        curr_path = parts[1] if len(parts) > 1 else ""

        cache_key = f"tree_{db_key}"
        if cache_key not in self._db_cache:
            conn = self._get_connection(db_key)
            if not conn: return {"list": []}

            auto_info = self._get_auto_mapping(conn)
            if not auto_info:
                conn.close()
                return {"list": []}
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info(`{auto_info['table_name']}`)")
            all_cols = [str(r[1]) for r in cursor.fetchall()]
            filter_field = "type_name" if "type_name" in all_cols else auto_info["field_mapping"]["category_field"]

            cursor.execute(f"SELECT `{filter_field}`, COUNT(*) FROM `{auto_info['table_name']}` WHERE `{filter_field}` IS NOT NULL GROUP BY `{filter_field}`")
            raw_data = cursor.fetchall()
            type_counts = {str(row[0]): row[1] for row in raw_data}

            # 当前库自己的头像映射（从 actres_avatar 字段读取）
            avatar_map = {}
            if "actress_avatar" in all_cols:
                try:
                    cursor.execute(
                        f"SELECT `{filter_field}`, `actress_avatar` FROM `{auto_info['table_name']}` "
                        "WHERE `actress_avatar` IS NOT NULL AND `actress_avatar` != ''"
                    )
                    for row in cursor.fetchall():
                        cat_val = str(row[0])
                        avatar_url = row[1]
                        if cat_val not in avatar_map:
                            avatar_map[cat_val] = avatar_url
                except: pass

            self._db_cache[cache_key] = {
                "types": list(type_counts.keys()),
                "counts": type_counts,
                "field": filter_field,
                "table": auto_info['table_name'],
                "mapping": auto_info['field_mapping'],
                "avatar_map": avatar_map
            }
            conn.close()

        db_data = self._db_cache[cache_key]
        all_vals = db_data["types"]
        all_counts = db_data["counts"]
        avatar_map = db_data.get("avatar_map", {})

        sub_dirs_info = {}
        for val in all_vals:
            count = all_counts.get(val, 0)
            if curr_path == "":
                d = val.split('/')[0]
                sub_dirs_info[d] = sub_dirs_info.get(d, 0) + count
            elif val.startswith(curr_path + "/"):
                suffix = val[len(curr_path):].lstrip('/')
                if suffix:
                    d = f"{curr_path}/{suffix.split('/')[0]}"
                    sub_dirs_info[d] = sub_dirs_info.get(d, 0) + count

        limit = 20
        offset = (int(pg) - 1) * limit

        if not sub_dirs_info:
            conn = self._get_connection(db_key)
            return self._fetch_video_list(conn, db_key, db_data["table"], db_data["mapping"],
                                          db_data["field"], curr_path if curr_path else None, pg, limit, offset)

        if len(sub_dirs_info) == 1:
            single_dir = list(sub_dirs_info.keys())[0]
            has_deeper = any(v.startswith(single_dir + "/") for v in all_vals)
            if not has_deeper:
                conn = self._get_connection(db_key)
                return self._fetch_video_list(conn, db_key, db_data["table"], db_data["mapping"],
                                              db_data["field"], single_dir, pg, limit, offset)

        def sort_key(d):
            # 有头像的优先（数据库、跨库、配置文件任一存在均算有头像）
            has_avatar = 0 if (avatar_map.get(d) or self.fallback_avatar_map.get(d) or self.sub_icons.get(d)) else 1
            return (has_avatar, -sub_dirs_info[d], d)

        sorted_dirs = sorted(list(sub_dirs_info.keys()), key=sort_key)
        paged_dirs = sorted_dirs[offset : offset + limit]

        vod_list = []
        for d in paged_dirs:
            display_name = d.split('/')[-1]
            num = sub_dirs_info[d]

            # 图标优先级：当前库头像 > 跨库头像 > 配置文件 > 默认合集图标
            pic = avatar_map.get(d)
            if not pic:
                pic = self.fallback_avatar_map.get(d)
            if not pic:
                # 配置文件支持完整路径或仅子分类名
                full_key = f"{curr_path}/{d}" if curr_path else d
                pic = self.sub_icons.get(full_key) or self.sub_icons.get(d)
            if not pic:
                pic = "https://gitcode.com/gcw_OAaqxWb5/tu/releases/download/%E5%9B%BE%E7%89%87/%E5%90%88%E9%9B%86.png"

            vod_list.append({
                "vod_id": f"{db_key}${d}",
                "vod_name": f"{display_name} ({num})",
                "vod_pic": pic,
                "vod_tag": "folder",
                "style": {"type": "rect", "ratio": 1.8}
            })

        return {"page": int(pg), "pagecount": int(pg) + 1, "limit": limit, "list": vod_list}

    def _fetch_video_list(self, conn, db_key, table_name, mapping, filter_field, category_val, pg, limit, offset):
        cursor = conn.cursor()
        vod_list = []
        f_id = mapping.get("vod_id") or "rowid"
        f_name = mapping.get("vod_name") or "rowid"
        f_pic = mapping.get("vod_pic") or "''"
        f_rem = mapping.get("vod_remarks") or "''"

        try:
            if category_val is not None:
                sql = f"SELECT `{f_id}`, `{f_name}`, `{f_pic}`, `{f_rem}` FROM `{table_name}` WHERE `{filter_field}` = ? LIMIT ? OFFSET ?"
                cursor.execute(sql, (category_val, limit, offset))
            else:
                sql = f"SELECT `{f_id}`, `{f_name}`, `{f_pic}`, `{f_rem}` FROM `{table_name}` LIMIT ? OFFSET ?"
                cursor.execute(sql, (limit, offset))

            for row in cursor.fetchall():
                pic = str(row[2]) if row[2] else ""
                if not pic:
                    pic = "https://img.icons8.com/color/512/movie.png"
                vod_list.append({
                    "vod_id": f"{db_key}#ID#{row[0]}",
                    "vod_name": str(row[1]),
                    "vod_pic": pic,
                    "vod_remarks": str(row[3]) if len(row) > 3 else ""
                })
        except:
            pass
        finally:
            conn.close()

        return {"page": int(pg), "pagecount": int(pg) + 1, "limit": limit, "list": vod_list}

    def detailContent(self, ids):
        mid_full = ids[0]
        db_key, _, real_id = mid_full.partition("#ID#")
        conn = self._get_connection(db_key)
        if not conn: return {"list": []}

        auto_info = self._get_auto_mapping(conn)
        if not auto_info:
            conn.close()
            return {"list": []}
        table_name = auto_info["table_name"]
        mapping = auto_info["field_mapping"]

        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        id_col = mapping.get("vod_id") or "rowid"

        cursor.execute(f"SELECT * FROM `{table_name}` WHERE `{id_col}` = ?", (real_id,))
        row = cursor.fetchone()
        if not row: 
            conn.close()
            return {"list": []}

        def get_val(m_key):
            real_col = mapping.get(m_key)
            return str(row[real_col]) if (real_col and real_col in row.keys() and row[real_col] is not None) else ""

        vod_year = get_val("vod_year")
        vod_content = get_val("vod_content")
        if not vod_content:
            vod_content = get_val("vod_remarks")

        vod = {
            "vod_id": mid_full,
            "vod_name": get_val("vod_name"),
            "vod_pic": get_val("vod_pic"),
            "vod_actor": get_val("vod_actor") or get_val("category_field"),
            "vod_director": "",
            "vod_remarks": get_val("vod_remarks"),
            "vod_pubdate": get_val("vod_pubdate"),
            "vod_area": get_val("vod_area"),
            "vod_year": vod_year,
            "vod_tags": get_val("vod_tags"),
            "vod_content": vod_content,
            "vod_play_from": get_val("vod_play_from") or "自动识别",
            "vod_play_url": get_val("vod_play_url").split('$$$')[-1],
            "type_name": get_val("category_field") or get_val("type_name")
        }
        conn.close()
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        playurl = id.split("|")[0]
        return {"parse": 0, "url": playurl, "header": {"User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; MIbox PRO Build/PI)"}}

    def searchContent(self, key, quick, pg="1"):
        search_list = []
        limit = 20
        for db_key, db_info in self.databases.items():
            if db_info.get("valid") == 0: continue
            conn = self._get_connection(db_key)
            if not conn: continue
            try:
                auto_info = self._get_auto_mapping(conn)
                if not auto_info: 
                    conn.close()
                    continue
                table_name = auto_info["table_name"]
                mapping = auto_info["field_mapping"]
                search_fields = [mapping.get("vod_name")] if mapping.get("vod_name") else []
                if not search_fields:
                    conn.close()
                    continue
                cursor = conn.cursor()
                where_clauses = [f"`{field}` LIKE ?" for field in search_fields]
                sql_where = " OR ".join(where_clauses)
                f_id = mapping.get("vod_id") or "rowid"
                f_name = mapping.get("vod_name")
                f_pic = mapping.get("vod_pic") or "''"
                f_rem = mapping.get("vod_remarks") or "''"

                sql = f"SELECT `{f_id}`, `{f_name}`, `{f_pic}`, `{f_rem}` FROM `{table_name}` WHERE {sql_where} LIMIT {limit}"
                params = [f"%{key}%"] * len(search_fields)
                cursor.execute(sql, params)
                for row in cursor.fetchall():
                    pic = str(row[2]) if row[2] else ""
                    if not pic:
                        pic = "https://img.icons8.com/color/512/movie.png"
                    search_list.append({
                        "vod_id": f"{db_key}#ID#{row[0]}",
                        "vod_name": f"[{db_info.get('name', db_key)}] {row[1]}",
                        "vod_pic": pic,
                        "vod_remarks": str(row[3]) if len(row) > 3 else ""
                    })
            except:
                pass
            finally:
                conn.close()
        return {"list": search_list, "page": pg}
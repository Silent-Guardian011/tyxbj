import sys
import sqlite3
import json
import os
import base64
import time
import re
from base.spider import Spider


class Spider(Spider):
    def getName(self):
        return "Universal_DB_Spider"

    SCAN_DIR_LIST = [
        "bh", "tvbox", "bhh", "tvbox/lz", "lz",
        "VodPlus", "peekpili/php-scripts", "纯福利", "江湖"
    ]

    MIN_DB_SIZE = 3 * 1024 * 1024
    DB_LOGO = "https://img.icons8.com/color/94/folder-invoices.png"
    CHUNK_SIZE = 500
    PAGE_LIMIT = 40
    COUNT_THRESHOLD = 20
    SCAN_CACHE_PATH = "/data/local/tmp/db_scan_cache.json"
    SCAN_CACHE_TTL = 300

    def init(self, extend=""):
        self.inited = True
        self.databases = {}
        self.scan_roots = ["/storage/emulated/0"]
        self.auto_mapping_cache = {}
        self.row_count_cache = {}

        try:
            if os.path.exists("/storage"):
                for s in os.listdir("/storage"):
                    if s not in [
                        "self", "emulated",
                        "knox", "sdcard0", "runtime"
                    ]:
                        full_s = os.path.join("/storage", s)
                        if os.path.isdir(full_s):
                            self.scan_roots.append(full_s)
        except:
            pass

        if not self._load_scan_cache():
            self._differential_scan()
            self._save_scan_cache()

    def _load_scan_cache(self):
        try:
            if not os.path.exists(self.SCAN_CACHE_PATH):
                return False
            mtime = os.path.getmtime(self.SCAN_CACHE_PATH)
            if time.time() - mtime > self.SCAN_CACHE_TTL:
                return False
            with open(self.SCAN_CACHE_PATH, 'r') as f:
                cached = json.load(f)
            valid_items = {}
            for key, info in cached.items():
                p = info.get("path", "")
                if os.path.exists(p):
                    sz = os.path.getsize(p)
                    if sz >= self.MIN_DB_SIZE:
                        valid_items[key] = info
            if valid_items:
                self.databases = valid_items
                return True
        except:
            pass
        return False

    def _save_scan_cache(self):
        try:
            cache_data = {}
            for key, info in self.databases.items():
                cache_data[key] = {
                    "name": info.get("name", ""),
                    "path": info.get("path", ""),
                    "size_str": info.get("size_str", ""),
                    "valid": info.get("valid", 1)
                }
            os.makedirs(
                os.path.dirname(self.SCAN_CACHE_PATH),
                exist_ok=True
            )
            with open(self.SCAN_CACHE_PATH, 'w') as f:
                json.dump(cache_data, f)
        except:
            pass

    def _format_size(self, size_bytes):
        if size_bytes < 1048576:
            return f"{int(size_bytes / 1024)}K"
        return f"{size_bytes / 1048576:.1f}M"

    def _differential_scan(self):
        temp_list = []
        for root_p in self.scan_roots:
            is_ext = not root_p.startswith("/storage/emulated/0")
            star = "☆" if is_ext else ""
            for target in self.SCAN_DIR_LIST:
                base_p = os.path.join(root_p, target)
                if not os.path.isdir(base_p):
                    continue
                for root, dirs, files in os.walk(base_p):
                    for file in files:
                        if not file.lower().endswith(".db"):
                            continue
                        f_path = os.path.join(root, file)
                        try:
                            sz_raw = os.path.getsize(f_path)
                            if sz_raw < self.MIN_DB_SIZE:
                                continue
                            rel_path = (
                                f_path
                                .replace("/storage/emulated/0/", "")
                                .replace(root_p, "")
                            )
                            display_name = (
                                f"📁{rel_path} "
                                f"({self._format_size(sz_raw)}){star}"
                            )
                            db_key = base64.b64encode(
                                f_path.encode()
                            ).decode()
                            temp_list.append({
                                "key": db_key,
                                "name": display_name,
                                "path": f_path,
                                "is_ext": is_ext,
                                "size_bytes": sz_raw
                            })
                        except:
                            continue
        temp_list.sort(key=lambda x: (x["is_ext"], x["size_bytes"]))
        for item in temp_list:
            self.databases[item["key"]] = {
                "name": item["name"],
                "path": item["path"],
                "size_str": self._format_size(item["size_bytes"]),
                "valid": 1
            }

    def _get_connection(self, db_path):
        if not os.path.exists(db_path):
            return None
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA cache_size=-8192")
            cur.execute("PRAGMA mmap_size=268435456")
            cur.execute("PRAGMA temp_store=MEMORY")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA page_size=4096")
            return conn
        except:
            return None

    def _get_auto_mapping(self, conn, db_key=None):
        cache_key = db_key or id(conn)
        if cache_key in self.auto_mapping_cache:
            return self.auto_mapping_cache[cache_key]

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'"
            )
            tables = [row[0] for row in cursor.fetchall()]

            priority_tables = [
                "videos", "vod_unified_data",
                "cj", "vod", "data", "video_detail"
            ]
            target_table = next(
                (t for t in priority_tables if t in tables),
                tables[0] if tables else None
            )
            if not target_table:
                return None

            cat_tables = [
                "categories", "type", "vod_type", "classes"
            ]
            target_cat_table = next(
                (t for t in cat_tables if t in tables), None
            )

            cursor.execute(
                f"PRAGMA table_info(`{target_table}`)"
            )
            cols = [str(r[1]) for r in cursor.fetchall()]

            mapping = {}
            field_candidates = {
                "vod_id": [
                    "id", "vod_id", "uuid", "aid", "rowid"
                ],
                "vod_name": [
                    "name", "vod_name", "title", "subject"
                ],
                "vod_pic": [
                    "image", "vod_pic", "pic",
                    "thumbnail", "cover"
                ],
                "vod_play_url": [
                    "play_url", "vod_play_url", "url", "link"
                ],
                "vod_remarks": [
                    "remarks", "vod_remarks", "quality", "note"
                ],
                "vod_content": [
                    "content", "vod_content",
                    "description", "summary"
                ],
                "category_field": [
                    "type_id", "category_id", "type_name",
                    "class_id", "actress_id"
                ]
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
                    cursor.execute(
                        f'SELECT `{match}` '
                        f'FROM `{target_table}` '
                        f'WHERE `{match}` IS NOT NULL '
                        f'AND `{match}` != "" LIMIT 10'
                    )
                    results = cursor.fetchall()
                    if not results:
                        continue
                    if k == "category_field":
                        distinct_vals = set(
                            [str(r[0]) for r in results]
                        )
                        if (
                            len(distinct_vals) <= 1
                            and len(results) > 1
                        ):
                            score -= 50
                        if target_cat_table:
                            score += 30
                    score += (
                        20 if match == candidates[0] else 5
                    )
                    if score > max_score:
                        max_score = score
                        best_match = match
                mapping[k] = best_match

            cat_id_field = None
            cat_name_field = None
            if target_cat_table:
                try:
                    cursor.execute(
                        f"PRAGMA table_info("
                        f"`{target_cat_table}`)"
                    )
                    cat_cols = [
                        str(r[1]) for r in cursor.fetchall()
                    ]
                    for c in [
                        "name", "type_name", "class_name",
                        "category_name", "title"
                    ]:
                        if c in cat_cols:
                            cat_name_field = c
                            break
                    data_cat = mapping.get("category_field")
                    if data_cat and data_cat in cat_cols:
                        cat_id_field = data_cat
                    else:
                        for c in [
                            "id", "type_id",
                            "category_id", "class_id"
                        ]:
                            if (
                                c in cat_cols
                                and c != cat_name_field
                            ):
                                cat_id_field = c
                                break
                        if not cat_id_field:
                            for c in cat_cols:
                                if (
                                    c.endswith("_id")
                                    and c != cat_name_field
                                ):
                                    cat_id_field = c
                                    break
                except:
                    pass

            result = {
                "table_name": target_table,
                "cat_table_name": target_cat_table,
                "cat_id_field": cat_id_field,
                "cat_name_field": cat_name_field,
                "field_mapping": mapping
            }
            if db_key:
                self.auto_mapping_cache[cache_key] = result
            return result
        except:
            return None

    def _cached_row_count(
        self, cursor, table,
        where_col=None, where_val=None
    ):
        cache_key = f"{table}_{where_col}_{where_val}"
        if cache_key in self.row_count_cache:
            return self.row_count_cache[cache_key]
        try:
            if where_col and where_val is not None:
                cursor.execute(
                    f"SELECT COUNT(*) FROM `{table}` "
                    f"WHERE CAST(`{where_col}` AS TEXT) = ?",
                    (str(where_val),)
                )
            else:
                cursor.execute(
                    f"SELECT COUNT(*) FROM `{table}`"
                )
            count = cursor.fetchone()[0]
            self.row_count_cache[cache_key] = count
            return count
        except:
            return 0

    def _get_db_display_name(self, db_path):
        try:
            basename = os.path.basename(db_path)
            name_no_ext = os.path.splitext(basename)[0]
            if name_no_ext:
                return name_no_ext
            parent = os.path.basename(
                os.path.dirname(db_path)
            )
            if parent:
                return parent
        except:
            pass
        return "全部数据"

    def _resolve_pic(self, raw_pic):
        if (
            raw_pic
            and str(raw_pic).strip()
            and str(raw_pic).startswith("http")
        ):
            return str(raw_pic).strip()
        return self.DB_LOGO

    # ==========================================================================
    # ★ 清洗名称 ★
    # ==========================================================================
    def _clean_name(self, raw_name):
        s = str(raw_name).strip()
        if not s:
            return s

        # 1) 去掉 "目录" 前缀
        s = re.sub(r'^目录\s*[:：\-\s]*', '', s)

        # 2) 去掉开头的 "第X页/集/章"
        s = re.sub(r'^第\s*\d+\s*[页集章节回]\s*', '', s)

        # 3) 去掉开头的纯数字段
        s = re.sub(r'^\d+[\s\-\._/]*', '', s)

        # 4) 去掉开头的方括号/圆括号标签
        s = re.sub(r'^$$[^$$]*\]\s*', '', s)
        s = re.sub(r'^$$[^)]*$$\s*', '', s)

        # 5) ★ 去掉所有括号及括号里的内容 ★
        #    匹配 () [] 【】 《》 内的任意内容
        s = re.sub(r'$$[^)]*$$', '', s)
        s = re.sub(r'$$[^$$]*\]', '', s)
        s = re.sub(r'【[^】]*】', '', s)
        s = re.sub(r'《[^》]*》', '', s)

        # 6) 去掉开头的英文+数字+符号前缀
        if re.search(r'[\u4e00-\u9fff]', s):
            s = re.sub(
                r'^[a-zA-Z0-9\-_\.~!@#$%^&*()=+$${}|;:,<>?/\\ ]+',
                '', s
            )

        # 7) 清理残留的开头标点
        s = re.sub(r'^[\s\-_—–·.。、,，:：;；]+', '', s)

        return s.strip() if s.strip() else str(raw_name).strip()

    # ==========================================================================
    # 辅助：直接渲染数据列表
    # ==========================================================================
    def _render_flat_data(
        self, conn, auto, db_key,
        table, category_val=None,
        pg="1"
    ):
        m = auto["field_mapping"]
        cursor = conn.cursor()
        vod_list = []
        limit = self.PAGE_LIMIT
        pg_int = int(pg)
        offset = (pg_int - 1) * limit

        f_id = m.get("vod_id") or "rowid"
        f_name = m.get("vod_name") or "rowid"
        f_pic = m.get("vod_pic") or "''"
        f_rem = m.get("vod_remarks") or "''"
        f_cnt = m.get("vod_content") or "''"
        cat_field = m.get("category_field")

        total_data = 0

        try:
            if category_val is not None and cat_field:
                total_data = self._cached_row_count(
                    cursor, table, cat_field, category_val
                )
                sql = (
                    f"SELECT {f_id}, {f_name}, "
                    f"{f_pic}, {f_rem}, {f_cnt} "
                    f"FROM `{table}` "
                    f"WHERE CAST(`{cat_field}` AS TEXT) "
                    f"= ? LIMIT ? OFFSET ?"
                )
                cursor.execute(
                    sql,
                    (str(category_val), limit, offset)
                )
            else:
                total_data = self._cached_row_count(
                    cursor, table
                )
                sql = (
                    f"SELECT {f_id}, {f_name}, "
                    f"{f_pic}, {f_rem}, {f_cnt} "
                    f"FROM `{table}` "
                    f"LIMIT ? OFFSET ?"
                )
                cursor.execute(sql, (limit, offset))

            rows = cursor.fetchall()
            for row in rows:
                raw_rem = (
                    str(row[3])
                    if row[3] is not None
                    and str(row[3]).strip() != ""
                    else ""
                )
                vod_list.append({
                    "vod_id": f"{db_key}#ID#{row[0]}",
                    "vod_name": self._clean_name(row[1]),
                    "vod_pic": self._resolve_pic(row[2]),
                    "vod_remarks": raw_rem,
                    "vod_content": (
                        str(row[4])
                        if row[4] is not None else ""
                    )
                })
        except:
            pass

        pagecount = max(
            1, (total_data + limit - 1) // limit
        )
        return {
            "page": pg_int,
            "pagecount": pagecount,
            "limit": limit,
            "list": vod_list
        }

    # ==========================================================================
    # homeContent
    # ==========================================================================
    def homeContent(self, filter):
        classes = []
        for key, info in self.databases.items():
            classes.append({
                "type_id": key, "type_name": info["name"]
            })
        return {"class": classes}

    # ==========================================================================
    # categoryContent
    # ==========================================================================
    def categoryContent(self, tid, pg, filter, extend):
        parts = tid.split('$')
        db_key = parts[0]
        category_val = parts[1] if len(parts) > 1 else None

        try:
            db_path = (
                base64.b64decode(db_key).decode()
                if len(db_key) > 32 else db_key
            )
        except:
            db_path = db_key
        if db_path in self.databases:
            db_path = self.databases[db_path].get(
                "path", db_path
            )

        conn = self._get_connection(db_path)
        if not conn:
            return {"list": []}

        auto = self._get_auto_mapping(conn, db_key)
        if not auto:
            conn.close()
            return {"list": []}

        table = auto["table_name"]
        cat_table = auto["cat_table_name"]
        cat_id_field = auto.get("cat_id_field")
        cat_name_field = auto.get("cat_name_field")
        m = auto["field_mapping"]

        if category_val is not None:
            result = self._render_flat_data(
                conn, auto, db_key,
                table, category_val, pg
            )
            conn.close()
            return result

        all_cats = []

        if cat_table and cat_name_field:
            try:
                if cat_id_field:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"SELECT `{cat_id_field}`, "
                        f"`{cat_name_field}` "
                        f"FROM `{cat_table}`"
                    )
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        f"SELECT `rowid`, "
                        f"`{cat_name_field}` "
                        f"FROM `{cat_table}`"
                    )
                all_cats = cursor.fetchall()

                if all_cats and m.get("category_field"):
                    cursor.execute(
                        f"SELECT COUNT(*) FROM `{table}` "
                        f"WHERE CAST("
                        f"`{m['category_field']}` "
                        f"AS TEXT) = ?",
                        (str(all_cats[0][0]),)
                    )
                    if cursor.fetchone()[0] == 0:
                        all_cats = []
            except:
                pass

        if not all_cats and m.get("category_field"):
            try:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT DISTINCT "
                    f"CAST(`{m['category_field']}` "
                    f"AS TEXT), "
                    f"`{m['category_field']}` "
                    f"FROM `{table}`"
                )
                all_cats = cursor.fetchall()
            except:
                pass

        if len(all_cats) <= 1:
            result = self._render_flat_data(
                conn, auto, db_key,
                table, category_val=None, pg=pg
            )
            conn.close()
            return result

        vod_list = []
        cat_field = m.get("category_field")
        do_count = (
            len(all_cats) <= self.COUNT_THRESHOLD
        )
        for row in all_cats:
            label = self._clean_name(row[1])
            if do_count and cat_field:
                cnt = self._cached_row_count(
                    cursor, table, cat_field, row[0]
                )
                # ★ 不再拼接数量到分类名上 ★
            vod_list.append({
                "vod_id": f"{db_key}${row[0]}",
                "vod_name": label,
                "vod_pic": self.DB_LOGO,
                "vod_tag": "folder",
                "vod_remarks": ""
            })
        conn.close()
        return {
            "page": 1, "pagecount": 1,
            "limit": 999,
            "list": vod_list
        }

    # ==========================================================================
    # 详情页
    # ==========================================================================
    def detailContent(self, ids):
        mid_full = ids[0]
        db_key, _, real_id = mid_full.partition("#ID#")

        try:
            db_path = (
                base64.b64decode(db_key).decode()
                if len(db_key) > 32 else db_key
            )
        except:
            db_path = db_key

        db_info = self.databases.get(db_key, {})
        if not db_info and db_path in self.databases:
            db_info = self.databases[db_path]

        actual_path = db_info.get("path", db_path)
        conn = self._get_connection(actual_path)
        if not conn:
            return {"list": []}

        auto_info = self._get_auto_mapping(conn, db_key)
        if not auto_info:
            conn.close()
            return {"list": []}

        table_name = auto_info["table_name"]
        mapping = auto_info["field_mapping"]

        cursor = conn.cursor()
        id_col = mapping.get("vod_id") or "rowid"

        try:
            total_count = self._cached_row_count(
                cursor, table_name
            )
            f_size_str = db_info.get("size_str", "未知")

            cursor.execute(
                f"SELECT * FROM `{table_name}` "
                f"WHERE `{id_col}` = ?",
                (real_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {"list": []}

            def get_val(m_key):
                col = mapping.get(m_key)
                if (
                    col and col in row.keys()
                    and row[col] is not None
                ):
                    return str(row[col])
                return ""

            raw_content = (
                get_val("vod_content") or "暂无原始简介"
            )

            v_content = (
                f"【原始简介】: {raw_content}\n"
                f"--------------------------\n"
                f"📊 数据统计: {total_count} 条有效数据\n"
                f"⚖️ 文件大小: {f_size_str}\n"
                f"✅ 索引位置: ID_{real_id}\n"
                f"⚡ 性能档位: High-Speed SQLite (WAL)\n"
                f"📍 物理路径: {actual_path}"
            )

            play_url = get_val("vod_play_url")
            if not play_url:
                play_url = f"Play#{real_id}"

            vod = {
                "vod_id": mid_full,
                "vod_name": self._clean_name(
                    get_val("vod_name")
                ),
                "vod_pic": self._resolve_pic(
                    get_val("vod_pic")
                ),
                "vod_remarks": get_val("vod_remarks"),
                "vod_actor": (
                    get_val("vod_actor") or "未知"
                ),
                "vod_content": v_content,
                "vod_play_from": "DB数据库",
                "vod_play_url": play_url.replace(
                    '$$$高清', '#播放'
                )
            }
            return {"list": [vod]}
        except:
            return {"list": []}
        finally:
            conn.close()

    def playerContent(self, flag, id, vipFlags):
        return {
            "parse": 0,
            "url": id,
            "header": {
                "User-Agent": (
                    "Dalvik/2.1.0 (Linux; U; Android 9; "
                    "MIbox PRO Build/PI)"
                )
            }
        }

    def searchContent(self, key, quick, pg="1"):
        return {"list": [], "page": pg}

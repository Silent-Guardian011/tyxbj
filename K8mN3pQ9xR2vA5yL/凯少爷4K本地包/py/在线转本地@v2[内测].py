# -*- coding: utf-8 -*-
# @version v3.0 - 浅色现代风 + 日志面板（修复按钮文字比较错误）
# @author 陆小凤 (最终版)

import base64
import copy
import hashlib
import json
import os
import queue
import re
import shutil
import threading
import time
import traceback
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from base.spider import Spider as BaseSpider

DEFAULT_USER_AGENT = 'okhttp/4.12.0'
DEFAULT_EXTERNAL_API_URL = "https://xn--v4q818bf34b.cc/helper/api.php"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
CACHE_DIR = os.path.join(SCRIPT_DIR, 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# 持久化配置路径（将根据应用缓存目录动态设置）
PERSISTENT_CONFIG_PATH = None

def _get_app_cache_dir():
    """通过反射获取当前应用的缓存目录，用于存放持久化配置"""
    try:
        from java import jclass
        ActivityThread = jclass("android.app.ActivityThread")
        at = ActivityThread.currentActivityThread()
        context = at.getApplication()
        cache_dir = context.getCacheDir().getAbsolutePath()
        return cache_dir
    except Exception:
        # 回退到外部存储
        return "/storage/emulated/0/.local_source_manager"

# 初始化持久化路径
_cache_root = _get_app_cache_dir()
os.makedirs(_cache_root, exist_ok=True)
PERSISTENT_CONFIG_PATH = os.path.join(_cache_root, "persistent_config.json")

def _decode_bytes(raw):
    if not raw:
        return ''
    if raw[:3] == b'\xef\xbb\xbf':
        return raw.decode('utf-8-sig', errors='replace')
    for enc in ('utf-8', 'gb18030', 'big5'):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode('utf-8', errors='replace')

def _read_text_file(path):
    with open(path, 'rb') as f:
        return _decode_bytes(f.read())

_COMMON_USER_DIRS = [
    '/storage/emulated/0',
    '/sdcard',
    '/storage/sdcard0',
    '/storage/emulated/0/TVBox',
    '/storage/emulated/0/影视仓',
    '/storage/emulated/0/影视TV',
    '/storage/emulated/0/Download',
    '/storage/emulated/0/Documents',
    '/data/data',
    '/storage',
]

_FS_SEARCH_ROOTS = [
    '/storage/emulated/0',
    '/sdcard',
    '/storage/sdcard0',
    '/storage',
]

_FS_SKIP_DIRS = {
    'Android', 'DCIM', 'Pictures', 'Music', 'Movies',
    'WhatsApp', 'tencent', 'Telegram', '.cache', 'cache',
    'Download', 'Documents', 'Ringtones', 'Alarms', 'Notifications',
    'Podcasts', 'Audiobooks',
}

GITHUB_PROXY = "https://gh-proxy.com/"

DOWNLOAD_EXTS = {
    '.js', '.py', '.jar', '.json', '.txt', '.m3u', '.m3u8',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.css', '.html', '.htm', '.xml', '.zip', '.mp4', '.ts',
    '.woff', '.woff2', '.ttf', '.eot', '.svg',
}
SKIP_EXTS = {'.php', '.asp', '.aspx', '.jsp'}
SKIP_PATTERNS = [
    r'/api\.php/provide/vod',
    r'/api\.php/app/',
    r'provide/vod',
    r'\?url=',
    r'\{name\}',
    r'\{date\}',
    r'\{episode\}',
    r'proxy://',
]

BOOL_MAP = {'是': True, '否': False, '下载': True, '不下载': False,
            'true': True, 'false': False, '1': True, '0': False, True: True, False: False}

# ========================= 解密模块 =========================
_HAS_AES = False
_AES_MODE = None
try:
    from Crypto.Cipher import AES as _AES_IMPL
    _AES_MODE = 'pycryptodome'
    _HAS_AES = True
except ImportError:
    try:
        import pyaes as _AES_IMPL
        _AES_MODE = 'pyaes'
        _HAS_AES = True
    except ImportError:
        pass

def _strip_pkcs7(d):
    if d:
        p = d[-1]
        if 0 < p <= 16 and d[-p:] == bytes([p]) * p:
            return d[:-p]
    return d

def _contains_special_strings(response):
    if not isinstance(response, str):
        return False
    return bool(re.search(r'sites|genre|EXTINF', response))

def _extract_text(response_no_spaces):
    trimmed = response_no_spaces.rstrip('*')
    pos = trimmed.rfind('**')
    if pos != -1:
        return trimmed[pos + 2:]
    return trimmed

def _extract_encryption_params(s):
    prefix = "2423"
    suffix = "2324"
    suffix_pos = s.find(suffix)
    if suffix_pos == -1:
        return None
    pwd_mix = s[:suffix_pos + len(suffix)]
    if len(s) < 26:
        return None
    roundtime_in_hax = s[-26:]
    encrypted_text = s[len(pwd_mix):-26]
    pwd_in_hax = pwd_mix[len(prefix):-len(suffix)]
    return {
        'pwdInHax': pwd_in_hax,
        'roundtimeInHax': roundtime_in_hax,
        'encryptedText': encrypted_text
    }

def _decrypt_aes(encrypted_text_hex, pwd_in_hax, roundtime_in_hax):
    if not _HAS_AES:
        return None
    try:
        round_time = bytes.fromhex(roundtime_in_hax)
        pwd = bytes.fromhex(pwd_in_hax)
    except Exception:
        return None
    iv = round_time.ljust(16, b'0')
    key = pwd.ljust(16, b'0')
    try:
        cipher_bytes = bytes.fromhex(encrypted_text_hex)
    except Exception:
        return None
    decrypted = None
    if _AES_MODE == 'pycryptodome':
        try:
            decrypted = _AES_IMPL.new(key, _AES_IMPL.MODE_CBC, iv).decrypt(cipher_bytes)
        except Exception:
            return None
    elif _AES_MODE == 'pyaes':
        try:
            aes = _AES_IMPL.AESModeOfOperationCBC(key, iv=iv)
            d = _AES_IMPL.Decrypter(aes)
            decrypted = d.feed(cipher_bytes)
            decrypted += d.feed()
        except Exception:
            return None
    if decrypted:
        return _strip_pkcs7(decrypted)
    return None

def _extract_content(response, depth=0, max_depth=50):
    if not response or depth > max_depth:
        return None
    current = response.strip()
    has_double_star = '**' in current
    starts_with_2423 = current.startswith('2423')
    if not has_double_star and not starts_with_2423:
        return current
    if has_double_star:
        response_no_spaces = re.sub(r'\s+', '', current)
        cleaned_text = _extract_text(response_no_spaces)
        try:
            decoded = base64.b64decode(cleaned_text).decode('utf-8', errors='replace')
            if _contains_special_strings(decoded):
                return decoded
            return _extract_content(decoded, depth + 1, max_depth)
        except Exception:
            return None
    if starts_with_2423:
        params = _extract_encryption_params(current)
        if not params:
            return None
        decrypted = _decrypt_aes(params['encryptedText'], params['pwdInHax'], params['roundtimeInHax'])
        if decrypted is None:
            return None
        try:
            decrypted_str = decrypted.decode('utf-8', errors='replace')
            if _contains_special_strings(decrypted_str):
                return decrypted_str
            return _extract_content(decrypted_str, depth + 1, max_depth)
        except Exception:
            return None
    return current

def try_decrypt_content(content, url='', external_api_url=DEFAULT_EXTERNAL_API_URL, session=None, max_rounds=5):
    if isinstance(content, str):
        content = content.lstrip('\ufeff')
    if not content:
        return None
    if _contains_special_strings(content) or (content.strip().startswith('{') or content.strip().startswith('[')):
        return content
    current = content
    for i in range(max_rounds):
        result = _extract_content(current)
        if result and result != current:
            current = result
            if _contains_special_strings(current) or (current.strip().startswith('{') or current.strip().startswith('[')):
                return current
        else:
            break
    if current != content:
        return current
    if external_api_url and session:
        try:
            if '?url=' in external_api_url:
                resp = session.get(external_api_url + url, timeout=(5, 10))
            else:
                resp = session.post(external_api_url,
                    json={"action": "fetch_content", "params": {"url": url}, "ts": int(time.time())},
                    timeout=(5, 10))
            if resp.status_code == 200:
                data = resp.json()
                if data.get('status') == 'success':
                    r = data.get('formattedContent') or data.get('data', '')
                    if r:
                        return r
        except Exception:
            pass
    return None

# ========================= 辅助函数 =========================
def clean_preroll_m3u8(content: str) -> str:
    lines = content.splitlines(keepends=True)
    out = []
    start_output = False
    for line in lines:
        s = line.strip()
        if s == "#EXT-X-DISCONTINUITY":
            start_output = True
            continue
        if start_output:
            out.append(line)
    if not start_output:
        return content
    return "".join(out)

def parse_curl_command(curl_str: str):
    import shlex
    url = ""
    headers = {}
    try:
        parts = shlex.split(curl_str)
        for i, p in enumerate(parts):
            if p.startswith("http://") or p.startswith("https://"):
                url = p
            elif p in ("-H", "--header") and i + 1 < len(parts):
                header_str = parts[i + 1]
                if ":" in header_str:
                    k, v = header_str.split(":", 1)
                    headers[k.strip()] = v.strip()
    except Exception:
        pass
    return url, headers

def _encode_url(url):
    if not url:
        return url
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.encode('idna').decode('ascii') if parsed.netloc else ''
        path = urllib.parse.quote(parsed.path, safe='/') if parsed.path else ''
        query = urllib.parse.quote(parsed.query, safe='=&?') if parsed.query else ''
        encoded = urllib.parse.urlunparse((parsed.scheme, netloc, path, parsed.params, query, parsed.fragment))
        return encoded
    except Exception:
        return url

# ========================= 文件下载器 =========================
class FileDownloader:
    SKIP_EXTS = {'.php', '.asp', '.jsp', '.cgi', '.exe', '.dll', '.sh', '.bat'}
    BINARY_EXTS = {'.jar', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.m3u', '.m3u8', '.mp4', '.ts'}
    DOWNLOAD_EXTS = DOWNLOAD_EXTS

    def __init__(self, output_dir, config=None, log_callback=None, progress_callback=None, cancel_event=None):
        self.output_dir = output_dir
        self.config = config or {}
        self.log_callback = log_callback or (lambda msg: None)
        self.progress_callback = progress_callback or (lambda msg: None)
        self.cancel_event = cancel_event
        self.downloaded = {}
        self.failed = []
        self.skipped = []
        self._lock = threading.Lock()
        self._processed = set()

        if 'download' in self.config:
            cfg_download = self.config.get('download', {})
        else:
            cfg_download = self.config

        self.overwrite = cfg_download.get('overwrite', False)
        self.timeout = (cfg_download.get('timeout_connect', 10), cfg_download.get('timeout_read', 60))
        self.chunk_size = cfg_download.get('chunk_size', 8192)
        self.max_size = self.config.get('max_file_size_mb', 100) * 1024 * 1024
        self.skip_exts = set(self.config.get('skip_extensions', []))
        self.skip_exts.update(self.SKIP_EXTS)
        self.skip_patterns = self.config.get('skip_patterns', [])
        self.decrypt_enabled = cfg_download.get('decrypt', {}).get('enabled', True)
        self.external_api = cfg_download.get('decrypt', {}).get('external_api_url', '')
        self.proxy = self.config.get('proxy', '')
        self.github_proxy = self.config.get('github_proxy', GITHUB_PROXY)
        self.user_agent = self.config.get('user_agent', DEFAULT_USER_AGENT)
        self.category_map = cfg_download.get('category_map', {'js': '.js', 'lib': '.json', 'py': '.py', 'jar': '.jar'})
        self.skip_patterns_core = cfg_download.get('skip_patterns_core', SKIP_PATTERNS)
        self.max_workers = cfg_download.get('max_workers', 8)
        self.retry_total = cfg_download.get('retry_total', 2)
        self.retry_backoff = cfg_download.get('retry_backoff', 0.3)
        self.pool_connections = cfg_download.get('pool_connections', 10)
        self.pool_maxsize = cfg_download.get('pool_maxsize', 20)

        self.session = requests.Session()
        retry = Retry(total=self.retry_total, backoff_factor=self.retry_backoff, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry, pool_connections=self.pool_connections, pool_maxsize=self.pool_maxsize)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'identity'
        })
        self.session.verify = False
        if self.proxy:
            self.session.proxies = {'http': self.proxy, 'https': self.proxy}
        os.makedirs(self.output_dir, exist_ok=True)

    def _log(self, msg):
        if self.log_callback:
            self.log_callback(msg)

    def _is_github_file_url(self, url):
        if not url:
            return False
        github_domains = (
            'raw.githubusercontent.com',
            'github.com',
            'gist.github.com',
            'gist.githubusercontent.com',
            'githubusercontent.com'
        )
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            for d in github_domains:
                if d in netloc:
                    return True
        except Exception:
            pass
        return False

    def normalize_github_url(self, url):
        if not url:
            return url
        if self.github_proxy:
            proxy_prefix = self.github_proxy.rstrip('/') + '/'
            if url.startswith(proxy_prefix):
                url = url[len(proxy_prefix):]
        if self._is_github_file_url(url):
            parsed = urllib.parse.urlparse(url)
            path = parsed.path.lstrip('/')
            if 'github.com' in parsed.netloc:
                parts = path.split('/')
                if len(parts) >= 4:
                    user = parts[0]
                    repo = parts[1]
                    if parts[2] in ('blob', 'raw'):
                        branch = parts[3]
                        file_path = '/'.join(parts[4:])
                        url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}"
                    else:
                        url = f"https://raw.githubusercontent.com/{user}/{repo}/master/{'/'.join(parts[3:])}"
            elif 'gist.github.com' in parsed.netloc:
                gist_id = path.split('/')[0]
                url = f"https://gist.githubusercontent.com/raw/{gist_id}/"
        if self.github_proxy and self._is_github_file_url(url):
            if not url.startswith(self.github_proxy):
                proxy = self.github_proxy.rstrip('/') + '/'
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                url = proxy + url.lstrip('/')
        return url

    def split_url_and_suffix(self, url):
        if not url:
            return url, ""
        if ';md5;' in url:
            idx = url.index(';md5;')
            return url[:idx], url[idx:]
        parsed = urllib.parse.urlparse(url)
        if parsed.query and ('md5=' in parsed.query or 'MD5=' in parsed.query):
            base = url.split('?')[0]
            return base, '?' + parsed.query
        return url, ""

    def is_downloadable(self, url, field_key=None):
        if not url or not isinstance(url, str):
            return False
        url_clean = url.strip()
        if not url_clean:
            return False
        if field_key in ('spider', 'jar'):
            if url_clean.startswith("proxy://"):
                return False
            for pat in self.skip_patterns_core:
                if re.search(pat, url_clean):
                    return False
            return True
        if url_clean.startswith("proxy://"):
            return False
        for pat in self.skip_patterns_core:
            if re.search(pat, url_clean):
                return False
        path_part = url_clean.split('?')[0].split(';')[0].rstrip('/')
        ext = os.path.splitext(path_part)[1].lower()
        if ext in self.SKIP_EXTS:
            return False
        if ext in self.DOWNLOAD_EXTS:
            return True
        if url_clean.startswith("http://") or url_clean.startswith("https://"):
            return False
        return False

    def resolve_url(self, rel_path, base_url):
        if not rel_path:
            return None
        if rel_path.startswith(('http://', 'https://')):
            return self.normalize_github_url(rel_path)
        if rel_path.startswith("//"):
            return self.normalize_github_url("https:" + rel_path)
        if rel_path.startswith("./") or rel_path.startswith("../"):
            return self.normalize_github_url(urllib.parse.urljoin(base_url, rel_path))
        if rel_path.startswith("/"):
            parsed = urllib.parse.urlparse(base_url)
            return self.normalize_github_url(f"{parsed.scheme}://{parsed.netloc}{rel_path}")
        return self.normalize_github_url(urllib.parse.urljoin(base_url, rel_path))

    def get_target_path(self, url, category, field_key=None):
        if not url:
            return os.path.join(category, 'unknown')
        clean_url = url
        if self.github_proxy:
            proxy = self.github_proxy.rstrip('/') + '/'
            if clean_url.startswith(proxy):
                clean_url = clean_url[len(proxy):]
        path_part = clean_url.split('?')[0].split(';')[0].rstrip('/')
        path_part = urllib.parse.unquote(path_part)
        filename = os.path.basename(path_part)
        if not filename:
            filename = hashlib.md5(url.encode()).hexdigest()[:8]
            filename += self.category_map.get(category, '.bin')
        ext = os.path.splitext(filename)[1].lower()
        if field_key in ('spider', 'jar'):
            if not ext:
                filename += '.jar'
            return os.path.join('jar', filename)
        if not ext:
            filename += self.category_map.get(category, '.bin')
        return os.path.join(category, filename)

    def should_skip(self, url):
        if not url or not isinstance(url, str):
            return True, "空URL"
        for pattern in self.skip_patterns:
            if pattern in url:
                return True, f"命中跳过模式: {pattern}"
        return False, ""

    def download_file(self, url, base_url, category='lib', field_key=None):
        if self.cancel_event and self.cancel_event.is_set():
            self._log("下载任务已取消")
            return None
        if not url or not isinstance(url, str):
            return None
        url_part, suffix = self.split_url_and_suffix(url)
        if not self.is_downloadable(url_part, field_key):
            return None
        should_skip, reason = self.should_skip(url_part)
        if should_skip:
            with self._lock:
                self.skipped.append((url, reason))
            self._log(f"跳过文件: {url} ({reason})")
            return None
        abs_url = self.resolve_url(url_part, base_url)
        if not abs_url:
            with self._lock:
                self.failed.append((url, "无法解析URL"))
            return None
        target_rel = self.get_target_path(abs_url, category, field_key)
        target_abs = os.path.join(self.output_dir, target_rel)
        with self._lock:
            if target_rel in self._processed:
                self.downloaded[url_part] = target_rel
                return target_rel
            self._processed.add(target_rel)
        if not self.overwrite and os.path.exists(target_abs):
            with self._lock:
                self.downloaded[url_part] = target_rel
            self._log(f"文件已存在，跳过: {target_rel}")
            return target_rel

        self._log(f"下载文件: {abs_url}")
        try:
            try:
                head_resp = self.session.head(abs_url, timeout=self.timeout, allow_redirects=True)
                total_size = int(head_resp.headers.get('content-length', 0))
                support_range = head_resp.headers.get('accept-ranges') == 'bytes'
            except Exception as head_err:
                self._log(f"HEAD请求失败 {abs_url}: {head_err}，尝试直接GET")
                total_size = 0
                support_range = False

            downloaded_size = 0
            req_headers = dict(self.session.headers)
            mode = "wb"
            if os.path.exists(target_abs) and total_size > 0:
                downloaded_size = os.path.getsize(target_abs)
                if downloaded_size == total_size:
                    with self._lock:
                        self.downloaded[url_part] = target_rel
                    self._log(f"✅ 本地已存在完整文件，跳过: {target_rel}")
                    return target_rel
                elif downloaded_size < total_size and support_range:
                    self._log(f"🔄 断点续传 {target_rel} (已下载 {downloaded_size/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB)")
                    req_headers["Range"] = f"bytes={downloaded_size}-"
                    mode = "ab"

            os.makedirs(os.path.dirname(target_abs), exist_ok=True)
            resp = self.session.get(abs_url, headers=req_headers, timeout=self.timeout, stream=True)
            self._log(f"响应状态: {resp.status_code}")
            if resp.status_code not in (200, 206):
                with self._lock:
                    self.failed.append((url, f"HTTP {resp.status_code}"))
                return None

            if total_size > 20 * 1024 * 1024 and support_range and mode == "wb":
                return self._download_file_multithread(abs_url, req_headers, target_abs, target_rel, url_part, total_size, field_key)

            last_log_time = time.time()
            downloaded_len = downloaded_size
            with open(target_abs, mode) as f_local:
                for chunk in resp.iter_content(chunk_size=self.chunk_size):
                    if self.cancel_event and self.cancel_event.is_set():
                        self._log("下载被取消")
                        return None
                    if chunk:
                        f_local.write(chunk)
                        downloaded_len += len(chunk)
                        now = time.time()
                        if now - last_log_time > 1.5:
                            if total_size > 0:
                                pct = (downloaded_len / total_size) * 100
                                self.progress_callback(f"⏳ {target_rel} {pct:.1f}% ({downloaded_len/1024/1024:.1f}MB)")
                            else:
                                self.progress_callback(f"⏳ {target_rel} ({downloaded_len/1024/1024:.1f}MB)")
                            last_log_time = now

            with self._lock:
                self.downloaded[url_part] = target_rel
            self._log(f"下载成功: {target_rel}")
            return target_rel
        except Exception as e:
            with self._lock:
                self.failed.append((url, str(e)))
                self._processed.discard(target_rel)
            self._log(f"下载失败: {e}")
            return None

    def _download_file_multithread(self, url, headers, path, target_rel, url_part, total_size, field_key=None):
        self._log(f"⚡ 启用多线程分块下载: {target_rel}")
        num_threads = min(8, max(2, self.max_workers))
        chunk_size = total_size // num_threads
        ranges = []
        for i in range(num_threads):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < num_threads - 1 else total_size - 1
            ranges.append((start, end))

        temp_files = []
        lock = threading.Lock()
        completed = [0]
        errors = []

        def download_chunk(idx, start, end):
            if self.cancel_event and self.cancel_event.is_set():
                return
            temp_path = f"{path}.part{idx}"
            temp_files.append(temp_path)
            try:
                h = dict(headers)
                h["Range"] = f"bytes={start}-{end}"
                r = self.session.get(url, headers=h, stream=True, timeout=self.timeout)
                r.raise_for_status()
                with open(temp_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if self.cancel_event and self.cancel_event.is_set():
                            return
                        if chunk:
                            f.write(chunk)
                with lock:
                    completed[0] += 1
                    self.progress_callback(f"⏳ {target_rel} 分块 {completed[0]}/{num_threads} 完成")
            except Exception as e:
                with lock:
                    errors.append(str(e))

        with ThreadPoolExecutor(max_workers=num_threads) as ex:
            futures = []
            for idx, (start, end) in enumerate(ranges):
                futures.append(ex.submit(download_chunk, idx, start, end))
            for fut in as_completed(futures):
                pass

        if errors:
            self._log(f"❌ 分块下载出错: {errors[0]}")
            with self._lock:
                self.failed.append((url, f"分块下载失败: {errors[0]}"))
            return None

        with open(path, 'wb') as outfile:
            for i in range(num_threads):
                part_path = f"{path}.part{i}"
                if os.path.exists(part_path):
                    with open(part_path, 'rb') as infile:
                        outfile.write(infile.read())
                    try:
                        os.remove(part_path)
                    except Exception:
                        pass

        with self._lock:
            self.downloaded[url_part] = target_rel
        self._log(f"🎉 多线程下载完成: {target_rel}")
        return target_rel

    def download_text(self, url, base_url, force_decrypt=None):
        if self.cancel_event and self.cancel_event.is_set():
            return None
        if not url or not isinstance(url, str):
            return None
        url_part, suffix = self.split_url_and_suffix(url)
        full_url = self.resolve_url(url_part, base_url)
        if not full_url:
            return None
        self._log(f"请求文本: {full_url}")
        try:
            req_headers = dict(self.session.headers)
            parsed = urllib.parse.urlparse(full_url)
            if 'cnb.cool' in parsed.netloc:
                req_headers['Referer'] = 'https://cnb.cool'
                req_headers['Origin'] = 'https://cnb.cool'
                self._log("自动添加 cnb.cool 请求头")
            resp = self.session.get(full_url, headers=req_headers, timeout=self.timeout)
            self._log(f"响应状态: {resp.status_code}, 内容长度: {len(resp.text)}")
            if resp.status_code != 200:
                self._log(f"下载文本失败，状态码: {resp.status_code}")
                return None
            try:
                content = resp.content.decode('utf-8')
            except UnicodeDecodeError:
                content = resp.text
            content = content.lstrip('\ufeff')
            preview = content[:200].replace('\n', ' ').replace('\r', '')
            self._log(f"内容预览: {preview}...")
            parsed = urllib.parse.urlparse(full_url)
            path = urllib.parse.unquote(parsed.path)
            ext = os.path.splitext(path)[1].lower()
            if ext in self.BINARY_EXTS:
                self._log("二进制文件，不进行解密")
                return content
            do_decrypt = force_decrypt if force_decrypt is not None else self.decrypt_enabled
            if do_decrypt:
                self._log("尝试解密内容...")
                decrypted = try_decrypt_content(content, full_url, self.external_api, self.session, max_rounds=5)
                if decrypted:
                    self._log("解密成功")
                    return decrypted
                else:
                    self._log("解密失败，返回原始内容")
            return content
        except Exception as e:
            self._log(f"下载文本异常: {e}")
            return None

# ========================= JSON路径提取器 =========================
class PathExtractor:
    PATH_FIELDS = {'api', 'ext', 'url', 'wallpaper', 'spider', 'logo', 'jar', 'playerType',
                   'header', 'headers', 'ua', 'ref', 'referer'}
    def __init__(self, config=None):
        self.config = config or {}
        self.recursive_depth = self.config.get('recursive_depth', 2)
        self.extracted = set()
        self._json_files = set()
    def extract(self, obj, depth=0):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    if v.startswith('./'):
                        self.extracted.add(v)
                        if v.endswith('.json') and depth < self.recursive_depth:
                            self._json_files.add(v)
                elif isinstance(v, (dict, list)):
                    self.extract(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                self.extract(item, depth + 1)
    def get_all_paths(self):
        return self.extracted
    def get_json_files(self):
        return self._json_files

# ========================= 主Spider类 =========================
class Spider(BaseSpider):
    VERSION = "v3.0 - 浅色现代风 + 日志面板"
    ACTION_DOWNLOAD_PACKAGE = "local_source_download_package"
    ACTION_SHOW_STATUS = "local_source_show_status"

    def __init__(self):
        super().__init__()
        self.lock = threading.RLock()
        self.inited = False
        self._initial_extend = None
        self.config = {}
        self.package_download_sites = []
        self.download_output_dir = ""
        self.download_config = {}
        self._package_download_state = "idle"
        self._package_download_message = ""
        self._package_download_thread = None
        self._package_download_lock = threading.Lock()
        self._package_cancel_event = None
        self._dialog_refs = []
        self._notification_refs = []
        self._destroyed = False
        self._session = None
        self._site_states = {}
        self._site_op_threads = {}
        self._site_op_lock = threading.Lock()
        self._site_cancel_events = {}
        self.session = None
        self.external_api_url = DEFAULT_EXTERNAL_API_URL
        self.log_enabled = True
        self.log_level = 'info'
        self.log_dir = os.path.join(SCRIPT_DIR, 'logs')
        self.user_agent = DEFAULT_USER_AGENT
        self.category_map = {'js': '.js', 'lib': '.json', 'py': '.py', 'jar': '.jar'}
        self.skip_patterns_core = SKIP_PATTERNS
        self.max_workers = 8
        self.retry_total = 2
        self.retry_backoff = 0.3
        self.pool_connections = 10
        self.pool_maxsize = 20

        self._base_dir = None
        self._resource_dirs = []
        self._config_file_path = None

        self.log_queue = queue.Queue()
        self._persisted_runnable = None
        self._ui_listeners = []
        self._active_views = {}
        self._is_downloading = False
        self._log_dialog_open = False

    # ========================= 动态路径检测 =========================
    def _is_remote_path(self, path):
        if not path:
            return False
        return str(path).lower().startswith(('http://', 'https://', 'ftp://'))

    def _get_base_dir(self):
        return self._base_dir or SCRIPT_DIR

    def _detect_base_dir(self, ext):
        if self._base_dir:
            return self._base_dir

        clues = []
        if isinstance(ext, dict):
            config_file = ext.get('config_file', '')
            if config_file and not self._is_remote_path(config_file):
                clues.append(config_file)
            lives = ext.get('lives', [])
            if isinstance(lives, list):
                for item in lives:
                    if isinstance(item, str) and not self._is_remote_path(item):
                        clues.append(item)
                    elif isinstance(item, dict):
                        for k in ('api', 'url'):
                            v = item.get(k, '')
                            if v and not self._is_remote_path(v):
                                clues.append(v)
            for key in ('接口_单仓', 'lives_urls', '接口_直播', 'lives_url'):
                val = ext.get(key, [])
                if isinstance(val, str) and not self._is_remote_path(val):
                    clues.append(val)
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, str) and not self._is_remote_path(v):
                            clues.append(v)

        if not clues:
            self._base_dir = SCRIPT_DIR
            return self._base_dir

        candidate_bases = []
        candidate_bases.extend(self._resource_dirs)
        candidate_bases.append(SCRIPT_DIR)
        parent = os.path.dirname(SCRIPT_DIR)
        if parent:
            candidate_bases.append(parent)
            pp = os.path.dirname(parent)
            if pp:
                candidate_bases.append(pp)
        candidate_bases.append(os.getcwd())
        for p in _COMMON_USER_DIRS:
            candidate_bases.append(p)

        seen = set()
        unique_bases = []
        for b in candidate_bases:
            if b and b not in seen and os.path.isdir(b):
                seen.add(b)
                unique_bases.append(b)

        for clue in clues:
            strip = clue.lstrip('./').lstrip('.\\').strip()
            basename = os.path.basename(clue)
            clue_dir = os.path.dirname(strip)
            for base in unique_bases:
                test_paths = [
                    os.path.join(base, strip),
                    os.path.join(base, clue) if clue.startswith('./') else None,
                    os.path.join(base, basename),
                    os.path.join(base, 'json', basename) if clue_dir else None,
                    os.path.join(base, 'py', basename) if clue_dir else None,
                ]
                for tp in test_paths:
                    if tp and os.path.exists(tp):
                        self._base_dir = base
                        self._remember_resource_dir(tp)
                        self._log(f"动态检测到基础目录: {base} (线索: {clue} -> {tp})")
                        return self._base_dir

        for base in unique_bases:
            if os.path.isdir(os.path.join(base, 'json')) or os.path.isdir(os.path.join(base, 'py')):
                self._base_dir = base
                self._log(f"通过目录结构检测到基础目录: {base}")
                return self._base_dir

        self._log(f"候选目录均未匹配，开始遍历文件系统搜索线索文件...")
        for root in _FS_SEARCH_ROOTS:
            if not os.path.isdir(root):
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    rel = os.path.relpath(dirpath, root)
                    depth = 0 if rel == '.' else rel.count(os.sep) + 1
                    if depth > 4:
                        dirnames[:] = []
                        continue
                    dirnames[:] = [d for d in dirnames if d not in _FS_SKIP_DIRS]

                    for clue in clues:
                        clue_strip = clue.lstrip('./').lstrip('.\\')
                        clue_basename = os.path.basename(clue_strip)
                        clue_parent = os.path.dirname(clue_strip)

                        if clue_basename not in filenames:
                            continue

                        full_path = os.path.join(dirpath, clue_basename)

                        if clue_parent and clue_parent != '.':
                            if not dirpath.endswith(clue_parent.replace('/', os.sep)):
                                if clue_parent.replace('/', os.sep) not in dirpath:
                                    continue
                            norm_parent = clue_parent.replace('/', os.sep).replace('\\', os.sep)
                            if dirpath.endswith(norm_parent):
                                self._base_dir = dirpath[:-len(norm_parent)].rstrip('/\\') or '/'
                            else:
                                idx = dirpath.find(norm_parent)
                                if idx >= 0:
                                    self._base_dir = dirpath[:idx].rstrip('/\\') or '/'
                                else:
                                    self._base_dir = os.path.dirname(dirpath)
                        else:
                            self._base_dir = dirpath

                        if self._base_dir and os.path.isdir(self._base_dir):
                            self._remember_resource_dir(full_path)
                            self._log(f"文件系统搜索检测到基础目录: {self._base_dir} (线索: {clue} -> {full_path})")
                            return self._base_dir

            except Exception as e:
                self._log(f"搜索 {root} 失败: {e}")
                continue

        self._base_dir = SCRIPT_DIR
        self._log(f"未检测到用户文件目录，回退到 SCRIPT_DIR: {self._base_dir}")
        return self._base_dir

    def _resolve_file_path(self, path, base_dirs=None):
        if not path or self._is_remote_path(path):
            return None, None

        if os.path.isabs(path) and os.path.exists(path):
            d = os.path.dirname(path)
            return path, d

        basename = os.path.basename(path)
        strip = path.lstrip('./').lstrip('.\\')
        strip_parent = os.path.dirname(strip)

        candidates = []

        base = self._get_base_dir()
        for b in [base, SCRIPT_DIR, os.getcwd()]:
            if b:
                candidates.append(os.path.join(b, strip))
                candidates.append(os.path.join(b, basename))
                if strip_parent:
                    candidates.append(os.path.join(b, strip_parent, basename))

        for rd in getattr(self, '_resource_dirs', []) or []:
            if rd:
                candidates.append(os.path.join(rd, strip))
                candidates.append(os.path.join(rd, basename))

        p = SCRIPT_DIR
        for _ in range(3):
            p = os.path.dirname(p)
            if p and os.path.isdir(p):
                candidates.append(os.path.join(p, strip))
                candidates.append(os.path.join(p, basename))

        if base_dirs is None:
            base_dirs = _COMMON_USER_DIRS
        for b in base_dirs:
            candidates.append(os.path.join(b, strip))
            candidates.append(os.path.join(b, basename))

        seen = set()
        for cand in candidates:
            if not cand or cand in seen:
                continue
            seen.add(cand)
            if os.path.exists(cand):
                self._remember_resource_dir(cand)
                cand_dir = os.path.dirname(cand)
                if strip_parent and strip_parent != '.':
                    if cand_dir.endswith(strip_parent.replace('/', os.sep)):
                        inferred_base = cand_dir[:-len(strip_parent)].rstrip('/\\') or '/'
                    else:
                        inferred_base = cand_dir
                else:
                    inferred_base = cand_dir
                return cand, inferred_base

        for root in _FS_SEARCH_ROOTS:
            if not os.path.isdir(root):
                continue
            try:
                for dirpath, dirnames, filenames in os.walk(root):
                    rel = os.path.relpath(dirpath, root)
                    depth = 0 if rel == '.' else rel.count(os.sep) + 1
                    if depth > 4:
                        dirnames[:] = []
                        continue
                    dirnames[:] = [d for d in dirnames if d not in _FS_SKIP_DIRS]

                    if basename not in filenames:
                        continue

                    found = os.path.join(dirpath, basename)

                    if strip_parent and strip_parent != '.':
                        norm_parent = strip_parent.replace('/', os.sep).replace('\\', os.sep)
                        if not dirpath.endswith(norm_parent) and norm_parent not in dirpath:
                            continue
                        if dirpath.endswith(norm_parent):
                            inferred_base = dirpath[:-len(norm_parent)].rstrip('/\\') or '/'
                        else:
                            idx = dirpath.find(norm_parent)
                            inferred_base = dirpath[:idx].rstrip('/\\') or '/' if idx >= 0 else dirpath
                    else:
                        inferred_base = dirpath

                    self._remember_resource_dir(found)
                    return found, inferred_base

            except Exception:
                continue

        return None, None

    def _resolve_resource_path(self, source):
        if not source:
            return None, None
        source = source.strip()

        if self._is_remote_path(source):
            return 'remote', source

        if os.path.isabs(source) and os.path.exists(source):
            return 'local', source

        found, _ = self._resolve_file_path(source)
        if found:
            return 'local', found

        base = self._get_base_dir()
        if source.startswith('./') or source.startswith('.\\'):
            return 'local', os.path.join(base, source[2:])
        elif not os.path.isabs(source):
            return 'local', os.path.join(base, source)
        else:
            return 'local', source

    def _resolve_local_path(self, path):
        if not path or self._is_remote_path(path):
            return path
        if os.path.isabs(path) and os.path.exists(path):
            return path

        found, _ = self._resolve_file_path(path)
        if found:
            return found
        return path

    def _remember_resource_dir(self, file_path):
        try:
            d = os.path.dirname(os.path.abspath(file_path))
            if d and d not in self._resource_dirs:
                self._resource_dirs.insert(0, d)
                parent = os.path.dirname(d)
                if parent and parent not in self._resource_dirs:
                    self._resource_dirs.append(parent)
                self._log(f"记录资源目录: {d}")
        except Exception:
            pass

    def _load_json_resource(self, source, allow_decrypt=False):
        if not source:
            return None
        source = source.strip()

        if self._is_remote_path(source):
            try:
                if self.session is None:
                    self._init_session()
                resp = self.session.get(source, timeout=(10, 30), verify=False)
                if resp.status_code != 200:
                    self._log(f"远程资源返回非200: {source} [{resp.status_code}]")
                    return None
                text = _decode_bytes(resp.content)
                try:
                    return json.loads(text)
                except Exception:
                    if allow_decrypt:
                        dec = try_decrypt_content(text, source, self.external_api_url, self.session, max_rounds=5)
                        if dec:
                            try:
                                return json.loads(dec)
                            except Exception:
                                m = re.search(r'\{[\s\S]*\}', dec)
                                if m:
                                    try:
                                        return json.loads(m.group())
                                    except Exception:
                                        pass
                                m2 = re.search(r'"(?:lives)"\s*:\s*(\[[\s\S]*?\])', dec)
                                if m2:
                                    try:
                                        return {"lives": json.loads(m2.group(1))}
                                    except Exception:
                                        pass
                    return None
            except Exception as e:
                self._log(f"远程加载失败 {source}: {e}")
                return None

        candidates_to_try = []

        if os.path.isabs(source) and os.path.exists(source):
            candidates_to_try.append(source)

        found, found_base = self._resolve_file_path(source)
        if found:
            candidates_to_try.append(found)

        base = self._get_base_dir()
        strip = source.lstrip('./').lstrip('.\\')
        for b in [base, SCRIPT_DIR, os.getcwd()]:
            if b:
                candidates_to_try.append(os.path.join(b, strip))
                candidates_to_try.append(os.path.join(b, os.path.basename(source)))

        for rd in getattr(self, '_resource_dirs', []) or []:
            if rd:
                candidates_to_try.append(os.path.join(rd, strip))
                candidates_to_try.append(os.path.join(rd, os.path.basename(source)))

        for b in _COMMON_USER_DIRS:
            candidates_to_try.append(os.path.join(b, strip))
            candidates_to_try.append(os.path.join(b, os.path.basename(source)))

        seen = set()
        uniq_candidates = []
        for c in candidates_to_try:
            if c and c not in seen:
                seen.add(c)
                uniq_candidates.append(c)

        last_err = None
        for cand in uniq_candidates:
            if not os.path.exists(cand):
                continue
            try:
                data = json.loads(_read_text_file(cand))
                self._remember_resource_dir(cand)
                return data
            except json.JSONDecodeError as e:
                last_err = e
                self._log(f"本地文件JSON解析失败 {cand}: {e}")
            except Exception as e:
                last_err = e
                self._log(f"读取本地文件失败 {cand}: {e}")

        if last_err is None:
            self._log(f"本地文件不存在: {source} (base={self._get_base_dir()})")
        return None

    def _load_config_file(self, path):
        if not path:
            return None
        return self._load_json_resource(path, allow_decrypt=False)

    def _load_ext_from_path(self, path):
        if not path:
            return None
        result = self._load_json_resource(path, allow_decrypt=False)
        if result is not None:
            return result
        if self._is_remote_path(path):
            return None

        candidates = []
        strip = path.lstrip('./').lstrip('.\\')
        basename = os.path.basename(path)

        found, _ = self._resolve_file_path(path)
        if found:
            candidates.append(found)

        for b in [self._get_base_dir(), SCRIPT_DIR, os.getcwd()]:
            if b:
                candidates.append(os.path.join(b, path))
                candidates.append(os.path.join(b, strip))

        for rd in getattr(self, '_resource_dirs', []) or []:
            if rd:
                candidates.append(os.path.join(rd, strip))
                candidates.append(os.path.join(rd, basename))

        for b in _COMMON_USER_DIRS:
            candidates.append(os.path.join(b, strip))
            candidates.append(os.path.join(b, basename))

        seen = set()
        for p in candidates:
            if not p or p in seen:
                continue
            seen.add(p)
            if os.path.exists(p):
                try:
                    data = json.loads(_read_text_file(p))
                    self._remember_resource_dir(p)
                    return data
                except Exception as e:
                    self._log(f"读取配置失败 {p}: {e}")
                    continue
        return None

    # ========================= 站点状态管理 =========================
    def _init_site_state(self, site_id):
        if site_id not in self._site_states:
            self._site_states[site_id] = {
                'decrypt_status': 'idle', 'decrypt_msg': '未执行',
                'localize_status': 'idle', 'localize_msg': '未执行',
                'apply_status': 'idle', 'apply_msg': '未执行',
                'decrypt_result': None,
                'localize_result': None,
            }

    def _get_site_status_icon(self, status):
        icons = {'idle': '⚪', 'processing': '🔄', 'success': '✅', 'error': '❌', 'partial': '⚠️'}
        return icons.get(status, '⚪')

    def _get_decrypt_status_text(self, site):
        state = self._site_states.get(site['id'], {})
        status = state.get('decrypt_status', 'idle')
        msg = state.get('decrypt_msg', '未执行')
        icon = self._get_site_status_icon(status)
        if status == 'processing':
            return f"{icon} 解密中..."
        elif status == 'success':
            return f"{icon} 已解密"
        elif status == 'error':
            return f"{icon} 解密失败"
        else:
            return f"{icon} 未执行"

    def _get_localize_status_text(self, site):
        state = self._site_states.get(site['id'], {})
        status = state.get('localize_status', 'idle')
        msg = state.get('localize_msg', '未执行')
        icon = self._get_site_status_icon(status)
        if status == 'processing':
            return f"{icon} 本地化中..."
        elif status == 'success':
            return f"{icon} 已本地化"
        elif status == 'error':
            return f"{icon} 本地化失败"
        else:
            return f"{icon} 未执行"

    def _log(self, msg, level='info'):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{level.upper()}] {msg}"
        print(line)
        self._push_log(msg)
        if not getattr(self, 'log_enabled', True):
            return
        try:
            log_dir = getattr(self, 'log_dir', None) or os.path.join(self.download_output_dir or SCRIPT_DIR, 'log')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'download.log')
            with open(log_file, 'a', encoding='utf-8') as f_local:
                f_local.write(line + '\n')
        except Exception:
            pass

    def _init_session(self):
        if self._session is None:
            self._session = requests.Session()
            retry = Retry(total=2, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
            adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=20)
            self._session.mount('http://', adapter)
            self._session.mount('https://', adapter)
            self._session.headers.update({
                'User-Agent': DEFAULT_USER_AGENT,
                'Accept': '*/*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'identity'
            })
            self._session.verify = False
            self.session = self._session

    # ========================= UI 线程辅助 =========================
    def _activity(self):
        try:
            from java import jclass
            JClass = jclass("java.lang.Class")
            AT = JClass.forName("android.app.ActivityThread")
            cur = AT.getMethod("currentActivityThread").invoke(None)
            f = AT.getDeclaredField("mActivities")
            f.setAccessible(True)
            for r in f.get(cur).values().toArray():
                rc = r.getClass()
                pf = rc.getDeclaredField("paused")
                pf.setAccessible(True)
                if not pf.getBoolean(r):
                    af = rc.getDeclaredField("activity")
                    af.setAccessible(True)
                    return af.get(r)
        except Exception:
            pass
        return None

    def _run_on_ui(self, ui_builder_fn):
        try:
            from java import jclass, dynamic_proxy
            from java.lang import Runnable
            act = self._activity()
            if not act:
                return

            Builder = jclass("android.app.AlertDialog$Builder")
            EditText = jclass("android.widget.EditText")
            TextView = jclass("android.widget.TextView")
            LinearLayout = jclass("android.widget.LinearLayout")
            LP = jclass("android.widget.LinearLayout$LayoutParams")
            InputType = jclass("android.text.InputType")
            DialogClick = jclass("android.content.DialogInterface$OnClickListener")
            Toast = jclass("android.widget.Toast")
            ScrollView = jclass("android.widget.ScrollView")
            Switch = jclass("android.widget.Switch")
            Button = jclass("android.widget.Button")
            GradientDrawable = jclass("android.graphics.drawable.GradientDrawable")
            Color = jclass("android.graphics.Color")
            Gravity = jclass("android.view.Gravity")
            TypedValue = jclass("android.util.TypedValue")
            Typeface = jclass("android.graphics.Typeface")

            class Run(dynamic_proxy(Runnable)):
                def run(self):
                    ui_builder_fn(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                                  Color, Gravity, TypedValue, Typeface)

            act.getWindow().getDecorView().post(Run())
        except Exception as e:
            self._log(f"UI 线程执行失败: {e}")

    # ========================= 浅色现代风格弹窗 =========================
    def _dp2px(self, act, dp):
        try:
            from java import jclass
            TypedValue = jclass("android.util.TypedValue")
            return int(TypedValue.applyDimension(TypedValue.COMPLEX_UNIT_DIP, dp, act.getResources().getDisplayMetrics()))
        except Exception:
            return int(dp)

    def _make_modern_button(self, act, text, bg_color, text_color, callback, dialog_ref=None, is_primary=False):
        """浅色现代风格按钮"""
        try:
            from java import jclass, dynamic_proxy
            Button = jclass("android.widget.Button")
            GradientDrawable = jclass("android.graphics.drawable.GradientDrawable")
            Color = jclass("android.graphics.Color")
            ViewOnClickListener = jclass("android.view.View$OnClickListener")
            Typeface = jclass("android.graphics.Typeface")

            btn = Button(act)
            btn.setText(text)
            btn.setAllCaps(False)
            btn.setTextSize(14.0)
            btn.setTypeface(Typeface.DEFAULT)
            btn.setPadding(self._dp2px(act, 20), self._dp2px(act, 10), self._dp2px(act, 20), self._dp2px(act, 10))

            btn.setTextColor(Color.parseColor(text_color))

            bg = GradientDrawable()
            bg.setShape(GradientDrawable.RECTANGLE)
            bg.setCornerRadius(float(self._dp2px(act, 8)))
            bg.setColor(Color.parseColor(bg_color))
            if is_primary:
                bg.setStroke(1, Color.parseColor("#6C63FF"))
            else:
                bg.setStroke(1, Color.parseColor("#D1D9E6"))
            btn.setBackgroundDrawable(bg)

            class ClickListener(dynamic_proxy(ViewOnClickListener)):
                def onClick(self, v):
                    if dialog_ref and dialog_ref.get("dialog"):
                        try:
                            dialog_ref["dialog"].dismiss()
                        except Exception:
                            pass
                    if callback:
                        callback()
            listener = ClickListener()
            self._ui_listeners.append(listener)
            btn.setOnClickListener(listener)
            return btn
        except Exception as e:
            self._log(f"创建按钮失败: {e}")
            return None

    def _build_modern_dialog(self, act, Builder, LinearLayout, TextView, LP, ScrollView,
                              Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                              title, content_view, bottom_buttons, width_ratio=0.90):
        """浅色现代风格对话框"""
        try:
            root = LinearLayout(act)
            root.setOrientation(LinearLayout.VERTICAL)
            root.setBackgroundColor(Color.WHITE)

            bg = GradientDrawable()
            bg.setShape(GradientDrawable.RECTANGLE)
            bg.setCornerRadius(float(self._dp2px(act, 12)))
            bg.setColor(Color.WHITE)
            bg.setStroke(1, Color.parseColor("#E2E8F0"))
            root.setBackgroundDrawable(bg)

            root.setPadding(self._dp2px(act, 24), self._dp2px(act, 16),
                           self._dp2px(act, 24), self._dp2px(act, 12))

            if title:
                color_bar = TextView(act)
                color_bar.setBackgroundColor(Color.parseColor("#6C63FF"))
                color_bar.setHeight(self._dp2px(act, 4))
                root.addView(color_bar, LP(-1, self._dp2px(act, 4)))

                title_view = TextView(act)
                title_view.setText(title)
                title_view.setTextSize(18.0)
                title_view.setTypeface(Typeface.DEFAULT_BOLD)
                title_view.setTextColor(Color.parseColor("#2C3E50"))
                title_view.setGravity(Gravity.CENTER_HORIZONTAL)
                title_view.setPadding(0, self._dp2px(act, 12), 0, self._dp2px(act, 8))
                root.addView(title_view, LP(-1, -2))

                divider = TextView(act)
                divider.setBackgroundColor(Color.parseColor("#E2E8F0"))
                divider.setHeight(1)
                root.addView(divider, LP(-1, 1))

            if content_view:
                content_container = LinearLayout(act)
                content_container.setOrientation(LinearLayout.VERTICAL)
                content_container.setPadding(0, self._dp2px(act, 12), 0, self._dp2px(act, 12))
                content_container.addView(content_view, LP(-1, -2))
                root.addView(content_container, LP(-1, -2))

            if bottom_buttons:
                divider2 = TextView(act)
                divider2.setBackgroundColor(Color.parseColor("#E2E8F0"))
                divider2.setHeight(1)
                root.addView(divider2, LP(-1, 1))

                btn_container = LinearLayout(act)
                btn_container.setOrientation(LinearLayout.HORIZONTAL)
                btn_container.setGravity(Gravity.CENTER_HORIZONTAL)
                btn_container.setPadding(0, self._dp2px(act, 12), 0, 0)

                dialog_holder = {"dialog": None}

                for i, btn_info in enumerate(bottom_buttons):
                    is_primary = btn_info.get("is_primary", False)
                    bg_color = btn_info.get("color", "#6C63FF" if is_primary else "#E8ECF1")
                    text_color = "#FFFFFF" if is_primary else "#4A4A4A"
                    btn = self._make_modern_button(act, btn_info["text"], bg_color, text_color,
                                                   btn_info["callback"], dialog_holder, is_primary)
                    if btn:
                        params = LP(0, -2, 1.0)
                        if i > 0:
                            params.setMargins(self._dp2px(act, 8), 0, 0, 0)
                        btn_container.addView(btn, params)

                root.addView(btn_container, LP(-1, -2))

            builder = Builder(act)
            builder.setView(root)
            dialog = builder.create()
            dialog.setCancelable(True)
            dialog_holder["dialog"] = dialog

            window = dialog.getWindow()
            if window:
                metrics = act.getResources().getDisplayMetrics()
                width = int(metrics.widthPixels * width_ratio)
                window.setLayout(width, -2)

            return dialog
        except Exception as e:
            self._log(f"构建对话框失败: {e}")
            return None

    def _show_modern_confirm(self, title, message, on_confirm, extra_buttons=None, show_cancel=True):
        """浅色现代确认对话框"""
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            content_view = TextView(act)
            content_view.setText(message)
            content_view.setTextSize(15.0)
            content_view.setTypeface(Typeface.DEFAULT)
            content_view.setTextColor(Color.parseColor("#4A4A4A"))
            content_view.setLineSpacing(0, 1.5)
            content_view.setPadding(0, 0, 0, 0)

            buttons = []
            if extra_buttons:
                for b in extra_buttons:
                    buttons.append({
                        "text": b["text"],
                        "color": "#E8ECF1",
                        "callback": b["callback"],
                        "is_primary": False
                    })
            if show_cancel:
                buttons.append({
                    "text": "取消",
                    "color": "#E8ECF1",
                    "callback": None,
                    "is_primary": False
                })
            buttons.append({
                "text": "确定",
                "color": "#6C63FF",
                "callback": on_confirm,
                "is_primary": True
            })

            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               title, content_view, buttons)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _show_modern_input(self, title, hint, current_value, on_save, multiline=False):
        """浅色现代输入对话框"""
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            edit = EditText(act)
            edit.setSingleLine(not multiline)
            if multiline:
                edit.setMinLines(3)
                edit.setMaxLines(8)
                edit.setGravity(Gravity.TOP | Gravity.START)
            edit.setHint(hint)
            edit.setHintTextColor(Color.parseColor("#A0AEC0"))
            edit.setInputType(InputType.TYPE_CLASS_TEXT)
            if current_value is not None:
                edit.setText(str(current_value))
                edit.setSelection(len(str(current_value)))
            edit.setPadding(self._dp2px(act, 12), self._dp2px(act, 10),
                           self._dp2px(act, 12), self._dp2px(act, 10))
            edit.setTextSize(15.0)
            edit.setTypeface(Typeface.DEFAULT)
            edit.setTextColor(Color.parseColor("#2C3E50"))

            bg = GradientDrawable()
            bg.setShape(GradientDrawable.RECTANGLE)
            bg.setCornerRadius(float(self._dp2px(act, 6)))
            bg.setColor(Color.parseColor("#F8F9FA"))
            bg.setStroke(1, Color.parseColor("#E2E8F0"))
            edit.setBackgroundDrawable(bg)

            def do_save():
                val = str(edit.getText().toString()).strip()
                try:
                    on_save(val)
                    Toast.makeText(act, "已保存", Toast.LENGTH_SHORT).show()
                except Exception as e:
                    Toast.makeText(act, f"保存失败: {e}", Toast.LENGTH_LONG).show()

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "保存", "color": "#6C63FF", "callback": do_save, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               title, edit, buttons)
            if dialog:
                dialog.show()
                edit.requestFocus()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _show_modern_info(self, title, message, show_copy=False):
        """浅色现代信息对话框"""
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            content_view = TextView(act)
            content_view.setText(message)
            content_view.setTextSize(15.0)
            content_view.setTypeface(Typeface.DEFAULT)
            content_view.setTextColor(Color.parseColor("#4A4A4A"))
            content_view.setLineSpacing(0, 1.5)
            if len(message) > 300:
                scroll = ScrollView(act)
                scroll.addView(content_view, LP(-1, -2))
                content_view = scroll

            buttons = []
            if show_copy:
                def do_copy():
                    try:
                        clipboard = act.getSystemService(act.CLIPBOARD_SERVICE)
                        ClipData = jclass("android.content.ClipData")
                        clip = ClipData.newPlainText(title, message)
                        clipboard.setPrimaryClip(clip)
                        Toast.makeText(act, "已复制到剪贴板", Toast.LENGTH_SHORT).show()
                    except Exception:
                        pass
                buttons.append({"text": "复制", "color": "#E8ECF1", "callback": do_copy, "is_primary": False})
            buttons.append({"text": "关闭", "color": "#6C63FF", "callback": None, "is_primary": True})

            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               title, content_view, buttons)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _show_modern_batch_selector(self, title, callback):
        """浅色现代批量站点选择器"""
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            container = LinearLayout(act)
            container.setOrientation(LinearLayout.VERTICAL)

            desc = TextView(act)
            desc.setText("选择要批量处理的站点（默认选中已开启）")
            desc.setTextSize(14.0)
            desc.setTypeface(Typeface.DEFAULT)
            desc.setTextColor(Color.parseColor("#7F8C8D"))
            desc.setPadding(0, 0, 0, self._dp2px(act, 12))
            container.addView(desc, LP(-1, -2))

            switches = {}
            for site in self.package_download_sites:
                sw = Switch(act)
                sw.setText(str(site.get("name", "未命名")))
                sw.setTextSize(16.0)
                sw.setTypeface(Typeface.DEFAULT)
                sw.setTextColor(Color.parseColor("#2C3E50"))
                sw.setChecked(bool(site.get("enabled", True)))
                sw.setPadding(0, self._dp2px(act, 6), 0, self._dp2px(act, 6))
                container.addView(sw, LP(-1, -2))
                switches[str(site.get("id", ""))] = sw

            scroll = ScrollView(act)
            scroll.addView(container, LP(-1, -2))

            def do_confirm():
                selected = []
                for sid, ctrl in switches.items():
                    if ctrl.isChecked():
                        for s in self.package_download_sites:
                            if str(s.get("id", "")) == sid:
                                selected.append(s)
                                break
                callback(selected)

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "确定", "color": "#6C63FF", "callback": do_confirm, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               title, scroll, buttons, width_ratio=0.95)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _show_modern_text_editor(self, title, content, file_path, remote_url, local_url, on_save):
        """浅色现代大文本编辑器：上排三按钮 + 编辑区 + 下排三按钮"""
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            metrics = act.getResources().getDisplayMetrics()
            screen_width = metrics.widthPixels
            screen_height = metrics.heightPixels

            root = LinearLayout(act)
            root.setOrientation(LinearLayout.VERTICAL)
            root.setBackgroundColor(Color.WHITE)

            bg = GradientDrawable()
            bg.setShape(GradientDrawable.RECTANGLE)
            bg.setCornerRadius(float(self._dp2px(act, 12)))
            bg.setColor(Color.WHITE)
            bg.setStroke(1, Color.parseColor("#E2E8F0"))
            root.setBackgroundDrawable(bg)

            root.setPadding(self._dp2px(act, 16), self._dp2px(act, 12),
                           self._dp2px(act, 16), self._dp2px(act, 12))

            color_bar = TextView(act)
            color_bar.setBackgroundColor(Color.parseColor("#6C63FF"))
            color_bar.setHeight(self._dp2px(act, 4))
            root.addView(color_bar, LP(-1, self._dp2px(act, 4)))

            title_view = TextView(act)
            title_view.setText(title)
            title_view.setTextSize(18.0)
            title_view.setTypeface(Typeface.DEFAULT_BOLD)
            title_view.setTextColor(Color.parseColor("#2C3E50"))
            title_view.setGravity(Gravity.CENTER_HORIZONTAL)
            title_view.setPadding(0, self._dp2px(act, 10), 0, self._dp2px(act, 6))
            root.addView(title_view, LP(-1, -2))

            div = TextView(act)
            div.setBackgroundColor(Color.parseColor("#E2E8F0"))
            div.setHeight(1)
            root.addView(div, LP(-1, 1))

            # 上排按钮
            top_btn_row = LinearLayout(act)
            top_btn_row.setOrientation(LinearLayout.HORIZONTAL)
            top_btn_row.setPadding(0, self._dp2px(act, 10), 0, self._dp2px(act, 8))

            edit_holder = {"edit": None, "is_editable": [False]}

            def copy_decrypt_url():
                self._copy_to_clipboard(local_url, "已复制解密文件路径")
                Toast.makeText(act, "已复制解密U", Toast.LENGTH_SHORT).show()

            def toggle_edit():
                edit_obj = edit_holder["edit"]
                if edit_obj:
                    edit_holder["is_editable"][0] = not edit_holder["is_editable"][0]
                    edit_obj.setEnabled(edit_holder["is_editable"][0])
                    edit_obj.setFocusable(edit_holder["is_editable"][0])
                    edit_obj.setFocusableInTouchMode(edit_holder["is_editable"][0])
                    if edit_holder["is_editable"][0]:
                        edit_obj.requestFocus()
                        # 修复：直接比较字符串，不用 .toString()
                        for i in range(top_btn_row.getChildCount()):
                            child = top_btn_row.getChildAt(i)
                            if isinstance(child, Button) and str(child.getText()) == "编辑":
                                child.setText("锁定")
                                child.setTextColor(Color.parseColor("#6C63FF"))
                                break
                    else:
                        for i in range(top_btn_row.getChildCount()):
                            child = top_btn_row.getChildAt(i)
                            if isinstance(child, Button) and str(child.getText()) == "锁定":
                                child.setText("编辑")
                                child.setTextColor(Color.parseColor("#4A4A4A"))
                                break

            def copy_content():
                edit_obj = edit_holder["edit"]
                if edit_obj:
                    text = str(edit_obj.getText().toString())
                    self._copy_to_clipboard(text, "已复制全部内容")
                    Toast.makeText(act, "已复制全部内容", Toast.LENGTH_SHORT).show()

            top_buttons = [
                ("解密U", "#E8ECF1", "#4A4A4A", copy_decrypt_url),
                ("编辑", "#E8ECF1", "#4A4A4A", toggle_edit),
                ("复制", "#E8ECF1", "#4A4A4A", copy_content),
            ]

            for idx, (text, bgc, txc, cb) in enumerate(top_buttons):
                btn = self._make_modern_button(act, text, bgc, txc, cb, None, False)
                if btn:
                    params = LP(0, -2, 1.0)
                    if idx > 0:
                        params.setMargins(self._dp2px(act, 6), 0, 0, 0)
                    top_btn_row.addView(btn, params)
            root.addView(top_btn_row, LP(-1, -2))

            # 编辑区
            edit = EditText(act)
            edit.setMinLines(10)
            edit.setMaxLines(20)
            edit.setGravity(Gravity.TOP | Gravity.START)
            edit.setTextSize(13.0)
            edit.setTypeface(Typeface.MONOSPACE)
            edit.setTextColor(Color.parseColor("#2C3E50"))
            edit.setHintTextColor(Color.parseColor("#A0AEC0"))
            edit.setText(content)
            edit.setEnabled(False)
            edit.setFocusable(False)
            edit.setFocusableInTouchMode(False)
            edit.setHorizontalScrollBarEnabled(True)
            edit.setVerticalScrollBarEnabled(True)
            edit.setPadding(self._dp2px(act, 12), self._dp2px(act, 12),
                           self._dp2px(act, 12), self._dp2px(act, 12))

            bg_edit = GradientDrawable()
            bg_edit.setShape(GradientDrawable.RECTANGLE)
            bg_edit.setCornerRadius(float(self._dp2px(act, 6)))
            bg_edit.setColor(Color.parseColor("#F8F9FA"))
            bg_edit.setStroke(1, Color.parseColor("#E2E8F0"))
            edit.setBackgroundDrawable(bg_edit)

            edit_holder["edit"] = edit

            edit_scroll = ScrollView(act)
            edit_scroll.addView(edit, LP(-1, -1))
            root.addView(edit_scroll, LP(-1, int(screen_height * 0.55)))

            div2 = TextView(act)
            div2.setBackgroundColor(Color.parseColor("#E2E8F0"))
            div2.setHeight(1)
            root.addView(div2, LP(-1, 1))

            # 下排按钮
            bottom_btn_row = LinearLayout(act)
            bottom_btn_row.setOrientation(LinearLayout.HORIZONTAL)
            bottom_btn_row.setPadding(0, self._dp2px(act, 10), 0, 0)

            def copy_remote_url():
                self._copy_to_clipboard(remote_url, "已复制远程接口URL")
                Toast.makeText(act, "已复制远程U", Toast.LENGTH_SHORT).show()

            def do_save_content():
                try:
                    new_content = str(edit.getText().toString())
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    on_save()
                    Toast.makeText(act, "已保存 ✓", Toast.LENGTH_SHORT).show()
                except Exception as e:
                    Toast.makeText(act, f"保存失败: {e}", Toast.LENGTH_LONG).show()

            dialog_holder = {"dialog": None}

            bottom_buttons = [
                ("远程U", "#E8ECF1", "#4A4A4A", copy_remote_url),
                ("保存", "#6C63FF", "#FFFFFF", do_save_content, True),
                ("关闭", "#E8ECF1", "#4A4A4A", None),
            ]

            for idx, btn_info in enumerate(bottom_buttons):
                is_primary = btn_info[4] if len(btn_info) > 4 else False
                bgc = btn_info[1]
                txc = btn_info[2]
                cb = btn_info[3]
                btn = self._make_modern_button(act, btn_info[0], bgc, txc, cb, dialog_holder, is_primary)
                if btn:
                    params = LP(0, -2, 1.0)
                    if idx > 0:
                        params.setMargins(self._dp2px(act, 6), 0, 0, 0)
                    bottom_btn_row.addView(btn, params)
            root.addView(bottom_btn_row, LP(-1, -2))

            builder = Builder(act)
            builder.setView(root)
            dialog = builder.create()
            dialog.setCancelable(True)
            dialog_holder["dialog"] = dialog

            window = dialog.getWindow()
            if window:
                width = int(screen_width * 0.94)
                height = int(screen_height * 0.88)
                window.setLayout(width, height)

            dialog.show()
            self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    # ========================= 旧弹窗重定向 =========================
    def _show_info_dialog(self, title, message, show_copy=False):
        self._show_modern_info(title, message, show_copy)

    def _show_input_dialog(self, title, hint, current_value, on_save_fn, multiline=False, input_type_value=None):
        self._show_modern_input(title, hint, current_value, on_save_fn, multiline)

    def _show_confirm_dialog(self, title, message, on_confirm_fn, extra_buttons=None):
        self._show_modern_confirm(title, message, on_confirm_fn, extra_buttons)

    def _show_batch_site_selector(self, title, action_type, callback):
        self._show_modern_batch_selector(title, callback)

    # ========================= 日志面板 =========================
    def _push_log(self, msg):
        time_str = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{time_str}] {msg}")

    def _start_log_looper(self, main_handler):
        from java import dynamic_proxy
        from java.lang import Runnable
        if self._persisted_runnable is not None:
            return
        class LogUpdater(dynamic_proxy(Runnable)):
            def __init__(self, spider_ref, handler):
                super().__init__()
                self.spider = spider_ref
                self.handler = handler
            def run(self):
                view = self.spider._active_views.get("log")
                scroll = self.spider._active_views.get("scroll")
                if not view or not scroll:
                    self.spider._persisted_runnable = None
                    return
                batch_logs = []
                while not self.spider.log_queue.empty():
                    try:
                        batch_logs.append(self.spider.log_queue.get_nowait())
                    except queue.Empty:
                        break
                if batch_logs:
                    current_text = str(view.getText() or "")
                    new_text = current_text + "\n" + "\n".join(batch_logs)
                    if len(new_text) > 6000:
                        new_text = new_text[-6000:]
                    view.setText(new_text)
                    scroll.post(Runnable_Scroll(scroll))
                self.handler.postDelayed(self, 300)
        class Runnable_Scroll(dynamic_proxy(Runnable)):
            def __init__(self, scroll):
                super().__init__()
                self.scroll = scroll
            def run(self):
                if self.scroll:
                    self.scroll.fullScroll(130)
        self._persisted_runnable = LogUpdater(self, main_handler)
        main_handler.post(self._persisted_runnable)

    def _get_recent_logs(self, lines=100):
        log_file = os.path.join(self.log_dir, 'download.log') if self.log_dir else None
        if not log_file or not os.path.exists(log_file):
            return None
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return ''.join(recent)
        except Exception:
            return None

    def _show_log_dialog(self):
        if self._log_dialog_open:
            self._push_log("⚠️ 日志面板已在运行中")
            return
        self._log_dialog_open = True
        self._ui_listeners.clear()
        self._active_views.clear()

        def on_ui(act, classes):
            (Builder, LinearLayout, ScrollView, TextView, EditText,
             Button, CheckBox, LP, ViewOnClickListener, Handler, Looper,
             Color, GradientDrawable, Typeface) = classes

            metrics = act.getResources().getDisplayMetrics()
            screen_width = metrics.widthPixels
            screen_height = metrics.heightPixels

            root = LinearLayout(act)
            root.setOrientation(LinearLayout.VERTICAL)
            root.setPadding(30, 20, 30, 20)
            root.setBackgroundColor(Color.parseColor("#F0F4F8"))

            title_view = TextView(act)
            title_view.setText("✉️ 日志面板")
            title_view.setTextSize(18.0)
            title_view.setTypeface(Typeface.DEFAULT_BOLD)
            title_view.setTextColor(Color.parseColor("#2C3E50"))
            title_view.setPadding(0, 0, 0, 12)
            root.addView(title_view, LP(-1, -2))

            scroll = ScrollView(act)
            log_view = TextView(act)
            recent_logs = self._get_recent_logs(100)
            if recent_logs:
                initial_text = recent_logs
            else:
                initial_text = "系统就绪，等待操作...\n"
            log_view.setText(initial_text)
            log_view.setTextSize(13.0)
            log_view.setTypeface(Typeface.MONOSPACE)
            log_view.setTextColor(Color.parseColor("#2C3E50"))
            log_view.setBackgroundColor(Color.parseColor("#F8F9FA"))
            log_view.setPadding(15, 15, 15, 15)
            log_view.setLineSpacing(0, 1.3)
            scroll.addView(log_view, LP(-1, -2))

            log_container = LinearLayout(act)
            log_container.setBackgroundColor(Color.WHITE)
            log_container.addView(scroll, LP(-1, int(screen_height * 0.70)))
            root.addView(log_container, LP(-1, -2))

            close_btn = Button(act)
            close_btn.setText("关闭")
            close_btn.setAllCaps(False)
            close_btn.setTextSize(16.0)
            close_btn.setBackgroundColor(Color.parseColor("#6C63FF"))
            close_btn.setTextColor(Color.WHITE)
            close_btn.setPadding(40, 12, 40, 12)
            gd = GradientDrawable()
            gd.setShape(GradientDrawable.RECTANGLE)
            gd.setCornerRadius(float(self._dp2px(act, 8)))
            gd.setColor(Color.parseColor("#6C63FF"))
            close_btn.setBackgroundDrawable(gd)

            lp = LP(-1, -2)
            lp.setMargins(0, 20, 0, 0)
            root.addView(close_btn, lp)

            dialog = Builder(act).setView(root).create()
            dialog.setCancelable(True)
            from android.content import DialogInterface
            from java import dynamic_proxy
            class DismissListener(dynamic_proxy(DialogInterface.OnDismissListener)):
                def __init__(self, callback):
                    super().__init__()
                    self.callback = callback
                def onDismiss(self, dialog):
                    if self.callback:
                        self.callback()
            dismiss_listener = DismissListener(self._on_log_dismiss)
            self._ui_listeners.append(dismiss_listener)
            dialog.setOnDismissListener(dismiss_listener)
            dialog.show()
            window = dialog.getWindow()
            if window is not None:
                window.setLayout(int(screen_width * 0.92), -2)
            self._active_views = {
                "log": log_view,
                "scroll": scroll,
                "dialog": dialog
            }

            from java import dynamic_proxy
            def bind_click(view_obj, callback):
                class ClickListener(dynamic_proxy(ViewOnClickListener)):
                    def onClick(self, v):
                        try:
                            callback()
                        except Exception:
                            self._push_log(f"❌ UI 点击事件异常:\n{traceback.format_exc()}")
                listener = ClickListener()
                self._ui_listeners.append(listener)
                view_obj.setOnClickListener(listener)

            def do_close():
                try:
                    dialog.dismiss()
                except Exception:
                    pass
                self._log_dialog_open = False
                self._persisted_runnable = None

            bind_click(close_btn, do_close)
            main_handler = Handler(Looper.getMainLooper())
            self._start_log_looper(main_handler)

        self._run_on_ui_log(on_ui)

    def _on_log_dismiss(self):
        self._log_dialog_open = False
        self._persisted_runnable = None
        self._active_views.clear()

    def _run_on_ui_log(self, ui_builder_fn):
        try:
            from java import jclass, dynamic_proxy
            from java.lang import Runnable
            act = self._activity()
            if not act:
                return
            Builder = jclass("android.app.AlertDialog$Builder")
            LinearLayout = jclass("android.widget.LinearLayout")
            ScrollView = jclass("android.widget.ScrollView")
            TextView = jclass("android.widget.TextView")
            EditText = jclass("android.widget.EditText")
            Button = jclass("android.widget.Button")
            CheckBox = jclass("android.widget.CheckBox")
            LP = jclass("android.widget.LinearLayout$LayoutParams")
            ViewOnClickListener = jclass("android.view.View$OnClickListener")
            Handler = jclass("android.os.Handler")
            Looper = jclass("android.os.Looper")
            Color = jclass("android.graphics.Color")
            GradientDrawable = jclass("android.graphics.drawable.GradientDrawable")
            Typeface = jclass("android.graphics.Typeface")
            classes = (Builder, LinearLayout, ScrollView, TextView, EditText,
                       Button, CheckBox, LP, ViewOnClickListener, Handler, Looper,
                       Color, GradientDrawable, Typeface)
            class Run(dynamic_proxy(Runnable)):
                def run(self):
                    ui_builder_fn(act, classes)
            act.getWindow().getDecorView().post(Run())
        except Exception:
            pass

    def _ensure_log_open(self):
        if not self._log_dialog_open:
            self._show_log_dialog()
            time.sleep(0.3)

    def _exec_with_log(self, func, *args, **kwargs):
        self._ensure_log_open()
        try:
            result = func(*args, **kwargs)
            if isinstance(result, str):
                self._log(result)
        except Exception as e:
            self._log(f"执行操作时异常: {e}")

    # ========================= 配置管理 =========================
    def _p(self, d, *keys, default=None):
        for key in keys:
            if key in d:
                return d[key]
        return default

    def _p_bool(self, d, *keys, default=False):
        v = self._p(d, *keys, default=default)
        if isinstance(v, bool):
            return v
        return BOOL_MAP.get(v, bool(v)) if v is not None else default

    def _extract_source_headers(self, item):
        headers = {}
        if not isinstance(item, dict):
            return headers
        h = item.get('header') or item.get('headers')
        if isinstance(h, dict):
            headers.update(h)
        elif isinstance(h, str):
            try:
                headers.update(json.loads(h))
            except Exception:
                pass
        ua = item.get('ua') or item.get('user-agent') or item.get('User-Agent')
        if ua:
            headers['User-Agent'] = ua
        ref = item.get('ref') or item.get('referer') or item.get('Referer')
        if ref:
            headers['Referer'] = ref
        return headers

    def _ensure_headers_with_default(self, headers):
        if not headers:
            headers = {}
        if 'User-Agent' not in headers:
            headers['User-Agent'] = DEFAULT_USER_AGENT
        return headers

    def _parse_url_string(self, input_data):
        base_url = ''
        pic_url = ''
        lives = []
        if '$$$' in input_data:
            parts = input_data.split('$$$', 1)
            base_url = parts[0].strip()
            rest = parts[1].strip()
        else:
            rest = input_data
        if '&&&' in rest:
            parts = rest.split('&&&', 1)
            rest = parts[0].strip()
            pic_url = parts[1].strip()
            if pic_url and not pic_url.startswith(('http://', 'https://')):
                pic_url = base_url + pic_url
        segments = rest.split('#')
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            if '$' in seg:
                name, url = seg.split('$', 1)
                if not url.startswith(('http://', 'https://')):
                    url = base_url + url
                lives.append({'name': name.replace('!!', ''), 'url': url, 'img': pic_url})
            else:
                url = seg
                if not url.startswith(('http://', 'https://')):
                    url = base_url + url
                try:
                    req_headers = self._ensure_headers_with_default({})
                    resp = self.session.get(url, timeout=(10, 30), headers=req_headers)
                    if resp.status_code == 200:
                        data = json.loads(resp.text)
                        path_prefix = url[:url.rfind('/')+1]
                        for item in data:
                            if not isinstance(item, dict):
                                continue
                            name = item.get('name', '').replace('!!', '')
                            item_url = item.get('url', '')
                            if not name or not item_url:
                                continue
                            if not item_url.startswith(('http://', 'https://')):
                                item_url = path_prefix + item_url
                            lives.append({'name': name, 'url': item_url, 'img': pic_url, 'headers': self._extract_source_headers(item)})
                except Exception as e:
                    self._log(f"URL字符串子分类请求失败: {url} - {e}")
        return lives, base_url, pic_url

    def _load_default_config(self):
        default_output = os.path.join(SCRIPT_DIR, "本地包")
        return {
            "sources": [],
            "download_output_dir": default_output,
            "download": {
                "skip_extensions": [".php", ".asp", ".jsp", ".cgi", ".exe", ".dll", ".sh", ".bat"],
                "skip_patterns": [],
                "max_file_size_mb": 100,
                "recursive_depth": 2,
                "decrypt": {"enabled": True, "external_api_url": DEFAULT_EXTERNAL_API_URL},
                "overwrite": False,
                "timeout_connect": 10,
                "timeout_read": 60,
                "chunk_size": 8192,
                "max_workers": 8,
                "retry_total": 2,
                "retry_backoff": 0.3,
                "pool_connections": 10,
                "pool_maxsize": 20,
                "category_map": {"js": ".js", "lib": ".json", "py": ".py", "jar": ".jar"},
                "skip_patterns_core": [
                    r"/api\.php/provide/vod",
                    r"/api\.php/app/",
                    r"provide/vod",
                    r"\?url=",
                    r"\{name\}",
                    r"\{date\}",
                    r"\{episode\}",
                    r"proxy://",
                ]
            },
            "proxy": "",
            "github_proxy": GITHUB_PROXY,
            "concurrent": 3,
            "user_agent": DEFAULT_USER_AGENT,
            "external_api_url": DEFAULT_EXTERNAL_API_URL,
            "log": {
                "enabled": True,
                "level": "debug",
                "dir": os.path.join(default_output, "log")
            }
        }

    def _normalize_config_keys(self, obj):
        if isinstance(obj, dict):
            new_obj = {}
            key_map = {
                '下载目录': 'download_output_dir',
                '全局代理': 'proxy',
                '并发数': 'concurrent',
                '跳过扩展名': 'skip_extensions',
                '跳过模式': 'skip_patterns',
                '最大文件大小MB': 'max_file_size_mb',
                '递归深度': 'recursive_depth',
                '覆盖': 'overwrite',
                '连接超时': 'timeout_connect',
                '读取超时': 'timeout_read',
                '块大小': 'chunk_size',
                '解密': 'decrypt',
                '启用': 'enabled',
                '外部API地址': 'external_api_url',
                '源列表': 'sources',
                '站点': 'sources',
                'github代理': 'github_proxy',
                '启用日志': 'log_enabled',
                '日志级别': 'log_level',
                '日志目录': 'log_dir',
            }
            for k, v in obj.items():
                new_key = key_map.get(k, k)
                new_obj[new_key] = self._normalize_config_keys(v)
            return new_obj
        elif isinstance(obj, list):
            return [self._normalize_config_keys(item) for item in obj]
        else:
            return obj

    def _load_config_from_ext(self, extend):
        if not extend:
            return None
        extend_str = str(extend).strip()
        if extend_str.startswith('{') or extend_str.startswith('['):
            try:
                return json.loads(extend_str)
            except Exception:
                return None
        else:
            return self._load_config_file(extend_str)

    def _apply_config(self, config):
        config = self._normalize_config_keys(config)
        self.config = config
        raw_sources = config.get('sources') or config.get('urls', [])
        self.package_download_sites = []
        for item in raw_sources:
            if isinstance(item, dict) and item.get('url'):
                site = {
                    "id": self._package_download_site_id(item.get('name', '未命名'), item['url']),
                    "name": item.get('name', '未命名'),
                    "url": item['url'],
                    "enabled": item.get('enabled', True),
                    "type": "json"
                }
                self.package_download_sites.append(site)
            elif isinstance(item, str):
                site = {
                    "id": self._package_download_site_id(item, item),
                    "name": item,
                    "url": item,
                    "enabled": True,
                    "type": "json"
                }
                self.package_download_sites.append(site)
        self.download_output_dir = config.get('download_output_dir') or config.get('下载目录', '')
        if not self.download_output_dir:
            self.download_output_dir = os.path.join(SCRIPT_DIR, "本地包")
        os.makedirs(self.download_output_dir, exist_ok=True)

        default_download = self._load_default_config()['download']
        user_download = config.get('download', {})
        self.download_config = copy.deepcopy(default_download)
        for k, v in user_download.items():
            if isinstance(v, dict) and k in self.download_config and isinstance(self.download_config[k], dict):
                self.download_config[k].update(v)
            else:
                self.download_config[k] = v
        if config.get('proxy'):
            self.download_config['proxy'] = config['proxy']
        if config.get('github_proxy'):
            self.download_config['github_proxy'] = config['github_proxy']
        if config.get('concurrent'):
            self.download_config['concurrent'] = config['concurrent']

        for site in self.package_download_sites:
            self._init_site_state(site['id'])

        self.user_agent = config.get('user_agent', DEFAULT_USER_AGENT)
        self.category_map = self.download_config.get('category_map', {'js': '.js', 'lib': '.json', 'py': '.py', 'jar': '.jar'})
        self.skip_patterns_core = self.download_config.get('skip_patterns_core', SKIP_PATTERNS)
        self.max_workers = self.download_config.get('max_workers', 8)
        self.retry_total = self.download_config.get('retry_total', 2)
        self.retry_backoff = self.download_config.get('retry_backoff', 0.3)
        self.pool_connections = self.download_config.get('pool_connections', 10)
        self.pool_maxsize = self.download_config.get('pool_maxsize', 20)

        self.external_api_url = (
            self.config.get('external_api_url')
            or self.config.get('decrypt', {}).get('external_api_url')
            or self.download_config.get('decrypt', {}).get('external_api_url', DEFAULT_EXTERNAL_API_URL)
        )
        log_cfg = self.config.get('log', {})
        self.log_enabled = log_cfg.get('enabled', self.config.get('log_enabled', True))
        self.log_level = log_cfg.get('level', self.config.get('log_level', 'debug'))
        self.log_dir = log_cfg.get('dir', self.config.get('log_dir', os.path.join(self.download_output_dir, 'log')))
        self.config['log'] = {'enabled': self.log_enabled, 'level': self.log_level, 'dir': self.log_dir}
        if self._session is not None:
            self.session = self._session

        if 'config_file' in config:
            self._config_file_path = config['config_file']
        else:
            self._config_file_path = self.config.get('config_file')

    def _save_config_to_file(self, path=None):
        if path is None:
            path = os.path.join(SCRIPT_DIR, 'config.json')
        config = {
            "sources": [
                {"name": site['name'], "url": site['url'], "enabled": site.get('enabled', True)}
                for site in self.package_download_sites
            ],
            "download_output_dir": self.download_output_dir,
            "download": self.download_config,
            "proxy": self.download_config.get('proxy', ''),
            "github_proxy": self.download_config.get('github_proxy', GITHUB_PROXY),
            "concurrent": self.download_config.get('concurrent', 3),
            "user_agent": getattr(self, 'user_agent', DEFAULT_USER_AGENT),
            "external_api_url": getattr(self, 'external_api_url', DEFAULT_EXTERNAL_API_URL),
            "log": {
                "enabled": getattr(self, 'log_enabled', True),
                "level": getattr(self, 'log_level', 'info'),
                "dir": getattr(self, 'log_dir', os.path.join(self.download_output_dir, 'log'))
            }
        }
        temp = path + ".tmp"
        with open(temp, 'w', encoding='utf-8') as f_local:
            json.dump(config, f_local, ensure_ascii=False, indent=2)
        os.replace(temp, path)
        self._save_persistent_config()

    def _save_persistent_config(self):
        try:
            os.makedirs(os.path.dirname(PERSISTENT_CONFIG_PATH), exist_ok=True)
            config = {
                "sources": [
                    {"name": site['name'], "url": site['url'], "enabled": site.get('enabled', True)}
                    for site in self.package_download_sites
                ],
                "download_output_dir": self.download_output_dir,
                "download": self.download_config,
                "proxy": self.download_config.get('proxy', ''),
                "github_proxy": self.download_config.get('github_proxy', GITHUB_PROXY),
                "concurrent": self.download_config.get('concurrent', 3),
                "user_agent": getattr(self, 'user_agent', DEFAULT_USER_AGENT),
                "external_api_url": getattr(self, 'external_api_url', DEFAULT_EXTERNAL_API_URL),
                "log": {
                    "enabled": getattr(self, 'log_enabled', True),
                    "level": getattr(self, 'log_level', 'info'),
                    "dir": getattr(self, 'log_dir', os.path.join(self.download_output_dir, 'log'))
                }
            }
            with open(PERSISTENT_CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self._log(f"配置已持久化: {PERSISTENT_CONFIG_PATH}")
        except Exception as e:
            self._log(f"持久化配置失败: {e}")

    def _load_persistent_config(self):
        if not os.path.exists(PERSISTENT_CONFIG_PATH):
            return None
        try:
            with open(PERSISTENT_CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self._log(f"加载持久化配置失败: {e}")
            return None

    def _restore_default_config(self):
        try:
            if os.path.exists(CACHE_DIR):
                shutil.rmtree(CACHE_DIR, ignore_errors=True)
            os.makedirs(CACHE_DIR, exist_ok=True)
            if os.path.exists(PERSISTENT_CONFIG_PATH):
                os.remove(PERSISTENT_CONFIG_PATH)
            self._log("已清除缓存和持久化配置")

            self._site_states.clear()
            self._site_op_threads.clear()
            self._site_cancel_events.clear()
            self._package_download_state = "idle"
            self._package_download_message = ""
            self._package_download_thread = None
            self._package_cancel_event = None
            self._is_downloading = False

            if self._initial_extend is not None:
                self._log("重新加载初始配置...")
                self.inited = False
                self.init(self._initial_extend)
                self._log("✅ 已恢复初始配置")
                return "已恢复初始配置"
            else:
                self._log("未找到初始配置，使用默认配置")
                self.config = self._load_default_config()
                self._apply_config(self.config)
                self._save_config_to_file()
                self._save_persistent_config()
                self._log("✅ 配置已恢复为内置默认值")
                return "配置已恢复为内置默认值"
        except Exception as e:
            self._log(f"恢复初始配置失败: {e}")
            return f"恢复失败: {e}"

    def _update_config_value(self, key_path, value, raw=False):
        try:
            keys = key_path.split('.')
            target = self.config
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            self._save_config_to_file()
            self._save_persistent_config()
            self._log(f"配置已更新: {key_path} = {value}")
        except Exception as e:
            self._log(f"配置更新失败: {e}")
            raise

    # ========================= 单站点操作 =========================
    def _absolutize_urls(self, obj, base_url):
        if isinstance(obj, dict):
            return {k: self._absolutize_urls(v, base_url) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._absolutize_urls(item, base_url) for item in obj]
        elif isinstance(obj, str):
            if obj.startswith(('http://', 'https://')):
                return obj
            if obj.startswith(('./', '../', '/')):
                return urllib.parse.urljoin(base_url, obj)
            return obj
        else:
            return obj

    def _decrypt_single_site(self, site_id):
        site = None
        for s in self.package_download_sites:
            if s['id'] == site_id:
                site = s
                break
        if not site:
            return "站点不存在"
        with self._site_op_lock:
            if site_id in self._site_op_threads and self._site_op_threads[site_id].is_alive():
                return "该站点正在处理中"
            self._init_site_state(site_id)
            self._site_states[site_id]['decrypt_status'] = 'processing'
            self._site_states[site_id]['decrypt_msg'] = '正在解密...'
            cancel_event = threading.Event()
            self._site_cancel_events[site_id] = cancel_event

        def _worker():
            try:
                name = site['name']
                url = site['url']
                self._log(f"【解密】开始处理 {name} ({url})")
                download_cfg = copy.deepcopy(self.download_config)
                download_cfg['base_url'] = self._get_base_url(url)
                download_cfg['github_proxy'] = self.config.get('github_proxy', GITHUB_PROXY)
                download_cfg['user_agent'] = self.user_agent
                downloader = FileDownloader(self.download_output_dir, download_cfg, log_callback=self._log,
                                            cancel_event=cancel_event)
                content = downloader.download_text(url, self._get_base_url(url), force_decrypt=True)
                if cancel_event.is_set():
                    self._site_states[site_id]['decrypt_status'] = 'idle'
                    self._site_states[site_id]['decrypt_msg'] = '已取消'
                    self._log(f"【解密】{name} 已取消")
                    return
                if not content:
                    self._site_states[site_id]['decrypt_status'] = 'error'
                    self._site_states[site_id]['decrypt_msg'] = '下载失败'
                    self._log(f"【解密】{name} 下载失败")
                    return
                try:
                    data = json.loads(content)
                    is_json = True
                except Exception:
                    is_json = False
                base_url = self._get_base_url(url)
                safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)
                output_dir = os.path.join(self.download_output_dir, safe_name)
                os.makedirs(output_dir, exist_ok=True)
                dec_path = os.path.join(output_dir, 'box_decrypted.json')
                if is_json:
                    data = self._absolutize_urls(data, base_url)
                    with open(dec_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    self._site_states[site_id]['decrypt_status'] = 'success'
                    self._site_states[site_id]['decrypt_msg'] = '明文JSON已保存'
                    self._site_states[site_id]['decrypt_result'] = dec_path
                    self._log(f"【解密】{name} 为明文JSON，已保存")
                else:
                    dec = try_decrypt_content(content, url, self.external_api_url, self._session, max_rounds=5)
                    if dec:
                        try:
                            data = json.loads(dec)
                            data = self._absolutize_urls(data, base_url)
                            with open(dec_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=2)
                            self._site_states[site_id]['decrypt_status'] = 'success'
                            self._site_states[site_id]['decrypt_msg'] = '解密成功'
                            self._site_states[site_id]['decrypt_result'] = dec_path
                            self._log(f"【解密】{name} 解密成功，已保存")
                        except Exception:
                            with open(dec_path, 'w', encoding='utf-8') as f:
                                f.write(dec)
                            self._site_states[site_id]['decrypt_status'] = 'success'
                            self._site_states[site_id]['decrypt_msg'] = '解密成功(非JSON)'
                            self._site_states[site_id]['decrypt_result'] = dec_path
                            self._log(f"【解密】{name} 解密成功（非标准JSON，已保存原文）")
                    else:
                        self._site_states[site_id]['decrypt_status'] = 'error'
                        self._site_states[site_id]['decrypt_msg'] = '解密失败'
                        self._log(f"【解密】{name} 解密失败")
            except Exception as e:
                self._site_states[site_id]['decrypt_status'] = 'error'
                self._site_states[site_id]['decrypt_msg'] = f'异常: {str(e)[:30]}'
                self._log(f"【解密】异常: {e}")
            finally:
                with self._site_op_lock:
                    self._site_op_threads.pop(site_id, None)
                    if site_id in self._site_cancel_events:
                        del self._site_cancel_events[site_id]

        t = threading.Thread(target=_worker, daemon=True)
        with self._site_op_lock:
            self._site_op_threads[site_id] = t
        t.start()
        return "已开始解密任务"

    def _localize_single_site(self, site_id):
        site = None
        for s in self.package_download_sites:
            if s['id'] == site_id:
                site = s
                break
        if not site:
            return "站点不存在"
        with self._site_op_lock:
            if site_id in self._site_op_threads and self._site_op_threads[site_id].is_alive():
                return "该站点正在处理中"
            self._init_site_state(site_id)
            self._site_states[site_id]['localize_status'] = 'processing'
            self._site_states[site_id]['localize_msg'] = '正在转换...'
            cancel_event = threading.Event()
            self._site_cancel_events[site_id] = cancel_event

        def _worker():
            try:
                stats = self._process_json_source(site, cancel_event)
                if cancel_event.is_set():
                    self._site_states[site_id]['localize_status'] = 'idle'
                    self._site_states[site_id]['localize_msg'] = '已取消'
                    self._log(f"【本地化】{site['name']} 已取消")
                    return
                self._site_states[site_id]['localize_status'] = 'success'
                self._site_states[site_id]['localize_msg'] = f"下载{stats['downloaded']}个文件"
                self._site_states[site_id]['localize_result'] = stats.get('box_path')
                self._log(f"【本地化】{site['name']} 完成，下载 {stats['downloaded']} 个文件")
            except Exception as e:
                self._site_states[site_id]['localize_status'] = 'error'
                self._site_states[site_id]['localize_msg'] = f'失败: {str(e)[:30]}'
                self._log(f"【本地化】{site['name']} 失败: {e}")
            finally:
                with self._site_op_lock:
                    self._site_op_threads.pop(site_id, None)
                    if site_id in self._site_cancel_events:
                        del self._site_cancel_events[site_id]

        t = threading.Thread(target=_worker, daemon=True)
        with self._site_op_lock:
            self._site_op_threads[site_id] = t
        t.start()
        return "已开始本地化任务"

    def _apply_single_site(self, site_id):
        site = None
        for s in self.package_download_sites:
            if s['id'] == site_id:
                site = s
                break
        if not site:
            return "站点不存在"
        self._init_site_state(site_id)
        self._site_states[site_id]['apply_status'] = 'idle'
        self._site_states[site_id]['apply_msg'] = '功能开发中'
        self._log(f"【应用】{site['name']} 应用功能尚未实现（占位）")
        return "应用功能开发中，敬请期待"

    def _decrypt_sites(self, sites):
        if not sites:
            return "没有选择任何站点"
        count = 0
        for site in sites:
            self._decrypt_single_site(site['id'])
            count += 1
        return f"已开始解密 {count} 个站点"

    def _localize_sites(self, sites):
        if not sites:
            return "没有选择任何站点"
        count = 0
        for site in sites:
            self._localize_single_site(site['id'])
            count += 1
        return f"已开始本地化 {count} 个站点"

    def _package_download_site_id(self, name, url):
        payload = "{}\0{}".format(str(name or ""), str(url or ""))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def _enabled_package_download_sites(self):
        return [s for s in self.package_download_sites if s.get("enabled", True)]

    def _normalize_package_download_name(self, name):
        name = re.sub(r"[\x00-\x1f]+", " ", str(name or "")).strip()
        name = re.sub(r"\s+", " ", name)
        if not name:
            raise ValueError("备注名不能为空")
        if name in (".", "..") or re.search(r'[\\/:*?"<>|]', name):
            raise ValueError("备注名包含非法字符")
        if len(name) > 40:
            raise ValueError("备注名不能超过40个字符")
        return name

    def _normalize_package_download_url(self, url):
        url = str(url or "").strip().strip('"').strip("'")
        if not url:
            raise ValueError("下载地址不能为空")
        if len(url) > 2048:
            raise ValueError("下载地址过长")
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
            raise ValueError("下载地址必须是 http 或 https URL")
        return url

    def _add_or_update_package_download_site(self, name, url):
        clean_name = self._normalize_package_download_name(name)
        clean_url = self._normalize_package_download_url(url)
        name_match = None
        url_match = None
        for item in self.package_download_sites:
            if str(item.get("name", "")).casefold() == clean_name.casefold():
                name_match = item
            if str(item.get("url", "")).casefold() == clean_url.casefold():
                url_match = item
        if name_match is not None and url_match is not None and name_match is not url_match:
            raise ValueError("备注名和网址分别属于两个已有站点")
        target = name_match or url_match
        created = target is None
        if created:
            if len(self.package_download_sites) >= 50:
                raise ValueError("下载站点最多保存50个")
            target = {
                "id": self._package_download_site_id(clean_name, clean_url),
                "name": clean_name,
                "url": clean_url,
                "enabled": True,
                "type": "json",
            }
            self.package_download_sites.append(target)
        else:
            target["name"] = clean_name
            target["url"] = clean_url
            target["type"] = "json"
        self._save_config_to_file()
        return dict(target), created

    def _set_package_download_site_states(self, states):
        if not isinstance(states, dict):
            raise ValueError("数据无效")
        changed = False
        for item in self.package_download_sites:
            sid = str(item.get("id", ""))
            if sid in states:
                enabled = bool(states[sid])
                if bool(item.get("enabled", True)) != enabled:
                    item["enabled"] = enabled
                    changed = True
        if changed:
            self._save_config_to_file()
        return changed

    def _delete_package_download_sites(self, site_ids):
        selected = {str(s).strip() for s in site_ids if str(s).strip()}
        if not selected:
            raise ValueError("请选择要删除的下载站点")
        existing = {str(item.get("id", "")).strip() for item in self.package_download_sites}
        matched = selected & existing
        if not matched:
            raise ValueError("选择的下载站点已不存在")
        if len(self.package_download_sites) - len(matched) < 1:
            raise ValueError("至少保留一个下载站点")
        removed = [item for item in self.package_download_sites if str(item.get("id", "")).strip() in matched]
        self.package_download_sites = [item for item in self.package_download_sites if str(item.get("id", "")).strip() not in matched]
        self._save_config_to_file()
        return removed

    # ========================= 核心下载逻辑 =========================
    def _guess_category(self, url, field_key=None):
        if field_key in ('spider', 'jar'):
            return 'jar'
        path_part = url.split('?')[0].split(';')[0].rstrip('/')
        ext = os.path.splitext(path_part)[1].lower()
        if ext == '.jar':
            return 'jar'
        elif ext == '.py':
            return 'py'
        elif ext == '.js':
            return 'js'
        else:
            return 'lib'

    def _walk_and_collect(self, obj, base_url, result, field_key=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_field = k if k in ('spider', 'jar') else field_key
                if isinstance(v, str):
                    stripped = v.strip()
                    if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('[') and stripped.endswith(']')):
                        try:
                            parsed = json.loads(stripped)
                            self._walk_and_collect(parsed, base_url, result, new_field)
                            continue
                        except json.JSONDecodeError:
                            pass
                    parts = [p.strip() for p in v.split('$$')]
                    for part in parts:
                        result.add((part, base_url, new_field))
                elif isinstance(v, (dict, list)):
                    self._walk_and_collect(v, base_url, result, new_field)
        elif isinstance(obj, list):
            for item in obj:
                self._walk_and_collect(item, base_url, result, field_key)

    def _collect_files(self, data, base_url, downloader):
        all_items = set()
        self._walk_and_collect(data, base_url, all_items)
        max_depth = self.download_config.get('recursive_depth', 2)
        current_depth = 0
        processed_jsons = set()
        while current_depth < max_depth:
            json_items = [(u, b, fk) for u, b, fk in all_items
                          if u.split('?')[0].split(';')[0].lower().endswith('.json')]
            new_items = set()
            for url, url_base, field_key in json_items:
                if url in processed_jsons:
                    continue
                if not downloader.is_downloadable(url, field_key):
                    continue
                processed_jsons.add(url)
                content = downloader.download_text(url, url_base, force_decrypt=False)
                if content:
                    try:
                        sub_data = json.loads(content)
                        if url.startswith(('http://', 'https://')):
                            parsed = urllib.parse.urlparse(url)
                            sub_base = f"{parsed.scheme}://{parsed.netloc}{os.path.dirname(parsed.path)}/"
                        else:
                            sub_base = url_base
                        self._walk_and_collect(sub_data, sub_base, new_items)
                    except Exception:
                        pass
            if not new_items:
                break
            all_items.update(new_items)
            current_depth += 1
        unique = []
        seen = set()
        for url, url_base, field_key in all_items:
            if url in seen:
                continue
            seen.add(url)
            if downloader.is_downloadable(url, field_key):
                cat = self._guess_category(url, field_key)
                unique.append((url, cat, url_base, field_key))
        return unique

    def _parse_box_json(self, url, downloader):
        base_url = self._get_base_url(url)
        self._log(f"开始下载并解析接口: {url}")
        content = downloader.download_text(url, base_url, force_decrypt=True)
        if not content:
            self._log("下载内容为空")
            return None, None, "下载失败或内容为空"
        try:
            data = json.loads(content)
            self._log("成功解析 JSON")
            return data, base_url, None
        except json.JSONDecodeError as e:
            self._log(f"JSON 解析失败: {e}, 尝试提取片段...")
        json_pattern = r'(\{[\s\S]*\}|\[[\s\S]*\])'
        matches = re.findall(json_pattern, content)
        for candidate in matches:
            try:
                data = json.loads(candidate)
                self._log("从提取的片段成功解析 JSON")
                return data, base_url, None
            except Exception:
                continue
        decrypted = try_decrypt_content(content, url, self.external_api_url, self._session, max_rounds=5)
        if decrypted:
            self._log("解密成功，尝试解析")
            try:
                data = json.loads(decrypted)
                return data, base_url, None
            except Exception:
                matches2 = re.findall(json_pattern, decrypted)
                for candidate in matches2:
                    try:
                        data = json.loads(candidate)
                        return data, base_url, None
                    except Exception:
                        continue
                self._log("解密后仍无法解析为 JSON")
        self._log("所有解析尝试均失败")
        return None, None, "无法解析为 JSON"

    def _download_all(self, paths, downloader):
        total = len(paths)
        if total == 0:
            return
        completed = [0]
        lock = threading.Lock()
        last_progress_time = [time.time()]

        def progress_wrapper(url, cat, base_url, field_key=None):
            if downloader.cancel_event and downloader.cancel_event.is_set():
                return None
            result = downloader.download_file(url, base_url, cat, field_key)
            with lock:
                completed[0] += 1
                now = time.time()
                if now - last_progress_time[0] > 1.0 or completed[0] == total:
                    pct = (completed[0] / total) * 100
                    self._push_log(f"⏳ 总进度 {completed[0]}/{total} ({pct:.1f}%) | 当前: {os.path.basename(url)[:30]}")
                    last_progress_time[0] = now
            return result

        max_workers = min(self.max_workers, max(1, len(paths)))
        self._push_log(f"🚀 启动 {max_workers} 线程并发下载，共 {total} 个文件...")
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(progress_wrapper, url, cat, base_url, field_key): (url, cat)
                       for url, cat, base_url, field_key in paths}
            for fut in as_completed(futures):
                if downloader.cancel_event and downloader.cancel_event.is_set():
                    ex.shutdown(wait=False)
                    break
        self._push_log(f"✅ 批量下载完成 {completed[0]}/{total}")

    def _find_local_path(self, url, downloader):
        if not url or not isinstance(url, str):
            return None
        url_part, suffix = downloader.split_url_and_suffix(url)

        if url_part in downloader.downloaded:
            return './' + downloader.downloaded[url_part].replace('\\', '/') + suffix

        variants = set()
        normalized = downloader.normalize_github_url(url_part)
        variants.add(normalized)

        if downloader.github_proxy:
            proxy = downloader.github_proxy.rstrip('/') + '/'
            if url_part.startswith(proxy):
                raw = url_part[len(proxy):]
                variants.add(raw)
                if raw.startswith('raw.githubusercontent.com/'):
                    variants.add('https://' + raw)

        for variant in variants:
            if variant != url_part and variant in downloader.downloaded:
                return './' + downloader.downloaded[variant].replace('\\', '/') + suffix

        return None

    def _collect_missing_files(self, data, downloader):
        all_items = set()
        self._walk_and_collect(data, "", all_items)
        missing = []
        seen = set()
        for url, _, field_key in all_items:
            if url in seen:
                continue
            seen.add(url)
            if not downloader.is_downloadable(url, field_key):
                continue
            url_part, _ = downloader.split_url_and_suffix(url)
            if url_part in downloader.downloaded:
                continue
            found = False
            variants = [downloader.normalize_github_url(url_part)]
            if downloader.github_proxy:
                proxy = downloader.github_proxy.rstrip('/') + '/'
                if url_part.startswith(proxy):
                    variants.append(url_part[len(proxy):])
            for v in variants:
                if v in downloader.downloaded:
                    found = True
                    break
            if found:
                continue
            cat = self._guess_category(url, field_key)
            missing.append((url, cat, "", field_key))
        return missing

    def _generate_local_box(self, data, source_name, output_dir, downloader):
        import json

        def localize(obj):
            if isinstance(obj, dict):
                result = {}
                for k, v in obj.items():
                    result[k] = localize(v)
                return result
            elif isinstance(obj, list):
                return [localize(item) for item in obj]
            elif isinstance(obj, str):
                stripped = obj.strip()
                if (stripped.startswith('{') and stripped.endswith('}')) or (stripped.startswith('[') and stripped.endswith(']')):
                    try:
                        parsed = json.loads(stripped)
                        replaced = localize(parsed)
                        return json.dumps(replaced, ensure_ascii=False, separators=(',', ':'))
                    except json.JSONDecodeError:
                        pass
                local_path = self._find_local_path(obj, downloader)
                if local_path:
                    return local_path
                return obj
            else:
                return obj

        local_data = localize(data)
        local_data['warningText'] = f"本地包生成于 {time.strftime('%Y-%m-%d %H:%M:%S')} | 源: {source_name}"
        box_path = os.path.join(output_dir, 'box.json')
        with open(box_path, 'w', encoding='utf-8') as f_local:
            json.dump(local_data, f_local, ensure_ascii=False, indent=2)
        return box_path

    def _process_json_source(self, site, cancel_event=None):
        name = site.get("name", "未命名")
        url = site.get("url", "")
        if not url:
            raise ValueError("站点URL为空")
        safe_name = re.sub(r'[\\/:*?"<>|]', '_', name)
        output_dir = os.path.join(self.download_output_dir, safe_name)
        os.makedirs(output_dir, exist_ok=True)
        download_cfg = copy.deepcopy(self.download_config)
        download_cfg['base_url'] = self._get_base_url(url)
        download_cfg['github_proxy'] = self.config.get('github_proxy', GITHUB_PROXY)
        download_cfg['user_agent'] = self.user_agent
        downloader = FileDownloader(output_dir, download_cfg, log_callback=self._log, progress_callback=self._push_log,
                                    cancel_event=cancel_event)
        self._package_download_message = f"正在解析 {name} ..."
        self._push_log(f"🎯 开始处理站点: {name}")
        data, base_url, error = self._parse_box_json(url, downloader)
        if error:
            raise Exception(f"解析失败: {error}")
        paths = self._collect_files(data, base_url, downloader)
        self._package_download_message = f"正在下载 {len(paths)} 个文件 ..."
        self._push_log(f"❤️️ 收集到 {len(paths)} 个可下载文件，开始并发下载...")
        self._download_all(paths, downloader)

        missing = self._collect_missing_files(data, downloader)
        if missing:
            self._push_log(f"🔄 发现 {len(missing)} 个遗漏文件，补充下载...")
            self._download_all(missing, downloader)

        self._push_log(f"🧩 正在生成本地化 box.json...")
        local_box_path = self._generate_local_box(data, name, output_dir, downloader)
        self._push_log(f"🎉 站点 {name} 处理完成！输出: {local_box_path}")
        stats = {
            "downloaded": len(downloader.downloaded),
            "failed": len(downloader.failed),
            "skipped": len(downloader.skipped),
            "output_dir": output_dir,
            "box_path": local_box_path,
        }
        return stats

    def _get_base_url(self, url):
        parsed = urllib.parse.urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}{os.path.dirname(parsed.path)}/"
        if not base.endswith('/'):
            base += '/'
        return base

    def _start_package_download(self, sites=None):
        if sites is None:
            sites = self._enabled_package_download_sites()
        if not sites:
            return False, "没有选择任何站点"
        with self._package_download_lock:
            if self._package_download_thread and self._package_download_thread.is_alive():
                return False, "正在下载中"
            names = "、".join(s.get("name", "本地包") for s in sites)
            self._package_download_state = "queued"
            self._package_download_message = "已加入批量任务：{}".format(names)
            self._package_cancel_event = threading.Event()
            worker = threading.Thread(target=self._package_download_worker, args=(sites, self._package_cancel_event), daemon=True)
            self._package_download_thread = worker
            worker.start()
        return True, "开始下载 {} 个已选站点".format(len(sites))

    def _package_download_worker(self, sites, cancel_event):
        successes = []
        failures = []
        used_names = set()
        try:
            total = len(sites)
            for idx, site in enumerate(sites, 1):
                if cancel_event.is_set():
                    self._log("批量下载已取消")
                    break
                name = site.get("name", "本地包")
                url = site.get("url", "")
                try:
                    self._package_download_state = "processing"
                    self._package_download_message = "正在转换 {}/{}：{}".format(idx, total, name)
                    self._push_log(f"🚀 [{idx}/{total}] 开始处理站点: {name}")
                    package_name = self._normalize_package_download_name(name)
                    if package_name.casefold() in used_names:
                        raise ValueError("下载站点备注名重复: {}".format(name))
                    used_names.add(package_name.casefold())
                    stats = self._process_json_source(site, cancel_event)
                    if cancel_event.is_set():
                        self._log("批量下载已取消")
                        break
                    successes.append({"name": name, "url": url, "result": stats})
                    self._log(f"站点 {name} 处理成功，下载 {stats.get('downloaded',0)} 个文件")
                except Exception as e:
                    self._log(f"站点 {name} 处理失败: {e}")
                    failures.append({"name": name, "error": str(e)})
            if cancel_event.is_set():
                msg = "批量下载已被用户取消"
                self._package_download_state = "idle"
                self._package_download_message = msg
                self._log(msg)
                self._notify_app(msg)
                return
            if not successes:
                raise ValueError("没有站点处理成功")
            total_files = sum(item["result"].get("downloaded", 0) for item in successes)
            fail_detail = "；".join("{}: {}".format(f["name"], f["error"]) for f in failures)
            msg = "批量处理完成：成功 {}/{}，共 {} 个文件；{}{}".format(
                len(successes), len(sites), total_files,
                "失败 {} 个（{}）；".format(len(failures), fail_detail) if failures else "",
                "（已通知）"
            )
            self._package_download_state = "partial" if failures else "success"
            self._package_download_message = msg
            self._log(msg)
            self._notify_app(msg)
        except Exception as e:
            msg = "批量处理失败: {}".format(e)
            self._package_download_state = "error"
            self._package_download_message = msg
            self._log(msg)
            self._notify_app(msg)
        finally:
            with self._package_download_lock:
                self._package_download_thread = None
                self._package_cancel_event = None

    def _copy_to_clipboard(self, text, toast_msg="已复制"):
        try:
            act = self._activity()
            if not act:
                return
            clipboard = act.getSystemService(act.CLIPBOARD_SERVICE)
            from java import jclass
            ClipData = jclass("android.content.ClipData")
            clip = ClipData.newPlainText("复制", text)
            clipboard.setPrimaryClip(clip)
            Toast = jclass("android.widget.Toast")
            Toast.makeText(act, toast_msg, Toast.LENGTH_SHORT).show()
        except Exception as e:
            self._log(f"复制失败: {e}")

    # ========================= 设置对话框 =========================
    def _open_package_download_url_dialog(self):
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            container = LinearLayout(act)
            container.setOrientation(LinearLayout.VERTICAL)

            desc = TextView(act)
            desc.setText("输入备注名和 box.json 网址")
            desc.setTextSize(14.0)
            desc.setTypeface(Typeface.DEFAULT)
            desc.setTextColor(Color.parseColor("#7F8C8D"))
            desc.setPadding(0, 0, 0, self._dp2px(act, 10))
            container.addView(desc, LP(-1, -2))

            name_edit = EditText(act)
            name_edit.setSingleLine(True)
            name_edit.setHint("备注名")
            name_edit.setHintTextColor(Color.parseColor("#A0AEC0"))
            name_edit.setPadding(self._dp2px(act, 12), self._dp2px(act, 10),
                                self._dp2px(act, 12), self._dp2px(act, 10))
            name_edit.setTextSize(15.0)
            name_edit.setTypeface(Typeface.DEFAULT)
            name_edit.setTextColor(Color.parseColor("#2C3E50"))
            bg = GradientDrawable()
            bg.setShape(GradientDrawable.RECTANGLE)
            bg.setCornerRadius(float(self._dp2px(act, 6)))
            bg.setColor(Color.parseColor("#F8F9FA"))
            bg.setStroke(1, Color.parseColor("#E2E8F0"))
            name_edit.setBackgroundDrawable(bg)
            container.addView(name_edit, LP(-1, -2))

            url_edit = EditText(act)
            url_edit.setSingleLine(True)
            url_edit.setHint("https://example.com/box.json")
            url_edit.setHintTextColor(Color.parseColor("#A0AEC0"))
            url_edit.setPadding(self._dp2px(act, 12), self._dp2px(act, 10),
                               self._dp2px(act, 12), self._dp2px(act, 10))
            url_edit.setTextSize(15.0)
            url_edit.setTypeface(Typeface.DEFAULT)
            url_edit.setTextColor(Color.parseColor("#2C3E50"))
            url_edit.setBackgroundDrawable(bg)
            container.addView(url_edit, LP(-1, -2))

            def save():
                try:
                    name = str(name_edit.getText().toString())
                    url = str(url_edit.getText().toString())
                    with self.lock:
                        saved, created = self._add_or_update_package_download_site(name, url)
                    Toast.makeText(act, "已{}下载站点：{}".format("添加" if created else "更新", saved["name"]), Toast.LENGTH_LONG).show()
                except Exception as exc:
                    Toast.makeText(act, "保存失败: {}".format(exc), Toast.LENGTH_LONG).show()

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "添加/更新", "color": "#6C63FF", "callback": save, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               "添加在线源网址", container, buttons)
            if dialog:
                dialog.show()
                name_edit.requestFocus()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _open_package_download_delete_dialog(self):
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            container = LinearLayout(act)
            container.setOrientation(LinearLayout.VERTICAL)

            desc = TextView(act)
            desc.setText("选择要删除的在线网址（只删除设置，不删除本地包）")
            desc.setTextSize(14.0)
            desc.setTypeface(Typeface.DEFAULT)
            desc.setTextColor(Color.parseColor("#7F8C8D"))
            desc.setPadding(0, 0, 0, self._dp2px(act, 10))
            container.addView(desc, LP(-1, -2))

            switches = {}
            for site in self.package_download_sites:
                sw = Switch(act)
                sw.setText("{} · {}".format(site.get("name", "未命名"), site.get("url", "")))
                sw.setTextSize(14.0)
                sw.setTypeface(Typeface.DEFAULT)
                sw.setTextColor(Color.parseColor("#2C3E50"))
                sw.setChecked(False)
                sw.setPadding(0, self._dp2px(act, 6), 0, self._dp2px(act, 6))
                container.addView(sw, LP(-1, -2))
                switches[str(site.get("id", ""))] = sw

            scroll = ScrollView(act)
            scroll.addView(container, LP(-1, -2))

            def do_delete():
                selected = [sid for sid, ctrl in switches.items() if ctrl.isChecked()]
                try:
                    with self.lock:
                        removed = self._delete_package_download_sites(selected)
                    names = "、".join(str(item.get("name", "未命名")) for item in removed)
                    Toast.makeText(act, "已删除在线网址：{}".format(names), Toast.LENGTH_LONG).show()
                except Exception as exc:
                    Toast.makeText(act, "删除失败: {}".format(exc), Toast.LENGTH_LONG).show()

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "删除", "color": "#FF6B6B", "callback": do_delete, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               "删除下载站点", scroll, buttons, width_ratio=0.95)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _open_download_dir_dialog(self):
        self._show_modern_input("设置本地包输出目录", "/storage/emulated/0/download/本地包",
                                self.download_output_dir,
                                lambda v: (setattr(self, 'download_output_dir', v or "/storage/emulated/0/download/本地包"),
                                           os.makedirs(self.download_output_dir, exist_ok=True),
                                           self._save_config_to_file()))

    def _open_user_agent_dialog(self):
        def on_save(v):
            self._update_config_value('user_agent', v)
            self.user_agent = v
        self._show_modern_input("设置 User-Agent", "输入 User-Agent 字符串", self.user_agent, on_save)

    def _open_github_proxy_dialog(self):
        def on_save(v):
            self._update_config_value('github_proxy', v)
            self.config['github_proxy'] = v
            self.download_config['github_proxy'] = v
        self._show_modern_input("设置 GitHub 代理", "输入 GitHub 代理前缀 URL", self.config.get('github_proxy', GITHUB_PROXY), on_save)

    def _open_max_workers_dialog(self):
        def on_save(v):
            val = max(1, min(16, int(v)))
            self._update_config_value('download.max_workers', val)
            self.max_workers = val
        self._show_modern_input("设置下载并发数", "输入最大并发数 (1-16)", str(self.max_workers), on_save)

    def _open_retry_total_dialog(self):
        def on_save(v):
            val = max(0, min(5, int(v)))
            self._update_config_value('download.retry_total', val)
            self.retry_total = val
        self._show_modern_input("设置 HTTP 重试次数", "输入重试次数 (0-5)", str(self.retry_total), on_save)

    def _open_max_file_size_dialog(self):
        def on_save(v):
            val = max(1, int(v))
            self._update_config_value('download.max_file_size_mb', val)
            self.download_config['max_file_size_mb'] = val
        self._show_modern_input("设置最大文件大小 (MB)", "输入单文件大小限制 (MB)", str(self.download_config.get('max_file_size_mb', 100)), on_save)

    def _open_recursive_depth_dialog(self):
        def on_save(v):
            val = max(0, min(5, int(v)))
            self._update_config_value('download.recursive_depth', val)
            self.download_config['recursive_depth'] = val
        self._show_modern_input("设置递归深度", "输入 JSON 递归解析深度 (0-5)", str(self.download_config.get('recursive_depth', 2)), on_save)

    def _open_timeout_connect_dialog(self):
        def on_save(v):
            val = max(1, int(v))
            self._update_config_value('download.timeout_connect', val)
            self.download_config['timeout_connect'] = val
        self._show_modern_input("设置连接超时 (秒)", "输入连接超时秒数", str(self.download_config.get('timeout_connect', 10)), on_save)

    def _open_timeout_read_dialog(self):
        def on_save(v):
            val = max(1, int(v))
            self._update_config_value('download.timeout_read', val)
            self.download_config['timeout_read'] = val
        self._show_modern_input("设置读取超时 (秒)", "输入读取超时秒数", str(self.download_config.get('timeout_read', 60)), on_save)

    def _open_chunk_size_dialog(self):
        def on_save(v):
            val = max(1024, int(v))
            self._update_config_value('download.chunk_size', val)
            self.download_config['chunk_size'] = val
        self._show_modern_input("设置块大小 (字节)", "输入下载块大小 (字节)", str(self.download_config.get('chunk_size', 8192)), on_save)

    def _open_overwrite_dialog(self):
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            sw = Switch(act)
            sw.setText("覆盖已有文件")
            sw.setTextSize(16.0)
            sw.setTypeface(Typeface.DEFAULT)
            sw.setTextColor(Color.parseColor("#2C3E50"))
            sw.setChecked(self.download_config.get('overwrite', False))
            sw.setPadding(0, self._dp2px(act, 6), 0, self._dp2px(act, 6))

            def save():
                enabled = sw.isChecked()
                self._update_config_value('download.overwrite', enabled)
                self.download_config['overwrite'] = enabled
                Toast.makeText(act, f"覆盖已{'开启' if enabled else '关闭'}", Toast.LENGTH_SHORT).show()

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "保存", "color": "#6C63FF", "callback": save, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               "覆盖开关", sw, buttons)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _open_proxy_dialog(self):
        def on_save(v):
            self._update_config_value('proxy', v)
            self.config['proxy'] = v
            self.download_config['proxy'] = v
        self._show_modern_input("设置全局代理", "输入代理地址 (如 http://127.0.0.1:7890)，留空取消", self.config.get('proxy', ''), on_save)

    def _open_external_api_dialog(self):
        def on_save(v):
            self._update_config_value('external_api_url', v)
            self._update_config_value('download.decrypt.external_api_url', v)
            self.external_api_url = v
        self._show_modern_input("设置备用解密接口", "输入外部解密API URL", self.external_api_url, on_save)

    def _open_log_enabled_dialog(self):
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            container = LinearLayout(act)
            container.setOrientation(LinearLayout.VERTICAL)

            sw = Switch(act)
            sw.setText("启用文件日志")
            sw.setChecked(self.log_enabled)
            sw.setTextSize(16.0)
            sw.setTypeface(Typeface.DEFAULT)
            sw.setTextColor(Color.parseColor("#2C3E50"))
            sw.setPadding(0, 0, 0, self._dp2px(act, 10))
            container.addView(sw, LP(-1, -2))

            info = TextView(act)
            info.setText(f"日志目录: {self.log_dir}\n当前状态: {'开启' if self.log_enabled else '关闭'}")
            info.setTextSize(13.0)
            info.setTypeface(Typeface.DEFAULT)
            info.setTextColor(Color.parseColor("#7F8C8D"))
            container.addView(info, LP(-1, -2))

            def save():
                enabled = sw.isChecked()
                self.log_enabled = enabled
                self._update_config_value('log.enabled', enabled, raw=True)
                Toast.makeText(act, f"日志已{'开启' if enabled else '关闭'}", Toast.LENGTH_SHORT).show()

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "保存", "color": "#6C63FF", "callback": save, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               "日志开关", container, buttons)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _open_log_level_dialog(self):
        def on_ui(act, Builder, EditText, TextView, LinearLayout, LP, InputType,
                  DialogClick, Toast, ScrollView, Switch, Button, GradientDrawable,
                  Color, Gravity, TypedValue, Typeface):
            container = LinearLayout(act)
            container.setOrientation(LinearLayout.VERTICAL)

            levels = ['debug', 'info', 'warn', 'error']
            current = self.log_level.lower()
            switches = {}
            for level in levels:
                sw = Switch(act)
                sw.setText(level.upper())
                sw.setTextSize(16.0)
                sw.setTypeface(Typeface.DEFAULT)
                sw.setTextColor(Color.parseColor("#2C3E50"))
                sw.setChecked(level == current)
                sw.setPadding(0, self._dp2px(act, 6), 0, self._dp2px(act, 6))
                container.addView(sw, LP(-1, -2))
                switches[level] = sw

            def save():
                for level, sw in switches.items():
                    if sw.isChecked():
                        self.log_level = level
                        self._update_config_value('log.level', level, raw=True)
                        Toast.makeText(act, f"日志级别已设为: {level.upper()}", Toast.LENGTH_SHORT).show()
                        return

            buttons = [
                {"text": "取消", "color": "#E8ECF1", "callback": None, "is_primary": False},
                {"text": "保存", "color": "#6C63FF", "callback": save, "is_primary": True}
            ]
            dialog = self._build_modern_dialog(act, Builder, LinearLayout, TextView, LP, ScrollView,
                                               Button, GradientDrawable, Color, Gravity, TypedValue, Typeface,
                                               "设置日志级别", container, buttons)
            if dialog:
                dialog.show()
                self._dialog_refs.append(dialog)
        self._run_on_ui(on_ui)

    def _open_log_dir_dialog(self):
        def on_save(v):
            self._update_config_value('log.dir', v.rstrip('/') + '/', raw=True)
            self.log_dir = v.rstrip('/') + '/'
        self._show_modern_input("设置日志目录", "输入日志保存路径", self.log_dir.rstrip('/'), on_save)

    def _notify_app(self, message, wait=False, replace=False):
        text = " ".join(str(message or "").split()).strip()
        if not text or self._destroyed:
            return False
        try:
            from java import dynamic_proxy, jclass
            from java.lang import Runnable
            toast_class = jclass("android.widget.Toast")
            act = self._activity()
            if not act:
                return False
            displayed = threading.Event()
            class Show(dynamic_proxy(Runnable)):
                def run(self):
                    try:
                        toast = toast_class.makeText(act, text[:120], toast_class.LENGTH_LONG)
                        toast.show()
                    except Exception:
                        pass
                    finally:
                        displayed.set()
            runner = Show()
            self._notification_refs.append(runner)
            act.runOnUiThread(runner)
            if wait and not displayed.wait(1.5):
                return False
            return True
        except Exception:
            return False

    # ========================= TVBox 标准接口 =========================
    def init(self, extend=""):
        with self.lock:
            if self.inited:
                self._log("init 被重复调用，跳过")
                return
            self._initial_extend = extend
            self._init_session()
            self._log("=" * 50)
            self._log("【init 开始】开始初始化")
            self._log(f"【init】SCRIPT_DIR = {SCRIPT_DIR}")
            self._log(f"【init】当前工作目录 = {os.getcwd()}")
            config = self._load_default_config()
            ext = {}
            if extend:
                self._log(f"【init】收到 extend，类型={type(extend).__name__}")
                if isinstance(extend, dict):
                    ext = extend
                    self._log(f"【init】extend 为 dict，键: {list(ext.keys())}")
                elif isinstance(extend, str):
                    extend_str = extend.strip()
                    self._log(f"【init】extend 为字符串，长度={len(extend_str)}")
                    self._log(f"【init】extend 前200字符: {extend_str[:200]}")
                    if extend_str.startswith('{') or extend_str.startswith('['):
                        self._log("【init】检测到 JSON 格式，开始解析...")
                        try:
                            ext = json.loads(extend_str)
                            self._log(f"【init】JSON 解析成功，键: {list(ext.keys())}")
                        except Exception as e:
                            self._log(f"【init】ext JSON 解析失败: {e}")
                            ext = {}
                    else:
                        self._log("【init】非 JSON 字符串，尝试作为路径/URL 加载...")
                        loaded = self._load_config_from_ext(extend_str)
                        if loaded and isinstance(loaded, dict):
                            ext = loaded
                            self._log(f"【init】路径加载成功，键: {list(ext.keys())}")
                        else:
                            self._log("【init】路径加载失败，尝试解析为传统 URL 字符串...")
                            lives, base_url, pic_url = self._parse_url_string(extend_str)
                            if lives:
                                ext = {'lives': lives, 'vod_pic': pic_url}
                                self._log(f"【init】传统 URL 解析成功，lives 数量: {len(lives)}")
                            else:
                                self._log("【init】传统 URL 解析失败，ext 为空")
                                ext = {}
                else:
                    self._log(f"【init】extend 为未知类型: {type(extend).__name__}")
                    ext = {}
            else:
                self._log("【init】extend 为空，使用默认配置")
                ext = {}

            self._detect_base_dir(ext)
            self._log(f"【init】基础目录检测完成: {self._get_base_dir()}")

            if ext:
                ext = self._normalize_config_keys(ext)
                self._log(f"【init】ext 键列表: {list(ext.keys())}")
                config_file = ext.get('config_file', '')
                self._log(f"【init】config_file 值: '{config_file}'")
                if config_file:
                    self._log(f"【init】开始加载外部配置: {config_file}")
                    cf_config = self._load_config_file(config_file)
                    if cf_config:
                        self._log(f"【init】✅ 已加载外部配置: {config_file}")
                        self._log(f"【init】外部配置原始键: {list(cf_config.keys())}")
                        cf_config = self._normalize_config_keys(cf_config)
                        self._log(f"【init】外部配置规范化后键: {list(cf_config.keys())}")
                        merged_count = 0
                        for k, v in cf_config.items():
                            if k not in ext:
                                ext[k] = v
                                merged_count += 1
                        self._log(f"【init】合并了 {merged_count} 个新键到 ext")
                        self._log(f"【init】合并后 ext 键: {list(ext.keys())}")
                    else:
                        self._log(f"【init】❌ 外部配置加载失败: {config_file}")
                else:
                    self._log("【init】config_file 为空，跳过外部配置加载")
                self._log("【init】开始合并 ext 到 config...")
                for k, v in ext.items():
                    if k == 'config_file':
                        continue
                    if isinstance(v, dict) and k in config and isinstance(config[k], dict):
                        config[k].update(v)
                        self._log(f"【init】合并 dict 键: {k}")
                    else:
                        config[k] = v
                        self._log(f"【init】合并键: {k} = {str(v)[:80]}")
            else:
                self._log("【init】ext 为空，跳过合并")
            self._log("【init】开始应用配置...")
            self._apply_config(config)

            persistent = self._load_persistent_config()
            if persistent and isinstance(persistent, dict):
                self._log("【init】检测到持久化配置，开始合并...")
                persistent = self._normalize_config_keys(persistent)
                merged_count = 0
                for k, v in persistent.items():
                    if k == 'config_file':
                        continue
                    if isinstance(v, dict) and k in self.config and isinstance(self.config[k], dict):
                        self.config[k].update(v)
                        merged_count += 1
                    else:
                        self.config[k] = v
                        merged_count += 1
                self._apply_config(self.config)
                self._log(f"【init】✅ 已合并持久化配置，共 {merged_count} 项")

            self.inited = True
            self._log("【init】✅ 初始化完成（v3.0 浅色现代风 + 日志面板）")
            self._log("=" * 50)

    def getName(self):
        return "本地包管理器 {}".format(self.VERSION)

    def homeContent(self, filter):
        self._ensure_initialized()
        classes = [
            {"type_id": "batch", "type_name": "📥 批量"},
            {"type_id": "decrypt", "type_name": "✂️ 解密"},
            {"type_id": "localize", "type_name": "❤️️ 本地"},
            {"type_id": "settings", "type_name": "⚙️ 设置"},
        ]
        return {"class": classes, "filters": {}}

    def homeVod(self):
        return {"list": []}

    def categoryContent(self, tid, pg, filter, ext):
        self._ensure_initialized()
        page = self._page_number(pg)
        if tid == "batch":
            items = [
                {"vod_id": "log", "vod_name": "✉️ 日志面板", "vod_pic": "", "vod_remarks": "实时查看下载日志与进度", "action": "show_log"},
                {"vod_id": self.ACTION_DOWNLOAD_PACKAGE, "vod_name": "⬇ 批量本地", "vod_pic": "", "vod_remarks": "选择站点生成本地包", "action": self.ACTION_DOWNLOAD_PACKAGE},
                {"vod_id": "decrypt_all", "vod_name": "✂️ 批量解密", "vod_pic": "", "vod_remarks": "选择站点解密", "action": "decrypt_all"},
            ]
            return self._paged_result(items, page)
        elif tid == "decrypt":
            items = []
            for site in self.package_download_sites:
                items.append({
                    "vod_id": f"decrypt_{site['id']}",
                    "vod_name": f"✂️ {site['name']}",
                    "vod_pic": "",
                    "vod_remarks": self._get_decrypt_status_text(site),
                    "action": f"decrypt_site_{site['id']}",
                })
            return self._paged_result(items, page)
        elif tid == "localize":
            items = []
            for site in self.package_download_sites:
                items.append({
                    "vod_id": f"localize_{site['id']}",
                    "vod_name": f"❤️️ {site['name']}",
                    "vod_pic": "",
                    "vod_remarks": self._get_localize_status_text(site),
                    "action": f"localize_site_{site['id']}",
                })
            return self._paged_result(items, page)
        elif tid == "apply":
            items = []
            for site in self.package_download_sites:
                label = self._get_site_state_label(site['id'], 'apply')
                items.append({
                    "vod_id": f"apply_{site['id']}",
                    "vod_name": f"📲 {site['name']}",
                    "vod_pic": "",
                    "vod_remarks": label,
                    "action": f"apply_site_{site['id']}",
                })
            return self._paged_result(items, page)
        elif tid == "settings":
            ua_display = self.user_agent
            if len(ua_display) > 30:
                ua_display = ua_display[:30] + "..."
            gh_display = self.config.get('github_proxy', GITHUB_PROXY)
            if len(gh_display) > 30:
                gh_display = gh_display[:30] + "..."
            ext_display = self.external_api_url
            if len(ext_display) > 30:
                ext_display = ext_display[:30] + "..."
            items = [
    {"vod_id": "setting_restore_default", "vod_name": "➰️ 恢复默认设置", "vod_pic": "", "vod_remarks": "恢复初始配置（清除运行时修改）", "action": "local_source_restore_default"},
    {"vod_id": "setting_add_url", "vod_name": "✏️ 添加在线源网址", "vod_pic": "", "vod_remarks": "当前 {} 个站点".format(len(self.package_download_sites)), "action": "local_source_edit_download_url"},
    {"vod_id": "setting_delete", "vod_name": "➖️ 删除下载站点", "vod_pic": "", "vod_remarks": "删除在线网址设置", "action": "local_source_delete_download_sites"},
    {"vod_id": "setting_download_dir", "vod_name": "✒️ 本地包下载目录", "vod_pic": "", "vod_remarks": self.download_output_dir or "未设置", "action": "local_source_edit_download_dir"},
    {"vod_id": "setting_user_agent", "vod_name": "✈️ User‑Agent", "vod_pic": "", "vod_remarks": ua_display, "action": "local_source_edit_user_agent"},
    {"vod_id": "setting_github_proxy", "vod_name": "✨️ GitHub 代理", "vod_pic": "", "vod_remarks": gh_display, "action": "local_source_edit_github_proxy"},
    {"vod_id": "setting_max_workers", "vod_name": "➕️ 下载并发数", "vod_pic": "", "vod_remarks": str(self.max_workers), "action": "local_source_edit_max_workers"},
    {"vod_id": "setting_retry_total", "vod_name": "➰️ HTTP 重试次数", "vod_pic": "", "vod_remarks": str(self.retry_total), "action": "local_source_edit_retry_total"},
    {"vod_id": "setting_max_file_size", "vod_name": "✂️ 最大文件大小 (MB)", "vod_pic": "", "vod_remarks": str(self.download_config.get('max_file_size_mb', 100)), "action": "local_source_edit_max_file_size"},
    {"vod_id": "setting_recursive_depth", "vod_name": "❓️ 递归解析深度", "vod_pic": "", "vod_remarks": str(self.download_config.get('recursive_depth', 2)), "action": "local_source_edit_recursive_depth"},
    {"vod_id": "setting_timeout_connect", "vod_name": "❗️ 连接超时 (秒)", "vod_pic": "", "vod_remarks": str(self.download_config.get('timeout_connect', 10)), "action": "local_source_edit_timeout_connect"},
    {"vod_id": "setting_timeout_read", "vod_name": "❗️ 读取超时 (秒)", "vod_pic": "", "vod_remarks": str(self.download_config.get('timeout_read', 60)), "action": "local_source_edit_timeout_read"},
    {"vod_id": "setting_chunk_size", "vod_name": "✒️ 块大小 (字节)", "vod_pic": "", "vod_remarks": str(self.download_config.get('chunk_size', 8192)), "action": "local_source_edit_chunk_size"},
    {"vod_id": "setting_overwrite", "vod_name": "✍️ 覆盖已有文件", "vod_pic": "", "vod_remarks": "是" if self.download_config.get('overwrite', False) else "否", "action": "local_source_edit_overwrite"},
    {"vod_id": "setting_proxy", "vod_name": "✈️ 全局代理", "vod_pic": "", "vod_remarks": self.config.get('proxy', '') or "未设置", "action": "local_source_edit_proxy"},
    {"vod_id": "setting_external_api", "vod_name": "✴️ 备用解密接口", "vod_pic": "", "vod_remarks": ext_display, "action": "local_source_edit_external_api"},
    {"vod_id": "setting_log_enabled", "vod_name": "✉️ 日志开关", "vod_pic": "", "vod_remarks": "已开启" if self.log_enabled else "已关闭", "action": "local_source_edit_log_enabled"},
    {"vod_id": "setting_log_level", "vod_name": "✅️ 日志级别", "vod_pic": "", "vod_remarks": self.log_level.upper(), "action": "local_source_edit_log_level"},
    {"vod_id": "setting_log_dir", "vod_name": "✒️ 日志目录", "vod_pic": "", "vod_remarks": self.log_dir.rstrip('/') if self.log_dir else "未设置", "action": "local_source_edit_log_dir"},
]
            return self._paged_result(items, page)
        else:
            return {"page": 1, "pagecount": 1, "limit": 10, "total": 0, "list": []}

    def _site_summary(self):
        return ", ".join(
            "{}:{}".format(s.get("name", "未命名"), "开" if s.get("enabled", True) else "关")
            for s in self.package_download_sites
        ) or "无"

    def _paged_result(self, items, page):
        total = len(items)
        page_size = 30
        page_count = max(1, (total + page_size - 1) // page_size)
        start = (page - 1) * page_size
        page_items = items[start:start+page_size] if page <= page_count else []
        return {
            "page": page,
            "pagecount": page_count,
            "limit": page_size,
            "total": total,
            "list": page_items,
        }

    def _page_number(self, value):
        try:
            return max(1, int(value))
        except Exception:
            return 1

    def detailContent(self, array):
        self._ensure_initialized()
        vid = str(array[0]) if isinstance(array, (list, tuple)) and array else str(array or "")
        if vid == "status":
            return {"list": [{"vod_name": "下载状态", "vod_remarks": self._package_download_message or "空闲"}]}
        if vid == self.ACTION_DOWNLOAD_PACKAGE:
            def do_download(selected_sites):
                self._exec_with_log(self._start_package_download, selected_sites)
            self._show_modern_batch_selector("选择批量本地站点", do_download)
            return {"list": [{"vod_name": "批量本地", "vod_remarks": "请选择站点"}]}
        if vid == "decrypt_all":
            def do_decrypt(selected_sites):
                self._exec_with_log(self._decrypt_sites, selected_sites)
            self._show_modern_batch_selector("选择批量解密站点", do_decrypt)
            return {"list": [{"vod_name": "批量解密", "vod_remarks": "请选择站点"}]}
        return {"list": []}

    def searchContent(self, key, quick, pg="1"):
        return {"page": 1, "pagecount": 1, "limit": 10, "total": 0, "list": []}

    def playerContent(self, flag, id, vipFlags):
        return {"parse": 0, "url": "", "header": {}, "msg": "该条目为配置管理"}

    def localProxy(self, params):
        return [404, "application/json", json.dumps({"error": "not found"})]

    def action(self, action):
        self._ensure_initialized()
        self._log(f"收到 action: {action}")

        if action == self.ACTION_DOWNLOAD_PACKAGE:
            if self._package_download_thread and self._package_download_thread.is_alive():
                def confirm_cancel():
                    self._show_modern_confirm(
                        "任务运行中",
                        "批量本地正在运行，是否结束当前任务？",
                        lambda: self._cancel_package_download(),
                        extra_buttons=[{"text": "日志", "callback": self._show_log_dialog}]
                    )
                confirm_cancel()
                return {"code": 0, "msg": ""}
            else:
                def do_download(selected_sites):
                    self._exec_with_log(self._start_package_download, selected_sites)
                self._show_modern_batch_selector("选择批量本地站点", do_download)
                return {"code": 0, "msg": ""}

        # 单个解密
        if action.startswith("decrypt_site_"):
            site_id = action[len("decrypt_site_"):]
            site = next((s for s in self.package_download_sites if s['id'] == site_id), None)
            if not site:
                return {"code": 0, "msg": ""}
            state = self._site_states.get(site_id, {})
            status = state.get('decrypt_status', 'idle')

            if status == 'success':
                local_path = state.get('decrypt_result')
                if local_path and os.path.exists(local_path):
                    def do_edit():
                        try:
                            with open(local_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            remote_url = site['url']
                            local_url = "file://" + os.path.abspath(local_path)
                            def on_save():
                                self._site_states[site_id]['decrypt_msg'] = '已编辑'
                            self._show_modern_text_editor(
                                f"⚙️ 解密内容 - {site['name']}",
                                content,
                                local_path,
                                remote_url,
                                local_url,
                                on_save
                            )
                        except Exception as e:
                            self._log(f"打开编辑器失败: {e}")
                            self._notify_app(f"打开编辑器失败: {e}")
                    do_edit()
                    return {"code": 0, "msg": ""}

            with self._site_op_lock:
                if site_id in self._site_op_threads and self._site_op_threads[site_id].is_alive():
                    def cancel_site_decrypt():
                        self._show_modern_confirm(
                            "任务运行中",
                            f"解密「{site['name']}」正在运行，是否结束？",
                            lambda: self._cancel_site_op(site_id, 'decrypt'),
                            extra_buttons=[{"text": "日志", "callback": self._show_log_dialog}]
                        )
                    cancel_site_decrypt()
                    return {"code": 0, "msg": ""}

            extra_btns = []
            remote_url = site['url']
            extra_btns.append({"text": "远程U", "callback": lambda: self._copy_to_clipboard(remote_url, "已复制远程接口URL")})

            self._show_modern_confirm(
                f"解密站点: {site['name']}",
                f"当前状态: {status}\n确定要启动解密任务吗？",
                lambda: self._exec_with_log(self._decrypt_single_site, site_id),
                extra_buttons=extra_btns
            )
            return {"code": 0, "msg": ""}

        # 单个本地化
        if action.startswith("localize_site_"):
            site_id = action[len("localize_site_"):]
            site = next((s for s in self.package_download_sites if s['id'] == site_id), None)
            if not site:
                return {"code": 0, "msg": ""}
            state = self._site_states.get(site_id, {})
            status = state.get('localize_status', 'idle')
            with self._site_op_lock:
                if site_id in self._site_op_threads and self._site_op_threads[site_id].is_alive():
                    def cancel_site_localize():
                        self._show_modern_confirm(
                            "任务运行中",
                            f"本地化「{site['name']}」正在运行，是否结束？",
                            lambda: self._cancel_site_op(site_id, 'localize'),
                            extra_buttons=[{"text": "日志", "callback": self._show_log_dialog}]
                        )
                    cancel_site_localize()
                    return {"code": 0, "msg": ""}

            extra_btns = []
            remote_url = site['url']
            extra_btns.append({"text": "远程U", "callback": lambda: self._copy_to_clipboard(remote_url, "已复制远程接口URL")})

            if status == 'success':
                local_path = state.get('localize_result')
                if local_path:
                    local_url = "file://" + os.path.abspath(local_path)
                    extra_btns.append({"text": "本地U", "callback": lambda: self._copy_to_clipboard(local_url, "已复制本地接口路径")})

            self._show_modern_confirm(
                f"本地化站点: {site['name']}",
                f"当前状态: {status}\n确定要启动本地化任务吗？",
                lambda: self._exec_with_log(self._localize_single_site, site_id),
                extra_buttons=extra_btns
            )
            return {"code": 0, "msg": ""}

        if action.startswith("apply_site_"):
            site_id = action[len("apply_site_"):]
            site = next((s for s in self.package_download_sites if s['id'] == site_id), None)
            if site:
                self._show_modern_confirm(
                    "确认应用",
                    f"确定要应用站点「{site['name']}」吗？\n（功能开发中）",
                    lambda: self._exec_with_log(self._apply_single_site, site_id)
                )
            return {"code": 0, "msg": ""}

        if action == "decrypt_all":
            def do_decrypt(selected_sites):
                self._exec_with_log(self._decrypt_sites, selected_sites)
            self._show_modern_batch_selector("选择批量解密站点", do_decrypt)
            return {"code": 0, "msg": ""}

        # 设置类
        if action == 'show_status':
            status_msg = self._package_download_message or "空闲"
            self._show_modern_info("下载状态", status_msg, show_copy=True)
        elif action == 'show_log' or action == 'show_monitor':
            self._show_log_dialog()
        elif action == 'local_source_edit_download_url':
            self._open_package_download_url_dialog()
        elif action == 'local_source_delete_download_sites':
            self._open_package_download_delete_dialog()
        elif action == 'local_source_edit_download_dir':
            self._open_download_dir_dialog()
        elif action == 'local_source_edit_user_agent':
            self._open_user_agent_dialog()
        elif action == 'local_source_edit_github_proxy':
            self._open_github_proxy_dialog()
        elif action == 'local_source_edit_max_workers':
            self._open_max_workers_dialog()
        elif action == 'local_source_edit_retry_total':
            self._open_retry_total_dialog()
        elif action == 'local_source_edit_max_file_size':
            self._open_max_file_size_dialog()
        elif action == 'local_source_edit_recursive_depth':
            self._open_recursive_depth_dialog()
        elif action == 'local_source_edit_timeout_connect':
            self._open_timeout_connect_dialog()
        elif action == 'local_source_edit_timeout_read':
            self._open_timeout_read_dialog()
        elif action == 'local_source_edit_chunk_size':
            self._open_chunk_size_dialog()
        elif action == 'local_source_edit_overwrite':
            self._open_overwrite_dialog()
        elif action == 'local_source_edit_proxy':
            self._open_proxy_dialog()
        elif action == 'local_source_edit_external_api':
            self._open_external_api_dialog()
        elif action == 'local_source_edit_log_enabled':
            self._open_log_enabled_dialog()
        elif action == 'local_source_edit_log_level':
            self._open_log_level_dialog()
        elif action == 'local_source_edit_log_dir':
            self._open_log_dir_dialog()
        elif action == 'local_source_restore_default':
            self._show_modern_confirm(
                "确认恢复初始配置",
                "确定要恢复初始配置吗？\n将清除所有运行时修改（缓存、持久化配置、站点状态等），重新加载初始数据。",
                lambda: self._exec_with_log(self._restore_default_config)
            )
        else:
            self._log(f"未知 action: {action}")
        return {"code": 0, "msg": ""}

    def _cancel_package_download(self):
        if self._package_cancel_event:
            self._package_cancel_event.set()
            self._log("用户请求取消批量下载")
            self._notify_app("正在取消批量下载...")

    def _cancel_site_op(self, site_id, op_type):
        if site_id in self._site_cancel_events:
            self._site_cancel_events[site_id].set()
            self._log(f"用户请求取消 {op_type} 操作 (site_id={site_id})")
            self._notify_app(f"正在取消 {op_type}...")

    def destroy(self):
        self._destroyed = True
        if self._session:
            try:
                self._session.close()
            except Exception:
                pass
        for ev in self._site_cancel_events.values():
            ev.set()
        if self._package_cancel_event:
            self._package_cancel_event.set()
        return "destroy"

    def _ensure_initialized(self):
        if not self.inited:
            try:
                self.init("")
            except Exception as e:
                self._log(f"延迟初始化失败: {e}")
                self.inited = True
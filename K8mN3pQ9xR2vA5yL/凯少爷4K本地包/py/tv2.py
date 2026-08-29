#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Whos.tv 全自动爬虫（完整版）
- 爬取页数: 29996 页（可自定义）
- 并发线程: 80 线程
- 输出: TVBox 直播 M3U + 点播 JSON
- 包含多策略解析、重试、防封、断点续爬（可选）
"""

import os
import re
import time
import json
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

class WhosTvUltimate:
    def __init__(self, start_url="https://whos.tv/videos", max_pages=29996, max_workers=80, delay=0.5):
        """
        初始化爬虫
        :param start_url: 起始列表页 URL
        :param max_pages: 最大爬取页数（29996）
        :param max_workers: 并发线程数（80）
        :param delay: 每个请求的间隔时间（秒），为避免封 IP，80 线程时建议 delay>=0.3
        """
        self.start_url = start_url
        self.max_pages = max_pages
        self.max_workers = max_workers
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
            "Referer": "https://whos.tv/",
            "X-Requested-With": "XMLHttpRequest"
        })
        self.lock = Lock()

        # 输出目录（手机存储根目录）
        self.output_dir = "/sdcard/whos_tv_m3u"
        os.makedirs(self.output_dir, exist_ok=True)

        # 输出文件
        self.m3u_file = os.path.join(self.output_dir, "whos_live.m3u")
        self.json_file = os.path.join(self.output_dir, "whos_vod.json")
        self.failed_file = os.path.join(self.output_dir, "failed_urls.txt")
        self.progress_file = os.path.join(self.output_dir, "progress.txt")  # 记录已爬取页码

        # 存储成功结果
        self.video_results = {}   # {m3u8_url: title}
        self.failed_urls = []

        # 断点续爬：记录已处理的页码
        self.processed_pages = set()
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                for line in f:
                    self.processed_pages.add(int(line.strip()))

    def fetch_html(self, url, retry=3):
        """获取页面 HTML，带重试和超时"""
        for i in range(retry):
            try:
                resp = self.session.get(url, timeout=20)
                if resp.status_code == 404:
                    return None
                resp.raise_for_status()
                if resp.encoding is None:
                    resp.encoding = 'utf-8'
                return resp.text
            except Exception as e:
                print(f"[请求失败] {url} ({i+1}/{retry}): {e}")
                if i < retry - 1:
                    time.sleep(2)
        return None

    def detect_page_format(self):
        """探测分页格式：/page-2 或 /pages/2"""
        test1 = self.start_url + "/page-2"
        test2 = self.start_url + "/pages/2"
        if self.fetch_html(test1):
            return "/page-{}"
        elif self.fetch_html(test2):
            return "/pages/{}"
        else:
            return "/page-{}"   # 默认

    def get_all_detail_urls(self):
        """
        遍历所有列表页，收集视频详情页 URL
        支持断点续爬（跳过已处理的页码）
        """
        print(f"1. 开始扫描列表页，共 {self.max_pages} 页（断点续爬已启用）...")
        detail_urls = set()
        page_format = self.detect_page_format()
        print(f"   分页格式: {page_format}")

        for page in range(1, self.max_pages + 1):
            if page in self.processed_pages:
                continue   # 跳过已爬取的页码

            if page == 1:
                url = self.start_url
            else:
                url = self.start_url + page_format.format(page)

            print(f"   正在爬取列表页 {page}: {url}")
            html = self.fetch_html(url)
            if not html:
                print(f"   列表页 {page} 无效，停止翻页")
                break

            soup = BeautifulSoup(html, 'html.parser')
            # 匹配所有视频详情页链接（排除分页链接）
            pattern = re.compile(r'/videos/(?!page-|pages/)[^/]+$')
            page_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                if pattern.search(href):
                    full_url = urljoin(url, href)
                    page_links.append(full_url)

            new_count = len(set(page_links))
            detail_urls.update(page_links)
            print(f"   本页发现 {new_count} 个视频，累计 {len(detail_urls)} 个")

            # 记录已爬取的页码
            with open(self.progress_file, 'a') as f:
                f.write(str(page) + "\n")
            self.processed_pages.add(page)

            time.sleep(self.delay)   # 避免请求过快

        print(f"✅ 列表页扫描完成，共收集到 {len(detail_urls)} 个视频详情页\n")
        return list(detail_urls)

    def extract_title_and_m3u8(self, detail_url):
        """
        从单个视频详情页中提取标题和真实 m3u8 链接（多策略）
        返回: (title, m3u8_url)
        """
        html = self.fetch_html(detail_url)
        if not html:
            return None, None

        soup = BeautifulSoup(html, 'html.parser')

        # ---------- 提取标题 ----------
        title = None
        # 策略1: h1 标签
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text(strip=True)
        # 策略2: title 标签并清洗
        if not title and soup.title:
            raw = soup.title.string.strip()
            if ' - ' in raw:
                parts = raw.split(' - ')
                title = next((p for p in parts if 'whos.tv' not in p.lower()), parts[0])
            else:
                title = raw
        # 策略3: URL 最后一段作为后备
        if not title:
            title = detail_url.rstrip('/').split('/')[-1]
        title = title.strip() if title else "未知视频"

        # ---------- 提取 m3u8 链接 ----------
        m3u8_url = None

        # 策略1: 直接在 HTML 中搜索 .m3u8
        m = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
        if m:
            m3u8_url = m.group(0).replace('\\', '')

        # 策略2: 分析所有 <script>（内联+外链）
        if not m3u8_url:
            scripts = soup.find_all('script')
            all_js = '\n'.join([s.string for s in scripts if s.string])
            # 下载外部 JS
            for script in scripts:
                if script.get('src'):
                    js_url = urljoin(detail_url, script['src'])
                    js_content = self.fetch_html(js_url)
                    if js_content:
                        all_js += '\n' + js_content
            m = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', all_js)
            if m:
                m3u8_url = m.group(0).replace('\\', '')

        # 策略3: 查找 iframe 并深入解析
        if not m3u8_url:
            iframe = soup.find('iframe', src=True)
            if iframe:
                iframe_src = iframe['src']
                if iframe_src.startswith('http'):
                    iframe_html = self.fetch_html(iframe_src)
                    if iframe_html:
                        m = re.search(r'https?://[^\s"\']+\.m3u8[^\s"\']*', iframe_html)
                        if m:
                            m3u8_url = m.group(0).replace('\\', '')

        # 策略4: 尝试 API 嗅探
        if not m3u8_url:
            api_patterns = [
                r'["\'](/api/[^"\']+)["\']',
                r'["\'](/videos/api/[^"\']+)["\']',
                r'["\'](/player/[^"\']+)["\']',
            ]
            api_candidates = set()
            for pat in api_patterns:
                for match in re.findall(pat, html):
                    full = urljoin(detail_url, match)
                    if any(key in full for key in ['api', 'player']):
                        api_candidates.add(full)
            video_id = detail_url.rstrip('/').split('/')[-1]
            for api in api_candidates:
                for param in ['id', 'video_id', 'vid']:
                    test_url = api + ('?' if '?' not in api else '&') + f'{param}={video_id}'
                    data = self.fetch_json(test_url)
                    if data:
                        m3u8 = self._extract_m3u8_from_json(data)
                        if m3u8:
                            m3u8_url = m3u8
                            break
                if m3u8_url:
                    break

        # 相对路径补全
        if m3u8_url and not m3u8_url.startswith('http'):
            m3u8_url = urljoin(detail_url, m3u8_url)

        return title, m3u8_url

    def fetch_json(self, url):
        """请求 JSON 接口"""
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200 and 'application/json' in resp.headers.get('Content-Type', ''):
                return resp.json()
        except:
            pass
        return None

    def _extract_m3u8_from_json(self, data):
        """递归从 JSON 中查找 m3u8 链接"""
        if isinstance(data, dict):
            for val in data.values():
                if isinstance(val, str) and ('.m3u8' in val or '.mp4' in val):
                    return val
                res = self._extract_m3u8_from_json(val)
                if res:
                    return res
        elif isinstance(data, list):
            for item in data:
                res = self._extract_m3u8_from_json(item)
                if res:
                    return res
        elif isinstance(data, str) and ('.m3u8' in data or '.mp4' in data):
            return data
        return None

    def parse_videos_concurrently(self, detail_urls):
        """使用 80 线程并发解析所有视频详情页"""
        total = len(detail_urls)
        print(f"2. 开始解析 {total} 个视频详情页（线程数: {self.max_workers}）...")
        success_count = 0

        # 使用 ThreadPoolExecutor 并控制最大线程数
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.extract_title_and_m3u8, url): url for url in detail_urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    title, m3u8 = future.result()
                    if title and m3u8:
                        with self.lock:
                            self.video_results[m3u8] = title
                        print(f"   ✅ 成功: {title[:50]}...")
                        success_count += 1
                    else:
                        with self.lock:
                            self.failed_urls.append(url)
                        print(f"   ❌ 失败: {url}")
                except Exception as e:
                    print(f"   ⚠️ 解析异常 {url}: {e}")
                    with self.lock:
                        self.failed_urls.append(url)
                # 控制请求频率（避免 80 线程同时发出大量请求）
                time.sleep(self.delay / self.max_workers)

        print(f"\n✅ 解析完成，成功 {success_count} / {total}")
        if self.failed_urls:
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                for u in self.failed_urls:
                    f.write(u + '\n')
            print(f"⚠️ 失败链接已保存至: {self.failed_file}")

    def generate_tvbox_files(self):
        """生成 TVBox 直播 M3U 和点播 JSON 文件"""
        if not self.video_results:
            print("❌ 没有成功获取任何视频，无法生成文件。")
            return

        # 1. 生成 M3U 直播文件
        with open(self.m3u_file, 'w', encoding='utf-8') as f:
            f.write("#EXTM3U\n")
            for url, title in self.video_results.items():
                f.write(f'#EXTINF:-1 tvg-name="{title}" group-title="WhosTV",{title}\n')
                f.write(url + "\n")
        print(f"📺 直播文件已生成: {self.m3u_file} (共 {len(self.video_results)} 条)")

        # 2. 生成 JSON 点播文件
        vod_list = []
        for url, title in self.video_results.items():
            vod_list.append({
                "vod_name": title,
                "vod_id": url,
                "vod_play_from": "WhosTV",
                "vod_play_url": f"播放${url}"
            })
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump({"list": vod_list}, f, ensure_ascii=False, indent=4)
        print(f"🎬 点播文件已生成: {self.json_file} (共 {len(vod_list)} 条)")

    def run(self):
        """主流程"""
        print("🚀 Whos.tv 终极爬虫启动")
        print(f"   目标页数: {self.max_pages} 页")
        print(f"   并发线程: {self.max_workers}")
        print(f"   请求间隔: {self.delay} 秒")
        print("   ⚠️ 注意: 80 线程可能导致 IP 被封，建议使用代理或降低线程数\n")

        # 1. 收集所有详情页 URL
        detail_urls = self.get_all_detail_urls()
        if not detail_urls:
            print("未找到任何视频详情页，程序退出。")
            return

        # 2. 并发解析
        self.parse_videos_concurrently(detail_urls)

        # 3. 生成输出文件
        self.generate_tvbox_files()
        print("\n✨ 全部完成！请将生成的文件导入 TVBox 使用。")

if __name__ == "__main__":
    # ========== 用户可修改参数 ==========
    TOTAL_PAGES = 29996       # 爬取页数（网站实际约 26997，这里按您要求 29996）
    WORKERS = 50              # 并发线程数（80）
    REQUEST_DELAY = 0.5       # 请求间隔（秒），线程多时建议不要小于 0.3
    # ==================================

    spider = WhosTvUltimate(
        start_url="https://whos.tv/videos",
        max_pages=TOTAL_PAGES,
        max_workers=WORKERS,
        delay=REQUEST_DELAY
    )
    spider.run()
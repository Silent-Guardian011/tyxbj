#!/usr/bin/env python3
"""
PHP服务检测与配置更新

"""

import os
import re
import subprocess
import json
import traceback
from base.spider import Spider

class Spider(Spider):
    
    def getName(self):
        return "PHP服务检测"
    
    def init(self, extend=""):
        pass
    
    def isVideoFormat(self, url):
        pass
    
    def manualVideoCheck(self):
        pass
    
    def action(self, action):
        pass
    
    def destroy(self):
        pass
    
    def homeContent(self, filter):
        """首页内容 - 返回空，不显示任何分类"""
        # 直接返回空，什么都不显示
        return {"class": []}
    
    def homeVideoContent(self):
        """首页视频内容 - 只显示一个检测触发项"""
        # 创建一个点击检测的项，只返回一个
        video_item = {
            "vod_id": "php_detect_trigger",
            "vod_name": "更新端口",
            "vod_pic": "https://img.icons8.com/color/96/000000/info--v1.png",
            "vod_remarks": "点击开始更新",
            "vod_content": "点击此条目开始检测PHP服务端口并更新配置"
        }
        
        # 只返回一个，就一个！
        return {"list": [video_item]}
    
    def categoryContent(self, tid, pg, filter, extend):
        """分类内容 - 返回空"""
        return {"list": []}
    
    def detailContent(self, ids):
        """详情内容 - 执行检测并显示结果"""
        if ids[0] == "php_detect_trigger":
            # 执行检测
            result = self.detect_and_update()
            
            # 显示结果，并添加播放链接避免自动切换源
            video_item = {
                "vod_id": "config_result",
                "vod_name": f"PHP端口已更新 端口: {result['port']}",
                "vod_pic": "https://img.icons8.com/color/96/000000/info--v1.png",
                "vod_remarks": f"状态: {result['status'][:20]}",
                "vod_content": self._format_result_content(result),
                "vod_play_url": f"看个视频，好心情${result.get('video_url', 'https://vd4.bdstatic.com/mda-kmbika46ppvf7nzc/v1-cae/1080p/mda-kmbika46ppvf7nzc.mp4')}",
                "vod_play_from": f"PHP端口更新结果：{result['port']}，返回刷新即可！"
            }
            
            return {"list": [video_item]}
        else:
            return {"list": []}
    
    def searchContent(self, key, quick, pg=1):
        return {"list": []}
    
    def playerContent(self, flag, id, vipFlags):
        """播放内容 - 返回视频播放地址"""
        play_url = "https://vd4.bdstatic.com/mda-kmbika46ppvf7nzc/v1-cae/1080p/mda-kmbika46ppvf7nzc.mp4"
        return {
            "parse": 0,  # 0表示直接播放，1表示解析
            "playUrl": "",  # 空字符串，不需要播放链接
            "url": play_url,  # 视频地址
            "header": {}  # 请求头，可以为空
        }
    
    def localProxy(self, param):
        return [200, "text/plain", "PHP服务检测工具"]
    
    # ==================== 核心功能 ====================
    
    def _format_result_content(self, result):
        """格式化结果内容"""
        status_icon = "✅" if result.get('success') else "❌"
        
        content = f"📊 PHP服务检测结果:\n\n"
        content += f"{status_icon} 检测端口: {result['port']}\n"
        content += f"{status_icon} 操作状态: {result['status']}\n\n"
        
        # 显示所有配置文件路径
        if 'config_paths' in result:
            for i, config_path in enumerate(result['config_paths'], 1):
                content += f"📁 配置文件{i}: {config_path}\n"
        else:
            content += f"📁 配置文件: {result['config_path']}\n"
        content += "\n"
        
        if result.get('success'):
            content += f"🌐 可用API地址:\n"
            content += f"http://127.0.0.1:{result['port']}/config.php?mode=scan-only\n"
            content += f"http://127.0.0.1:{result['port']}/config.php?mode=insert\n"
            content += f"http://127.0.0.1:{result['port']}/config.php?mode=cover\n\n"
            content += f"✅ 配置已自动更新到此端口"
        else:
            content += f"⚠️ 检测失败，请检查:\n"
            content += f"1. PHP服务是否运行\n"
            content += f"2. 配置文件是否存在\n"
            content += f"3. 文件权限是否足够\n\n"
            content += f"📝 错误详情: {result['status']}"
        
        return content
    
    def detect_and_update(self):
        """检测PHP服务端口并更新配置文件"""
        config_paths = [
            "/storage/emulated/0/lz/config.json",
            "/storage/emulated/0/lz/lib/config.json"
        ]
        
        try:
            # 检测PHP服务端口
            port = self.detect_php_port_from_process()
            
            # 更新所有配置文件
            update_results = []
            for config_path in config_paths:
                success, error_msg = self.update_config_file(config_path, port)
                update_results.append({
                    "path": config_path,
                    "success": success,
                    "message": error_msg
                })
            
            # 统计结果
            success_count = sum(1 for r in update_results if r["success"])
            total_count = len(update_results)
            
            if success_count == total_count:
                status_msg = f"所有配置文件更新成功 ({success_count}/{total_count})"
                success_flag = True
            elif success_count > 0:
                status_msg = f"部分配置文件更新成功 ({success_count}/{total_count})"
                success_flag = False  # 部分成功也算失败，但显示不同信息
            else:
                status_msg = f"所有配置文件更新失败 ({success_count}/{total_count})"
                success_flag = False
            
            # 收集详细信息
            details = []
            for r in update_results:
                status = "✅" if r["success"] else "❌"
                details.append(f"{status} {os.path.basename(r['path'])}: {r['message']}")
            
            full_status = f"{status_msg}\n" + "\n".join(details)
            
            return {
                "port": port,
                "status": full_status,
                "config_path": config_paths[0],  # 保持向后兼容
                "config_paths": config_paths,    # 新增：所有配置文件路径
                "success": success_flag,
                "video_url": "https://vd4.bdstatic.com/mda-kmbika46ppvf7nzc/v1-cae/1080p/mda-kmbika46ppvf7nzc.mp4",
                "update_results": update_results  # 详细结果
            }
                
        except Exception as e:
            return {
                "port": 9980,
                "status": f"检测失败: {str(e)[:100]}",
                "config_path": config_paths[0],
                "config_paths": config_paths,
                "success": False,
                "video_url": "https://vd4.bdstatic.com/mda-kmbika46ppvf7nzc/v1-cae/1080p/mda-kmbika46ppvf7nzc.mp4"
            }
    
    def detect_php_port_from_process(self):
        """只通过进程检测获取PHP端口"""
        
        # 方法1: 使用ps aux命令
        try:
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'php' in line.lower() and 'grep' not in line:
                        numbers = re.findall(r':(\d{4,5})', line)
                        for num in numbers:
                            port = int(num)
                            if 1024 <= port <= 65535:
                                return port
        except:
            pass
        
        # 方法2: 使用pgrep
        try:
            result = subprocess.run(
                ['pgrep', '-lf', 'php'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'php' in line.lower():
                        numbers = re.findall(r':(\d{4,5})', line)
                        for num in numbers:
                            port = int(num)
                            if 1024 <= port <= 65535:
                                return port
        except:
            pass
        
        # 方法3: 使用shell组合命令
        try:
            result = subprocess.run(
                'ps aux | grep php | grep -v grep',
                shell=True,
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        numbers = re.findall(r':(\d{4,5})', line)
                        for num in numbers:
                            port = int(num)
                            if 1024 <= port <= 65535:
                                return port
        except:
            pass
        
        # 默认端口
        return 9980
    
    def update_config_file(self, config_path, new_port):
        """更新指定路径的config.json文件"""
        try:
            if not os.path.exists(config_path):
                return False, f"配置文件不存在: {config_path}"
            
            if not os.access(config_path, os.W_OK):
                return False, f"没有写入权限: {config_path}"
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            updated_count = 0
            if 'sites' in config and isinstance(config['sites'], list):
                for i, site in enumerate(config['sites']):
                    if 'api' in site and isinstance(site['api'], str):
                        api = site['api']
                        old_api = api
                        
                        # 替换所有127.0.0.1:端口
                        api = re.sub(
                            r'http://127\.0\.0\.1:\d+',
                            f'http://127.0.0.1:{new_port}',
                            api
                        )
                        
                        if old_api != api:
                            config['sites'][i]['api'] = api
                            updated_count += 1
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            file_size = os.path.getsize(config_path)
            if file_size > 0:
                return True, f"更新了 {updated_count} 个站点"
            else:
                return False, "文件写入失败"
            
        except json.JSONDecodeError as e:
            return False, f"JSON解析失败: {e}"
        except Exception as e:
            return False, f"更新失败: {str(e)}"
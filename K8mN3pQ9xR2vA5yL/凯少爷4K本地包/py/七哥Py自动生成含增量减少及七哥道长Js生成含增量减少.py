
import os
import json
import glob
import sys
import random
import string

# 常量混淆
_0x1a2b3c = "py"
_0x4d5e6f = "js" 
_0x7a8b9c = "./js/drpy2.min.js"
_0xabcdef = ["drpy2.min.js", "drpy-core-lite.min.js"]

# 随机函数名
def _0xf1e2d3():
    if not os.path.exists(_0x1a2b3c) or not os.path.isdir(_0x1a2b3c):
        return []
    return [os.path.basename(f) for f in glob.glob(os.path.join(_0x1a2b3c, "*.py"))]

def _0xa1b2c3():
    if not os.path.exists(_0x4d5e6f) or not os.path.isdir(_0x4d5e6f):
        return []
    all_files = glob.glob(os.path.join(_0x4d5e6f, "*.js"))
    return [os.path.basename(f) for f in all_files if os.path.basename(f) not in _0xabcdef]

def _0xd4e5f6(mode="all"):
    _0xconfig = {
        "spider": "./yt内置.jar",
        "wallpaper": "https://tuapi.eees.cc/api.php?category=fengjing&type=302",
        "sites": [],
        "parses": [
            {"name": "解析聚合", "type": 3, "url": "Web"},
            {"name": "777", "type": 0, "url": "https://www.huaqi.live/?url="},
            {"name": "jsonplayer", "type": 0, "url": "https://jx.jsonplayer.com/player/?url="},
            {"name": "xmflv", "type": 0, "url": "https://jx.xmflv.com/?url="}
        ],
        "flags": ["youku", "tudou", "qq", "qiyi", "iqiyi", "leshi", "letv", "sohu", "imgo", "mgtv", "bilibili", "pptv", "PPTV", "migu"],
        "doh": [
            {"name": "Google", "url": "https://dns.google/dns-query", "ips": ["8.8.4.4", "8.8.8.8"]},
            {"name": "Cloudflare", "url": "https://cloudflare-dns.com/dns-query", "ips": ["1.1.1.1", "1.0.0.1", "2606:4700:4700::1111", "2606:4700:4700::1001"]},
            {"name": "AdGuard", "url": "https://dns.adguard.com/dns-query", "ips": ["94.140.14.140", "94.140.14.141"]},
            {"name": "DNSWatch", "url": "https://resolver2.dns.watch/dns-query", "ips": ["84.200.69.80", "84.200.70.40"]},
            {"name": "Quad9", "url": "https://dns.quad9.net/dns-query", "ips": ["9.9.9.9", "149.112.112.112"]}
        ],
        "lives": [
            {"name": "MY live-catvod", "type": "0", "ua": "okhttp/3.15", "url": "https://live.catvod.com/tv.m3u"},
            {"name": "MY live-catvod-local", "type": "0", "ua": "okhttp/3.15", "url": "http://127.0.0.1:9978/file/lives/Live-catvod.txt"},
            {"name": "MQiTV", "api": "csp_MQiTV", "jar": "https://slink.ltd/https://raw.githubusercontent.com/sqspot/tac/refs/heads/main/jar/fmMQiTV.jar", "ext": "https://59.125.210.231:4433", "playerType": 1, "epg": "http://epg.112114.xyz/?ch={name}&date={date}"},
            {"name": "肥羊国内直播", "type": 3, "api": "csp_Feiyang", "url": "tv.m3u", "ext": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/lystv/fmapp/ok/apk/allinone/v7/allinone;md5;https://mirror.ghproxy.com/https://raw.githubusercontent.com/lystv/fmapp/ok/apk/allinone/v7/md5", "jar": "https://mirror.ghproxy.com/https://raw.githubusercontent.com/FongMi/CatVodSpider/main/jar/custom_spider.jar"}
        ]
    }
    
    if mode == "increment":
        _0xb2c3d4(_0xconfig)
    elif mode == "sync":
        _0xc3d4e5(_0xconfig)
    else:
        _0xe5f6a7(_0xconfig)

def _0xe5f6a7(_0xcfg):
    """全新生成配置 - 显示详细添加内容"""
    _0xpy = _0xf1e2d3()
    _0xjs = _0xa1b2c3()
    
    if not _0xpy and not _0xjs:
        print("❌ 没有找到任何文件")
        return
    
    print("🔄 开始全新生成配置...")
    _0xsites = []
    _0xadded_py = []
    _0xadded_js = []
    
    # 添加Python站点
    for _0xf in _0xpy:
        _0xname = os.path.splitext(_0xf)[0]
        _0xsites.append({
            "key": _0xname, "name": _0xname, "type": 3,
            "api": f"./{_0x1a2b3c}/{_0xf}",
            "searchable": 1, "quickSearch": 0, "filterable": 0, "changeable": 0
        })
        _0xadded_py.append(_0xname)
    
    # 添加JavaScript站点
    for _0xf in _0xjs:
        _0xname = os.path.splitext(_0xf)[0]
        _0xsites.append({
            "key": _0xname, "name": _0xname, "type": 3,
            "api": _0x7a8b9c, "ext": f"./{_0x4d5e6f}/{_0xf}",
            "searchable": 1, "quickSearch": 0, "filterable": 0, "changeable": 0
        })
        _0xadded_js.append(_0xname)
    
    _0xcfg["sites"] = _0xsites
    
    # 显示添加的详细内容
    print("\n📊 全新生成详细报告:")
    print(f"   添加的Python站点 ({len(_0xadded_py)}个):")
    for i, name in enumerate(_0xadded_py, 1):
        print(f"     ✅ {i:2d}. {name}")
    
    print(f"   添加的JavaScript站点 ({len(_0xadded_js)}个):")
    for i, name in enumerate(_0xadded_js, 1):
        print(f"     ✅ {i:2d}. {name}")
    
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(_0xcfg, f, ensure_ascii=False, indent=4)
    
    print(f"\n🎉 配置文件已生成: config.json")
    print(f"📁 总共添加了 {len(_0xsites)} 个站点")
    print(f"   - Python站点: {len(_0xadded_py)} 个")
    print(f"   - JavaScript站点: {len(_0xadded_js)} 个")

def _0xb2c3d4(_0xcfg):
    """增量更新配置 - 显示新增内容"""
    if not os.path.exists("config.json"):
        print("⚠️  配置文件不存在，将创建新配置")
        _0xe5f6a7(_0xcfg)
        return
    
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            _0xold = json.load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return
    
    _0xkeys = {_0xs["key"] for _0xs in _0xold.get("sites", [])}
    _0xcfg["sites"] = _0xold["sites"]
    
    _0xpy = _0xf1e2d3()
    _0xjs = _0xa1b2c3()
    
    _0xnew_py = [(os.path.splitext(f)[0], f) for f in _0xpy 
                if os.path.splitext(f)[0] not in _0xkeys]
    _0xnew_js = [(os.path.splitext(f)[0], f) for f in _0xjs 
                 if os.path.splitext(f)[0] not in _0xkeys]
    
    if not _0xnew_py and not _0xnew_js:
        print("✅ 没有发现新的文件需要添加")
        return
    
    print("🔄 开始增量更新配置...")
    
    # 显示新增内容
    print("\n📊 增量更新详细报告:")
    
    if _0xnew_py:
        print(f"   新增的Python站点 ({len(_0xnew_py)}个):")
        for i, (_0xname, _0xfile) in enumerate(_0xnew_py, 1):
            _0xcfg["sites"].append({
                "key": _0xname, "name": _0xname, "type": 3,
                "api": f"./{_0x1a2b3c}/{_0xfile}",
                "searchable": 1, "quickSearch": 0, "filterable": 0, "changeable": 0
            })
            print(f"     ➕ {i:2d}. {_0xname}")
    
    if _0xnew_js:
        print(f"   新增的JavaScript站点 ({len(_0xnew_js)}个):")
        for i, (_0xname, _0xfile) in enumerate(_0xnew_js, 1):
            _0xcfg["sites"].append({
                "key": _0xname, "name": _0xname, "type": 3,
                "api": _0x7a8b9c, "ext": f"./{_0x4d5e6f}/{_0xfile}",
                "searchable": 1, "quickSearch": 0, "filterable": 0, "changeable": 0
            })
            print(f"     ➕ {i:2d}. {_0xname}")
    
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(_0xcfg, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 配置文件已更新: config.json")
    print(f"📈 新增了 {len(_0xnew_py) + len(_0xnew_js)} 个站点")
    print(f"   - Python站点: {len(_0xnew_py)} 个")
    print(f"   - JavaScript站点: {len(_0xnew_js)} 个")

def _0xc3d4e5(_0xcfg):
    """同步更新配置 - 显示添加和删除的详细内容"""
    if not os.path.exists("config.json"):
        print("⚠️  配置文件不存在，将创建新配置")
        _0xe5f6a7(_0xcfg)
        return
    
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            _0xold = json.load(f)
    except Exception as e:
        print(f"❌ 读取配置文件失败: {e}")
        return
    
    _0xpy = _0xf1e2d3()
    _0xjs = _0xa1b2c3()
    
    _0xcurrent = {os.path.splitext(f)[0] for f in _0xpy}
    _0xcurrent.update({os.path.splitext(f)[0] for f in _0xjs})
    
    _0xold_sites = _0xold.get("sites", [])
    _0xkept = [_0xs for _0xs in _0xold_sites if _0xs["key"] in _0xcurrent]
    _0xremoved = [_0xs for _0xs in _0xold_sites if _0xs["key"] not in _0xcurrent]
    
    _0xold_keys = {_0xs["key"] for _0xs in _0xold_sites}
    _0xnew_py = [(os.path.splitext(f)[0], f) for f in _0xpy 
                if os.path.splitext(f)[0] not in _0xold_keys]
    _0xnew_js = [(os.path.splitext(f)[0], f) for f in _0xjs 
                 if os.path.splitext(f)[0] not in _0xold_keys]
    
    _0xall_sites = _0xkept.copy()
    
    print("🔄 开始同步更新配置...")
    
    # 显示同步更新详细报告
    print("\n📊 同步更新详细报告:")
    print(f"   保留的站点: {len(_0xkept)} 个")
    
    # 显示删除的站点
    if _0xremoved:
        print(f"   删除的站点 ({len(_0xremoved)}个):")
        for i, site in enumerate(_0xremoved, 1):
            print(f"     ❌ {i:2d}. {site['key']}")
    else:
        print("   删除的站点: 0 个")
    
    # 显示新增的Python站点
    if _0xnew_py:
        print(f"   新增的Python站点 ({len(_0xnew_py)}个):")
        for i, (_0xname, _0xfile) in enumerate(_0xnew_py, 1):
            _0xall_sites.append({
                "key": _0xname, "name": _0xname, "type": 3,
                "api": f"./{_0x1a2b3c}/{_0xfile}",
                "searchable": 1, "quickSearch": 0, "filterable": 0, "changeable": 0
            })
            print(f"     ➕ {i:2d}. {_0xname}")
    else:
        print("   新增的Python站点: 0 个")
    
    # 显示新增的JavaScript站点
    if _0xnew_js:
        print(f"   新增的JavaScript站点 ({len(_0xnew_js)}个):")
        for i, (_0xname, _0xfile) in enumerate(_0xnew_js, 1):
            _0xall_sites.append({
                "key": _0xname, "name": _0xname, "type": 3,
                "api": _0x7a8b9c, "ext": f"./{_0x4d5e6f}/{_0xfile}",
                "searchable": 1, "quickSearch": 0, "filterable": 0, "changeable": 0
            })
            print(f"     ➕ {i:2d}. {_0xname}")
    else:
        print("   新增的JavaScript站点: 0 个")
    
    _0xcfg["sites"] = _0xall_sites
    
    with open("config.json", 'w', encoding='utf-8') as f:
        json.dump(_0xcfg, f, ensure_ascii=False, indent=4)
    
    print(f"\n✅ 配置文件已同步更新: config.json")
    print(f"📂 当前总共 {len(_0xall_sites)} 个站点")
    print(f"   - 保留: {len(_0xkept)} 个")
    print(f"   - 删除: {len(_0xremoved)} 个") 
    print(f"   - 新增: {len(_0xnew_py) + len(_0xnew_js)} 个")
    print(f"     (Python: {len(_0xnew_py)} 个, JavaScript: {len(_0xnew_js)} 个)")

def _0xf7a8b9():
    """显示目录信息"""
    print("=" * 60)
    print("配置文件生成器 (加密版)")
    print("=" * 60)
    
    current_dir = os.getcwd()
    print(f"📁 当前目录: {current_dir}")
    
    # 显示py文件夹信息
    _0xpy = _0xf1e2d3()
    if _0xpy:
        print(f"📂 py文件夹: {len(_0xpy)} 个Python文件")
        for i, f in enumerate(_0xpy[:5], 1):
            print(f"     {i}. {f}")
        if len(_0xpy) > 5:
            print(f"     ... 还有 {len(_0xpy) - 5} 个文件")
    else:
        print("📂 py文件夹: 没有找到Python文件")
    
    # 显示js文件夹信息
    _0xjs = _0xa1b2c3()
    all_js = glob.glob(os.path.join(_0x4d5e6f, "*.js"))
    excluded_count = len(all_js) - len(_0xjs) if all_js else 0
    
    if _0xjs:
        print(f"📂 js文件夹: {len(_0xjs)} 个JavaScript文件 (已排除 {excluded_count} 个)")
        for i, f in enumerate(_0xjs[:5], 1):
            print(f"     {i}. {f}")
        if len(_0xjs) > 5:
            print(f"     ... 还有 {len(_0xjs) - 5} 个文件")
    else:
        print(f"📂 js文件夹: 没有找到JavaScript文件 (已排除 {excluded_count} 个)")

def _0xg8h9i0():
    """主函数"""
    _0xf7a8b9()
    
    print("\n请选择操作:")
    print("1. 全新生成配置 (覆盖所有)")
    print("2. 增量更新配置 (只添加新文件)")
    print("3. 同步更新配置 (添加新文件 + 删除不存在的文件)")
    print("4. 退出")
    
    while True:
        _0xchoice = input("\n请输入选择 (1-4): ").strip()
        if _0xchoice == "1":
            _0xd4e5f6("all")
            break
        elif _0xchoice == "2":
            _0xd4e5f6("increment")
            break
        elif _0xchoice == "3":
            _0xd4e5f6("sync")
            break
        elif _0xchoice == "4":
            print("👋 再见！")
            break
        else:
            print("❌ 无效选择，请重新输入")
    
    input("\n按回车键退出...")

if __name__ == "__main__":
    _0xg8h9i0()
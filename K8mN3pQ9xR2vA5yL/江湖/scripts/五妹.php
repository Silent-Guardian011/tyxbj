<?php
/**
 * TVBox PHP 爬虫脚本 - 完整增强版
 * 支持JSON/TXT/M3U/DB文件格式 + 磁力链接 + ed2k链接 + 音频媒体库 + 视频媒体中心 + 文件夹分类
 * 完整磁力文件夹扫描和智能命名功能 + 完整调试系统
 */

// 初始化调试系统
初始化调试助手(true, '/storage/emulated/0/江湖/debug/', ['系统', '文件扫描', '目录扫描', '数据库', 'JSON解析', 'TXT解析', 'M3U解析', '音频扫描', '视频扫描', '分类处理', '性能监控'], 1);

ini_set('memory_limit', '-1');
// 获取请求参数
$操作类型 = $_GET['ac'] ?? 'detail';
$分类标识 = $_GET['t'] ?? '';
$页码 = $_GET['pg'] ?? '1';
$视频标识 = $_GET['ids'] ?? '';
$搜索关键词 = $_GET['wd'] ?? '';
$播放标志 = $_GET['flag'] ?? '';
$播放标识 = $_GET['id'] ?? '';

// 设置响应头为 JSON
header('Content-Type: application/json; charset=utf-8');

// 性能优化 - 增加超时时间
@set_time_limit(30);

// 根据不同 action 返回数据
switch ($操作类型) {
    case 'detail':
        if (!empty($视频标识)) {
            $结果 = 获取详情($视频标识);
        } elseif (!empty($分类标识)) {
            $结果 = 获取分类($分类标识, $页码);
        } else {
            $结果 = 获取首页();
        }
        break;
    
    case 'search':
        $结果 = 搜索($搜索关键词, $页码);
        break;
        
    case 'play':
        $结果 = 获取播放($播放标志, $播放标识);
        break;
    
    default:
        $结果 = ['错误' => '未知操作: ' . $操作类型];
}

echo json_encode($结果, JSON_UNESCAPED_UNICODE);

/**
 * 完整独立调试功能模块 - 带手动开关
 */
class 调试助手 {
    private $调试模式;
    private $手动调试开关;
    private $日志目录;
    private $日志文件;
    private $调试收集器;
    private $允许的分类 = [];
    
    public function __construct($调试模式 = false, $日志目录 = null, $允许的分类 = [], $手动开关 = null) {
        $this->调试模式 = $调试模式;
        
        // 手动开关设置
        if ($手动开关 !== null) {
            $this->手动调试开关 = (bool)$手动开关;
        } else {
            $this->手动调试开关 = null;
        }
        
        $this->日志目录 = $日志目录 ?: '/storage/emulated/0/江湖/debug/';
        $this->日志文件 = [
            'system' => '调试文件.txt',
            'database' => '数据库调试.txt', 
            'play' => '播放日志.txt',
            'scan' => '文件扫描日志.txt',
            'media' => '媒体库日志.txt'
        ];
        $this->调试收集器 = new 调试收集器();
        $this->允许的分类 = $允许的分类;
        
        // 根据手动开关状态决定是否初始化调试
        $最终调试状态 = $this->获取最终调试状态();
        if ($最终调试状态) {
            $this->初始化调试();
        }
    }
    
    /**
     * 获取最终调试状态（优先使用手动开关）
     */
    private function 获取最终调试状态() {
        if ($this->手动调试开关 !== null) {
            return $this->手动调试开关;
        }
        return $this->调试模式;
    }
    
    /**
     * 初始化调试系统
     */
    private function 初始化调试() {
        if (!is_dir($this->日志目录)) {
            mkdir($this->日志目录, 0755, true);
        }
        
        foreach ($this->日志文件 as $文件) {
            $完整路径 = $this->日志目录 . $文件;
            file_put_contents($完整路径, "=== 调试日志生成时间: " . date('Y-m-d H:i:s') . " ===\n\n", FILE_APPEND);
        }
        
        $this->记录到文件('系统', "调试系统初始化完成");
        $this->记录到文件('系统', "手动开关状态: " . ($this->手动调试开关 !== null ? ($this->手动调试开关 ? '开启(1)' : '关闭(0)') : '未设置(自动模式)'));
    }
    
    /**
     * 检查是否允许记录该分类
     */
    private function 分类是否允许($分类) {
        if (empty($this->允许的分类)) {
            return true;
        }
        return in_array($分类, $this->允许的分类);
    }
    
    /**
     * 记录调试信息到文件
     */
    public function 记录到文件($分类, $消息) {
        if (!$this->获取最终调试状态()) {
            return;
        }
        
        if (!$this->分类是否允许($分类)) {
            return;
        }
        
        $时间戳 = date('Y-m-d H:i:s');
        
        $文件映射 = [
            '文件扫描' => '文件扫描日志.txt',
            '目录扫描' => '文件扫描日志.txt',
            '音频扫描' => '媒体库日志.txt',
            '视频扫描' => '媒体库日志.txt',
            '分类处理' => '媒体库日志.txt',
            '系统' => '调试文件.txt',
            '性能监控' => '调试文件.txt',
            '错误追踪' => '调试文件.txt',
            '数据库' => '数据库调试.txt',
            'JSON解析' => '调试文件.txt',
            'TXT解析' => '调试文件.txt',
            'M3U解析' => '调试文件.txt'
        ];
        
        $文件名 = $文件映射[$分类] ?? '调试文件.txt';
        $日志条目 = "[{$时间戳}] {$分类}: {$消息}\n";
        
        file_put_contents($this->日志目录 . $文件名, $日志条目, FILE_APPEND);
    }
    
    /**
     * 记录调试信息（带数据）
     */
    public function 记录调试($分类, $消息, $数据 = null) {
        if (!$this->获取最终调试状态()) {
            return;
        }
        
        if (!$this->分类是否允许($分类)) {
            return;
        }
        
        $日志消息 = $消息;
        if ($数据 !== null) {
            $日志消息 .= " - 数据: " . (is_string($数据) ? $数据 : json_encode($数据, JSON_UNESCAPED_UNICODE));
        }
        $this->记录到文件($分类, $日志消息);
        $this->调试收集器->记录($分类, $消息, $数据);
    }
    
    /**
     * 设置手动开关 (0=关闭, 1=开启)
     */
    public function 设置手动开关($开关状态) {
        $this->手动调试开关 = (bool)$开关状态;
        $状态文本 = $开关状态 ? '开启(1)' : '关闭(0)';
        $this->记录到文件('系统', "手动开关设置为: {$状态文本}");
        return $this;
    }
    
    /**
     * 获取手动开关状态
     */
    public function 获取手动开关() {
        return $this->手动调试开关;
    }
    
    /**
     * 清除手动开关（恢复自动模式）
     */
    public function 清除手动开关() {
        $this->手动调试开关 = null;
        $this->记录到文件('系统', "手动开关已清除，恢复自动模式");
        return $this;
    }
    
    /**
     * 获取当前调试状态详情
     */
    public function 获取调试状态() {
        $最终状态 = $this->获取最终调试状态();
        $模式说明 = $this->手动调试开关 !== null ? '手动模式' : '自动模式';
        $开关状态 = $this->手动调试开关 !== null ? ($this->手动调试开关 ? '开启(1)' : '关闭(0)') : '自动(' . ($this->调试模式 ? '开' : '关') . ')';
        
        return [
            '最终状态' => $最终状态,
            '模式' => $模式说明,
            '开关状态' => $开关状态,
            '自动模式状态' => $this->调试模式,
            '手动开关状态' => $this->手动调试开关,
            '允许的分类' => $this->允许的分类,
            '日志目录' => $this->日志目录,
            '总记录数' => $this->调试收集器->获取汇总()['总记录数'] ?? 0
        ];
    }
    
    /**
     * 开始计时
     */
    public function 开始计时($标签) {
        if (!$this->获取最终调试状态()) return;
        $this->调试收集器->开始计时($标签);
    }
    
    /**
     * 结束计时
     */
    public function 结束计时($标签) {
        if (!$this->获取最终调试状态()) return;
        $耗时 = $this->调试收集器->结束计时($标签);
        $this->记录到文件('性能监控', "{$标签} 耗时: {$耗时}秒");
        return $耗时;
    }
    
    /**
     * 记录错误
     */
    public function 记录错误($错误信息, $错误数据 = null) {
        $this->记录调试('错误追踪', $错误信息, $错误数据);
    }
}

/**
 * 调试收集器类
 */
class 调试收集器 {
    private $记录 = [];
    private $计时器 = [];
    
    public function 记录($分类, $消息, $数据 = null) {
        $时间戳 = microtime(true);
        $this->记录[] = [
            '时间' => $时间戳,
            '分类' => $分类,
            '消息' => $消息,
            '数据' => $数据
        ];
        
        // 限制记录数量，防止内存溢出
        if (count($this->记录) > 1000) {
            array_shift($this->记录);
        }
    }
    
    public function 开始计时($标签) {
        $this->计时器[$标签] = microtime(true);
    }
    
    public function 结束计时($标签) {
        if (!isset($this->计时器[$标签])) {
            return 0;
        }
        $开始时间 = $this->计时器[$标签];
        $结束时间 = microtime(true);
        unset($this->计时器[$标签]);
        return round($结束时间 - $开始时间, 4);
    }
    
    public function 获取汇总() {
        $分类统计 = [];
        foreach ($this->记录 as $记录) {
            $分类 = $记录['分类'];
            if (!isset($分类统计[$分类])) {
                $分类统计[$分类] = 0;
            }
            $分类统计[$分类]++;
        }
        
        return [
            '总记录数' => count($this->记录),
            '分类统计' => $分类统计
        ];
    }
}

/**
 * 全局调试助手实例
 */
$全局调试助手 = null;

/**
 * 初始化全局调试助手
 */
function 初始化调试助手($调试模式 = false, $日志目录 = null, $允许的分类 = [], $手动开关 = null) {
    global $全局调试助手;
    $全局调试助手 = new 调试助手($调试模式, $日志目录, $允许的分类, $手动开关);
    return $全局调试助手;
}

/**
 * 设置手动调试开关
 */
function 设置手动调试开关($开关状态) {
    global $全局调试助手;
    if ($全局调试助手) {
        return $全局调试助手->设置手动开关($开关状态);
    }
    return null;
}

/**
 * 清除手动调试开关
 */
function 清除手动调试开关() {
    global $全局调试助手;
    if ($全局调试助手) {
        return $全局调试助手->清除手动开关();
    }
    return null;
}

/**
 * 获取调试状态详情
 */
function 获取调试状态详情() {
    global $全局调试助手;
    return $全局调试助手 ? $全局调试助手->获取调试状态() : null;
}

/**
 * 调试日志函数
 */
function 调试日志($分类, $消息, $数据 = null) {
    global $全局调试助手;
    if ($全局调试助手) {
        $全局调试助手->记录调试($分类, $消息, $数据);
    }
}

/**
 * 开始性能计时
 */
function 开始计时($标签) {
    global $全局调试助手;
    if ($全局调试助手) {
        $全局调试助手->开始计时($标签);
    }
}

/**
 * 结束性能计时
 */
function 结束计时($标签) {
    global $全局调试助手;
    if ($全局调试助手) {
        return $全局调试助手->结束计时($标签);
    }
    return 0;
}

/**
 * 递归扫描目录 - 支持无限级子文件夹
 */
function 递归扫描目录($目录, $文件类型, $当前深度 = 0, $最大深度 = 20) {
    开始计时('递归扫描目录');
    
    $文件列表 = [];
    
    if (!is_dir($目录)) {
        调试日志('目录扫描', "目录不存在: {$目录}");
        结束计时('递归扫描目录');
        return $文件列表;
    }
    
    if ($当前深度 > $最大深度) {
        调试日志('目录扫描', "达到最大深度限制: {$目录}");
        结束计时('递归扫描目录');
        return $文件列表;
    }
    
    $目录项 = @scandir($目录);
    if ($目录项 === false) {
        调试日志('目录扫描', "无法扫描目录: {$目录}");
        结束计时('递归扫描目录');
        return $文件列表;
    }
    
    $扫描计数 = 0;
    foreach ($目录项 as $项目) {
        if ($项目 === '.' || $项目 === '..') continue;
        
        $路径 = $目录 . $项目;
        
        if (is_dir($路径)) {
            $子文件 = 递归扫描目录($路径 . '/', $文件类型, $当前深度 + 1, $最大深度);
            $文件列表 = array_merge($文件列表, $子文件);
            $扫描计数 += count($子文件);
        } else {
            $扩展名 = strtolower(pathinfo($路径, PATHINFO_EXTENSION));
            if (in_array($扩展名, $文件类型)) {
                $相对路径 = str_replace('/storage/emulated/0/江湖/', '', $路径);
                
                // 检查是否为磁力文件夹
                $是磁力文件夹 = (strpos($路径, '/江湖/wj/bt/') !== false);
                
                $文件列表[] = [
                    'type' => $扩展名,
                    'path' => $路径,
                    'name' => $项目,
                    'filename' => pathinfo($项目, PATHINFO_FILENAME),
                    'relative_path' => $相对路径,
                    'depth' => $当前深度,
                    'is_magnet_folder' => $是磁力文件夹
                ];
                $扫描计数++;
            }
        }
    }
    
    调试日志('目录扫描', "扫描目录完成: {$目录}, 深度: {$当前深度}, 找到文件: {$扫描计数}个");
    结束计时('递归扫描目录');
    
    return $文件列表;
}

/**
 * 扫描媒体文件 - 新增音频和视频文件扫描
 */
function 扫描媒体文件($媒体类型 = 'all') {
    开始计时('扫描媒体文件');
    
    $音频格式 = ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma'];
    $视频格式 = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'm4v', '3gp', 'webm'];
    
    $扫描目录 = '/storage/emulated/0/江湖/';
    $媒体文件 = [];
    
    if ($媒体类型 === 'audio' || $媒体类型 === 'all') {
        调试日志('音频扫描', '开始扫描音频文件');
        $音频文件 = 递归扫描目录($扫描目录, $音频格式);
        调试日志('音频扫描', "找到音频文件: " . count($音频文件) . "个");
        $媒体文件 = array_merge($媒体文件, $音频文件);
    }
    
    if ($媒体类型 === 'video' || $媒体类型 === 'all') {
        调试日志('视频扫描', '开始扫描视频文件');
        $视频文件 = 递归扫描目录($扫描目录, $视频格式);
        调试日志('视频扫描', "找到视频文件: " . count($视频文件) . "个");
        $媒体文件 = array_merge($媒体文件, $视频文件);
    }
    
    调试日志('媒体扫描', "媒体扫描完成，总计: " . count($媒体文件) . "个文件");
    结束计时('扫描媒体文件');
    
    return $媒体文件;
}

/**
 * 获取所有文件列表 - 增强磁力文件夹支持
 */
function 获取所有文件() {
    static $所有文件 = null;
    
    if ($所有文件 === null) {
        $所有文件 = [];
        
        $JSON文件 = 递归扫描目录('/storage/emulated/0/江湖/json/影视/', ['json']);
        $TXT文件 = 递归扫描目录('/storage/emulated/0/江湖/wj/', ['txt']);
        $M3U文件 = array_merge(
            递归扫描目录('/storage/emulated/0/江湖/json/影视/', ['m3u']),
            递归扫描目录('/storage/emulated/0/江湖/wj/', ['m3u'])
        );
        
        // 增强数据库文件扫描，包含bt磁力文件夹
        $数据库文件 = array_merge(
            递归扫描目录('/storage/emulated/0/江湖/json/影视/', ['db']),
            递归扫描目录('/storage/emulated/0/江湖/wj/', ['db']),
            递归扫描目录('/storage/emulated/0/江湖/db/', ['db']),
            递归扫描目录('/storage/emulated/0/江湖/wj/bt/', ['db'])
        );
        
        $所有文件 = array_merge($JSON文件, $TXT文件, $M3U文件, $数据库文件);
        
        // 按路径排序
        usort($所有文件, function($甲, $乙) {
            return strcmp($甲['relative_path'], $乙['relative_path']);
        });
        
        调试日志('文件扫描', "所有文件扫描完成，总计: " . count($所有文件) . "个文件");
    }
    
    return $所有文件;
}

/**
 * 获取媒体文件分类 - 新增音频和视频分类
 */
function 获取媒体文件分类($媒体类型) {
    static $媒体分类缓存 = [];
    
    if (isset($媒体分类缓存[$媒体类型])) {
        return $媒体分类缓存[$媒体类型];
    }
    
    $媒体文件 = 扫描媒体文件($媒体类型);
    
    if (empty($媒体文件)) {
        $媒体分类缓存[$媒体类型] = [];
        return [];
    }
    
    // 文件夹分类处理
    $文件夹分类 = [];
    foreach ($媒体文件 as $文件) {
        $文件夹路径 = dirname($文件['relative_path']);
        $文件夹名称 = basename($文件夹路径);
        
        if ($文件夹路径 === '.') {
            $文件夹路径 = '根目录';
            $文件夹名称 = '根目录';
        }
        
        if (!isset($文件夹分类[$文件夹路径])) {
            $文件夹分类[$文件夹路径] = [
                'name' => $文件夹名称,
                'path' => $文件夹路径,
                'files' => [],
                'file_count' => 0
            ];
        }
        
        $文件夹分类[$文件夹路径]['files'][] = $文件;
        $文件夹分类[$文件夹路径]['file_count']++;
    }
    
    // 转换为分类列表
    $分类列表 = [];
    $索引 = 0;
    
    foreach ($文件夹分类 as $文件夹路径 => $文件夹信息) {
        $类型名称 = ($媒体类型 === 'audio' ? '🎵 ' : '🎬 ') . $文件夹信息['name'] . ' (' . $文件夹信息['file_count'] . '个文件)';
        
        $分类列表[] = [
            'type_id' => 'media_' . $媒体类型 . '_' . (++$索引),
            'type_name' => $类型名称,
            'type_file' => $文件夹路径,
            'source_path' => $文件夹路径,
            'source_type' => $媒体Type,
            'media_type' => $媒体类型,
            'file_count' => $文件夹信息['file_count'],
            'is_media_folder' => true
        ];
    }
    
    $媒体分类缓存[$媒体类型] = $分类列表;
    调试日志('分类处理', "{$媒体Type}媒体分类完成，分类数: " . count($分类列表));
    
    return $分类列表;
}

/**
 * 估算文件中的视频数量（快速估算，不实际解析）
 */
function 估算文件视频数量($文件) {
    $路径 = $文件['path'];
    $类型 = $文件['type'];
    
    if (!file_exists($路径)) {
        return 0;
    }
    
    $文件大小 = filesize($路径);
    
    // 根据文件类型和大小快速估算
    switch ($类型) {
        case 'json':
            $数量 = $文件大小 > 1024 ? intval($文件大小 / 1024) : 1;
            break;
        case 'txt':
            $行数 = $文件大小 > 100 ? intval($文件大小 / 100) : 1;
            $数量 = min($行数, 10000);
            break;
        case 'm3u':
            $行数 = $文件大小 > 200 ? intval($文件大小 / 200) : 1;
            $数量 = min($行数, 5000);
            break;
        case 'db':
            $数量 = $文件大小 > 500 ? intval($文件大小 / 500) : 1;
            break;
        default:
            $数量 = 0;
    }
    
    return $数量;
}

/**
 * 获取分类列表
 */
function 获取分类列表() {
    static $分类列表 = null;
    
    if ($分类列表 === null) {
        $分类列表 = [];
        
        // 新增热门推荐分类
        $所有文件 = 获取所有文件();
        $总文件数 = count($所有文件);
        $分类列表[] = [
            'type_id' => 'hot',
            'type_name' => '🔥热门推荐 (' . $总文件数 . '个文件)',
            'type_file' => 'hot_recommend',
            'source_path' => 'hot',
            'source_type' => 'hot'
        ];
        
        // 新增音频媒体库分类
        $音频分类 = 获取媒体文件分类('audio');
        if (!empty($音频分类)) {
            $分类列表[] = [
                'type_id' => 'audio_library',
                'type_name' => '🎵 音频媒体库 (' . count($音频分类) . '个分类)',
                'type_file' => 'audio_library',
                'source_path' => 'audio',
                'source_type' => 'audio_library'
            ];
        }
        
        // 新增视频媒体中心分类
        $视频分类 = 获取媒体文件分类('video');
        if (!empty($视频分类)) {
            $分类列表[] = [
                'type_id' => 'video_center',
                'type_name' => '🎬 视频媒体中心 (' . count($视频分类) . '个分类)',
                'type_file' => 'video_center',
                'source_path' => 'video',
                'source_type' => 'video_center'
            ];
        }
        
        // 用于去重的数组
        $已处理文件 = [];
        
        // 文件分类（显示所有文件）
        foreach ($所有文件 as $索引 => $文件) {
            // 去重：基于文件路径和名称
            $文件标识 = $文件['path'] . '|' . $文件['name'];
            if (in_array($文件标识, $已处理文件)) {
                continue;
            }
            $已处理文件[] = $文件标识;
            
            $文件类型 = '';
            $类型图标 = '';
            
            switch ($文件['type']) {
                case 'json':
                    $文件类型 = '[JSON] ';
                    $类型图标 = '📊 ';
                    break;
                case 'txt':
                    $文件类型 = '[TXT] ';
                    $类型图标 = '📄 ';
                    break;
                case 'm3u':
                    $文件类型 = '[M3U] ';
                    $类型图标 = '📺 ';
                    break;
                case 'db':
                    $文件类型 = '[数据库] ';
                    $类型图标 = '🗃️ ';
                    break;
            }
            
            // 磁力文件夹标识
            if ($文件['is_magnet_folder']) {
                $类型图标 = '🧲 ';
                $文件类型 = '[磁力] ';
            }
            
            // 显示文件夹路径
            $文件夹信息 = '';
            if (strpos($文件['relative_path'], '/') !== false) {
                $文件夹路径 = dirname($文件['relative_path']);
                $文件夹信息 = ' 📁 ' . $文件夹路径;
            }
            
            // 估算每个文件的视频数量
            $视频数量 = 估算文件视频数量($文件);
            $数量显示 = $视频数量 > 0 ? ' (' . number_format($视频数量) . '个视频)' : '';
            
            $分类列表[] = [
                'type_id' => (string)($索引 + 1000), // 从1000开始避免冲突
                'type_name' => $类型图标 . $文件类型 . $文件['filename'] . $数量显示 . $文件夹信息,
                'type_file' => $文件['name'],
                'source_path' => $文件['path'],
                'source_type' => $文件['type'],
                'video_count' => $视频数量,
                'is_magnet_folder' => $文件['is_magnet_folder']
            ];
        }
        
        if (empty($所有文件) && empty($音频分类) && empty($视频分类)) {
            $分类列表[] = [
                'type_id' => '1',
                'type_name' => '❓ 未找到媒体文件',
                'type_file' => 'empty',
                'source_path' => 'empty',
                'source_type' => 'empty'
            ];
        }
        
        调试日志('分类处理', "分类列表生成完成，总计: " . count($分类列表) . "个分类");
    }
    
    return $分类列表;
}

/**
 * 解析媒体文件夹内容
 */
function 解析媒体文件夹($文件夹路径, $媒体类型) {
    开始计时('解析媒体文件夹');
    
    $媒体文件 = 扫描媒体文件($媒体类型);
    $文件夹媒体 = [];
    
    foreach ($媒体文件 as $文件) {
        $文件文件夹路径 = dirname($文件['relative_path']);
        
        if ($文件文件夹路径 === $文件夹路径 || 
            ($文件夹路径 === '根目录' && $文件文件夹路径 === '.')) {
            
            $播放来源 = $媒体类型 === 'audio' ? '🎵 音频文件' : '🎬 视频文件';
            $备注 = $媒体类型 === 'audio' ? '音频' : '视频';
            
            $文件夹媒体[] = [
                'vod_id' => 'media_' . $媒体类型 . '_' . md5($文件['path']),
                'vod_name' => $文件['filename'],
                'vod_pic' => $媒体类型 === 'audio' ? 
                    'https://www.252035.xyz/imgs?t=audio_icon' : 
                    'https://www.252035.xyz/imgs?t=video_icon',
                'vod_remarks' => $备注,
                'vod_year' => date('Y'),
                'vod_area' => '本地文件',
                'vod_content' => $文件['name'] . ' - ' . $文件['relative_path'],
                'vod_play_from' => $播放来源,
                'vod_play_url' => '播放$' . $文件['path'],
                'file_path' => $文件['path'],
                'file_type' => $文件['type']
            ];
        }
    }
    
    调试日志('媒体扫描', "解析媒体文件夹: {$文件夹路径}, 找到媒体文件: " . count($文件夹媒体) . "个");
    结束计时('解析媒体文件夹');
    
    return $文件夹媒体;
}

/**
 * 解析SQLite数据库文件内容 - 增强磁力链接和JSON支持
 */
function 解析数据库文件($文件路径) {
    开始计时('解析数据库文件');
    
    if (!file_exists($文件路径)) {
        调试日志('数据库', "数据库文件不存在: {$文件路径}");
        结束计时('解析数据库文件');
        return ['错误' => '数据库文件不存在: ' . basename($文件路径)];
    }
    
    $文件大小 = filesize($文件路径);
    $可读 = is_readable($文件路径);
    
    if ($文件大小 === 0) {
        调试日志('数据库', "数据库文件为空: {$文件路径}");
        结束计时('解析数据库文件');
        return ['错误' => '数据库文件为空: ' . basename($文件路径)];
    }
    
    if (!$可读) {
        调试日志('数据库', "数据库文件不可读: {$文件路径}");
        结束计时('解析数据库文件');
        return ['错误' => '数据库文件不可读: ' . basename($文件路径)];
    }
    
    if (!extension_loaded('pdo_sqlite')) {
        调试日志('数据库', "PDO_SQLite扩展不可用");
        结束计时('解析数据库文件');
        return ['错误' => 'PDO_SQLite扩展不可用，无法读取数据库文件'];
    }
    
    try {
        $数据库 = new PDO("sqlite:" . $文件路径);
        $数据库->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        
        $视频列表 = [];
        
        $表列表 = $数据库->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(PDO::FETCH_COLUMN);
        
        if (empty($表列表)) {
            调试日志('数据库', "数据库中未找到任何数据表: {$文件路径}");
            $数据库 = null;
            结束计时('解析数据库文件');
            return ['错误' => '数据库中未找到任何数据表'];
        }
        
        调试日志('数据库', "找到数据表: " . implode(', ', $表列表));
        
        $默认图片 = [
            'https://www.252035.xyz/imgs?t=1335527662'
        ];
        
        foreach ($表列表 as $表名) {
            if (strpos($表名, 'sqlite_') === 0) continue;
            
            $字段列表 = $数据库->query("PRAGMA table_info($表名)")->fetchAll(PDO::FETCH_ASSOC);
            $字段名称 = array_column($字段列表, 'name');
            
            // 特殊处理：如果表有data字段，假设它包含JSON数据
            if (in_array('data', $字段名称)) {
                $结果集 = $数据库->query("SELECT data FROM $表名")->fetchAll(PDO::FETCH_COLUMN);
                
                foreach ($结果集 as $索引 => $json数据) {
                    if (empty($json数据)) continue;
                    
                    $视频数据 = json_decode($json数据, true);
                    if ($视频数据 && is_array($视频数据)) {
                        $视频名称 = $视频数据['name'] ?? $视频数据['title'] ?? '未知视频';
                        $视频链接 = '';
                        $播放来源 = '数据库源';
                        
                        if (isset($视频数据['magnet']) && !empty($视频数据['magnet'])) {
                            $视频链接 = $视频数据['magnet'];
                            $播放来源 = '🧲磁力链接';
                        } elseif (isset($视频数据['magnet_url']) && !empty($视频数据['magnet_url'])) {
                            $视频链接 = $视频数据['magnet_url'];
                            $播放来源 = '🧲磁力链接';
                        } elseif (isset($视频数据['url']) && !empty($视频数据['url'])) {
                            $视频链接 = $视频数据['url'];
                            if (strpos($视频链接, 'magnet:') === 0) {
                                $播放来源 = '🧲磁力链接';
                            }
                        }
                        
                        if (empty($视频链接)) {
                            continue;
                        }
                        
                        $视频封面 = $视频数据['cover'] ?? $视频数据['image'] ?? $视频数据['poster'] ?? $默认图片[$索引 % count($默认图片)];
                        $视频描述 = $视频数据['description'] ?? $视频数据['desc'] ?? $视频数据['content'] ?? '《' . $视频名称 . '》的精彩内容';
                        $视频年份 = $视频数据['year'] ?? date('Y');
                        $视频地区 = $视频数据['area'] ?? $视频数据['region'] ?? '未知地区';
                        
                        $视频列表[] = [
                            'vod_id' => 'db_' . md5($文件路径) . '_' . $表名 . '_' . $索引,
                            'vod_name' => $视频名称,
                            'vod_pic' => $视频封面,
                            'vod_remarks' => '高清',
                            'vod_year' => $视频年份,
                            'vod_area' => $视频地区,
                            'vod_content' => $视频描述,
                            'vod_play_from' => $播放来源,
                            'vod_play_url' => '正片$' . $视频链接
                        ];
                    }
                }
            } else {
                $名称字段 = null;
                $链接字段 = null;
                $磁力字段 = null;
                $电驴字段 = null;
                $图片字段 = null;
                $描述字段 = null;
                $年份字段 = null;
                $地区字段 = null;
                $JSON字段 = null;
                
                foreach ($字段名称 as $字段) {
                    $小写字段 = strtolower($字段);
                    if (in_array($小写字段, ['name', 'title', 'vod_name', 'filename', 'video_name'])) {
                        $名称字段 = $字段;
                    } elseif (in_array($小写字段, ['url', 'link', 'vod_url', 'play_url', 'video_url', 'torrent'])) {
                        $链接字段 = $字段;
                    } elseif (in_array($小写字段, ['magnet', 'magnet_url', 'magnet_link'])) {
                        $磁力字段 = $字段;
                    } elseif (in_array($小写字段, ['ed2k', 'ed2k_url', 'ed2k_link'])) {
                        $电驴字段 = $字段;
                    } elseif (in_array($小写字段, ['pic', 'image', 'cover', 'vod_pic', 'poster'])) {
                        $图片字段 = $字段;
                    } elseif (in_array($小写字段, ['desc', 'description', 'content', 'vod_content'])) {
                        $描述字段 = $字段;
                    } elseif (in_array($小写字段, ['year', 'vod_year'])) {
                        $年份字段 = $字段;
                    } elseif (in_array($小写字段, ['area', 'region', 'vod_area'])) {
                        $地区字段 = $字段;
                    } elseif (in_array($小写字段, ['json', 'data', 'vod_data'])) {
                        $JSON字段 = $字段;
                    }
                }
                
                if ($名称字段) {
                    $选择字段 = [$名称字段];
                    if ($链接字段) $选择字段[] = $链接字段;
                    if ($磁力字段) $选择字段[] = $磁力字段;
                    if ($电驴字段) $选择字段[] = $电驴字段;
                    if ($图片字段) $选择字段[] = $图片字段;
                    if ($描述字段) $选择字段[] = $描述字段;
                    if ($年份字段) $选择字段[] = $年份字段;
                    if ($地区字段) $选择字段[] = $地区字段;
                    if ($JSON字段) $选择字段[] = $JSON字段;
                    
                    $查询SQL = "SELECT " . implode(', ', $选择字段) . " FROM $表名";
                    
                    $语句 = $数据库->query($查询SQL);
                    $结果集 = $语句->fetchAll(PDO::FETCH_ASSOC);
                    
                    foreach ($结果集 as $索引 => $行数据) {
                        $视频名称 = $行数据[$名称字段] ?? '未知视频';
                        
                        if ($JSON字段 && !empty($行数据[$JSON字段])) {
                            $json数据 = json_decode($行数据[$JSON字段], true);
                            if ($json数据 && is_array($json数据)) {
                                if (isset($json数据['name']) && empty($视频名称)) {
                                    $视频名称 = $json数据['name'];
                                }
                            }
                        }
                        
                        $视频链接 = '';
                        $播放来源 = '数据库源';
                        
                        if ($磁力字段 && !empty($行数据[$磁力字段])) {
                            $视频链接 = $行数据[$磁力字段];
                            $播放来源 = '🧲磁力链接';
                        } elseif ($电驴字段 && !empty($行数据[$电驴字段])) {
                            $视频链接 = $行数据[$电驴字段];
                            $播放来源 = '⚡电驴链接';
                        } elseif ($链接字段 && !empty($行数据[$链接字段])) {
                            $视频链接 = $行数据[$链接字段];
                            if (strpos($视频链接, 'magnet:') === 0) {
                                $播放来源 = '🧲磁力链接';
                            } elseif (strpos($视频链接, 'ed2k://') === 0) {
                                $播放来源 = '⚡电驴链接';
                            }
                        }
                        
                        if (empty($视频链接)) {
                            continue;
                        }
                        
                        $视频封面 = $行数据[$图片字段] ?? $默认图片[$索引 % count($默认图片)];
                        $视频描述 = $行数据[$描述字段] ?? '《' . $视频名称 . '》的精彩内容';
                        $视频年份 = $行数据[$年份字段] ?? date('Y');
                        $视频地区 = $行数据[$地区字段] ?? '中国大陆';
                        
                        $有效协议 = ['http://', 'https://', 'rtmp://', 'rtsp://', 'udp://', 'magnet:', 'ed2k://'];
                        $有有效协议 = false;
                        foreach ($有效协议 as $协议) {
                            if (stripos($视频链接, $协议) === 0) {
                                $有有效协议 = true;
                                break;
                            }
                        }
                        
                        if (!$有有效协议) {
                            continue;
                        }
                        
                        $视频列表[] = [
                            'vod_id' => 'db_' . md5($文件路径) . '_' . $表名 . '_' . $索引,
                            'vod_name' => $视频名称,
                            'vod_pic' => $视频封面,
                            'vod_remarks' => '高清',
                            'vod_year' => $视频年份,
                            'vod_area' => $视频地区,
                            'vod_content' => $视频描述,
                            'vod_play_from' => $播放来源,
                            'vod_play_url' => '正片$' . $视频链接
                        ];
                        
                        if (count($视频列表) >= 1000) {
                            break 2;
                        }
                    }
                }
            }
        }
        
        $数据库 = null;
        调试日志('数据库', "数据库解析完成: {$文件路径}, 找到视频: " . count($视频列表) . "个");
        结束计时('解析数据库文件');
        
        return $视频列表;
        
    } catch (PDOException $异常) {
        调试日志('数据库', "数据库读取失败: {$文件路径}, 错误: " . $异常->getMessage());
        结束计时('解析数据库文件');
        return ['错误' => '数据库读取失败: ' . $异常->getMessage()];
    }
}

/**
 * 解析JSON文件内容 - 完整加载
 */
function 解析JSON文件($文件路径) {
    开始计时('解析JSON文件');
    
    if (!file_exists($文件路径)) {
        调试日志('JSON解析', "JSON文件不存在: {$文件路径}");
        结束计时('解析JSON文件');
        return ['错误' => 'JSON文件不存在: ' . basename($文件路径)];
    }
    
    $JSON内容 = @file_get_contents($文件路径);
    if ($JSON内容 === false) {
        调试日志('JSON解析', "无法读取JSON文件: {$文件路径}");
        结束计时('解析JSON文件');
        return ['错误' => '无法读取JSON文件: ' . basename($文件路径)];
    }
    
    if (substr($JSON内容, 0, 3) == "\xEF\xBB\xBF") {
        $JSON内容 = substr($JSON内容, 3);
    }
    
    $数据 = json_decode($JSON内容, true);
    if (!$数据) {
        调试日志('JSON解析', "JSON格式无效: {$文件路径}");
        结束计时('解析JSON文件');
        return ['错误' => 'JSON格式无效: ' . basename($文件路径)];
    }
    
    if (!isset($数据['list']) || !is_array($数据['list'])) {
        调试日志('JSON解析', "JSON格式无效或缺少list字段: {$文件路径}");
        结束计时('解析JSON文件');
        return ['错误' => 'JSON格式无效或缺少list字段: ' . basename($文件路径)];
    }
    
    调试日志('JSON解析', "JSON解析完成: {$文件路径}, 找到视频: " . count($数据['list']) . "个");
    结束计时('解析JSON文件');
    
    return $数据['list'];
}

/**
 * 智能生成视频名称
 */
function 生成视频名称($链接, $默认名称 = '未知视频') {
    if (strpos($链接, 'magnet:?xt=urn:btih:') === 0) {
        if (preg_match('/&dn=([^&]+)/i', $链接, $匹配)) {
            $名称 = urldecode($匹配[1]);
            return $名称 ?: '磁力资源';
        }
        return '磁力资源';
    }
    
    if (strpos($链接, 'ed2k://') === 0) {
        if (preg_match('/\|file\|([^\|]+)\|/i', $链接, $匹配)) {
            $名称 = urldecode($匹配[1]);
            return $名称 ?: '电驴资源';
        }
        return '电驴资源';
    }
    
    return $默认名称;
}

/**
 * 解析TXT文件内容 - 增强磁力链接和纯链接支持
 */
function 解析TXT文件($文件路径) {
    开始计时('解析TXT文件');
    
    if (!file_exists($文件路径)) {
        调试日志('TXT解析', "TXT文件不存在: {$文件路径}");
        结束计时('解析TXT文件');
        return ['错误' => 'TXT文件不存在: ' . basename($文件路径)];
    }
    
    $句柄 = @fopen($文件路径, 'r');
    if (!$句柄) {
        调试日志('TXT解析', "无法打开TXT文件: {$文件路径}");
        结束计时('解析TXT文件');
        return ['错误' => '无法打开TXT文件: ' . basename($文件路径)];
    }
    
    $视频列表 = [];
    $视频数量 = 0;
    $行号 = 0;
    
    $默认图片 = [
        'https://www.252035.xyz/imgs?t=1335527662'
    ];
    
    $首行 = fgets($句柄);
    rewind($句柄);
    $有BOM = (substr($首行, 0, 3) == "\xEF\xBB\xBF");
    if ($有BOM) {
        fseek($句柄, 3);
    }
    
    $内存限制 = 50 * 1024 * 1024;
    $起始内存 = memory_get_usage();
    
    while (($行 = fgets($句柄)) !== false) {
        $行号++;
        $行 = trim($行);
        
        if ($行 === '' || $行[0] === '#' || $行[0] === ';') {
            continue;
        }
        
        if (strpos($行, 'magnet:') === 0 || strpos($行, 'ed2k://') === 0) {
            $链接 = $行;
            $名称 = 生成视频名称($链接);
        } else {
            $分隔符 = [',', "\t", '|', '$', '#'];
            $分隔符位置 = false;
            
            foreach ($分隔符 as $分隔) {
                $位置 = strpos($行, $分隔);
                if ($位置 !== false) {
                    $分隔符位置 = $位置;
                    break;
                }
            }
            
            if ($分隔符位置 === false) {
                $链接 = $行;
                $名称 = 生成视频名称($链接);
            } else {
                $名称 = trim(substr($行, 0, $分隔符位置));
                $链接 = trim(substr($行, $分隔符位置 + 1));
            }
        }
        
        if (empty($名称) || empty($链接)) {
            continue;
        }
        
        $有效协议 = ['http://', 'https://', 'rtmp://', 'rtsp://', 'udp://', 'magnet:', 'ed2k://'];
        $有有效协议 = false;
        foreach ($有效协议 as $协议) {
            if (stripos($链接, $协议) === 0) {
                $有有效协议 = true;
                break;
            }
        }
        
        if (!$有有效协议) {
            continue;
        }
        
        $图片索引 = $视频数量 % count($默认图片);
        
        $播放来源 = '在线播放';
        if (strpos($链接, 'magnet:') === 0) {
            $播放来源 = '🧲磁力链接';
        } elseif (strpos($链接, 'ed2k://') === 0) {
            $播放来源 = '⚡电驴链接';
        }
        
        $视频列表[] = [
            'vod_id' => 'txt_' . md5($文件路径) . '_' . $行号,
            'vod_name' => $名称,
            'vod_pic' => $默认图片[$图片索引],
            'vod_remarks' => '高清',
            'vod_year' => date('Y'),
            'vod_area' => '中国大陆',
            'vod_content' => '《' . $名称 . '》的精彩内容',
            'vod_play_from' => $播放来源,
            'vod_play_url' => '正片$' . $链接
        ];
        
        $视频数量++;
        
        if ($视频数量 % 100 === 0) {
            $当前内存 = memory_get_usage() - $起始内存;
            if ($当前内存 > $内存限制) {
                调试日志('TXT解析', "内存限制达到，停止解析: {$文件路径}");
                break;
            }
            gc_collect_cycles();
        }
        
        if ($视频数量 >= 10000) {
            调试日志('TXT解析', "达到最大视频数量限制: {$文件路径}");
            break;
        }
    }
    
    fclose($句柄);
    
    调试日志('TXT解析', "TXT解析完成: {$文件路径}, 找到视频: " . count($视频列表) . "个");
    结束计时('解析TXT文件');
    
    return $视频列表;
}

/**
 * 解析M3U文件内容 - 增强磁力链接支持
 */
function 解析M3U文件($文件路径) {
    开始计时('解析M3U文件');
    
    if (!file_exists($文件路径)) {
        调试日志('M3U解析', "M3U文件不存在: {$文件路径}");
        结束计时('解析M3U文件');
        return ['错误' => 'M3U文件不存在: ' . basename($文件路径)];
    }
    
    $句柄 = @fopen($文件路径, 'r');
    if (!$句柄) {
        调试日志('M3U解析', "无法打开M3U文件: {$文件路径}");
        结束计时('解析M3U文件');
        return ['错误' => '无法打开M3U文件: ' . basename($文件路径)];
    }
    
    $视频列表 = [];
    $视频数量 = 0;
    $当前名称 = '';
    $当前图标 = '';
    $当前分组 = '';
    $行号 = 0;
    
    $默认图片 = [
        'https://www.252035.xyz/imgs?t=1335527662'
    ];
    
    $首行 = fgets($句柄);
    rewind($句柄);
    $有BOM = (substr($首行, 0, 3) == "\xEF\xBB\xBF");
    if ($有BOM) {
        fseek($句柄, 3);
    }
    
    while (($行 = fgets($句柄)) !== false) {
        $行号++;
        $行 = trim($行);
        if ($行 === '') continue;
        
        if (strpos($行, '#EXTM3U') === 0) {
            continue;
        }
        
        if (strpos($行, '#EXTINF:') === 0) {
            $当前名称 = '';
            $当前图标 = '';
            $当前分组 = '';
            
            $部分 = explode(',', $行, 2);
            if (count($部分) > 1) {
                $当前名称 = trim($部分[1]);
            }
            
            if (preg_match('/tvg-logo="([^"]*)"/i', $行, $图标匹配)) {
                $当前图标 = trim($图标匹配[1]);
            }
            
            if (preg_match('/group-title="([^"]*)"/i', $行, $分组匹配)) {
                $当前分组 = trim($分组匹配[1]);
            }
            continue;
        }
        
        $有效协议 = ['http://', 'https://', 'rtmp://', 'rtsp://', 'udp://', 'magnet:', 'ed2k://'];
        $有有效协议 = false;
        foreach ($有效协议 as $协议) {
            if (stripos($行, $协议) === 0) {
                $有有效协议 = true;
                break;
            }
        }
        
        if ($有有效协议 && !empty($当前名称)) {
            $图片索引 = $视频数量 % count($默认图片);
            
            $视频封面 = $当前图标;
            if (empty($视频封面) || !filter_var($视频封面, FILTER_VALIDATE_URL)) {
                $视频封面 = $默认图片[$图片索引];
            }
            
            $播放来源 = '直播源';
            if (!empty($当前分组)) {
                $播放来源 = $当前分组;
            }
            
            if (strpos($行, 'magnet:') === 0) {
                $播放来源 = '🧲磁力链接';
            } elseif (strpos($行, 'ed2k://') === 0) {
                $播放来源 = '⚡电驴链接';
            }
            
            $视频列表[] = [
                'vod_id' => 'm3u_' . md5($文件路径) . '_' . $行号,
                'vod_name' => $当前名称,
                'vod_pic' => $视频封面,
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $当前名称 . '直播频道',
                'vod_play_from' => $播放来源,
                'vod_play_url' => '直播$' . $行
            ];
            
            $视频数量++;
            
            $当前名称 = '';
            $当前图标 = '';
            $当前分组 = '';
            
            if ($视频数量 >= 5000) {
                调试日志('M3U解析', "达到最大视频数量限制: {$文件路径}");
                break;
            }
        }
    }
    
    fclose($句柄);
    
    调试日志('M3U解析', "M3U解析完成: {$文件路径}, 找到视频: " . count($视频列表) . "个");
    结束计时('解析M3U文件');
    
    return $视频列表;
}

/**
 * 获取热门推荐视频 - 从所有分类中随机获取
 */
function 获取热门视频($页码, $每页数量 = 10) {
    开始计时('获取热门视频');
    
    static $所有热门视频 = null;
    static $已使用视频标识 = [];
    
    if ($页码 == 1) {
        $已使用视频标识 = [];
    }
    
    if ($所有热门视频 === null) {
        $所有热门视频 = [];
        $所有文件 = 获取所有文件();
        
        foreach ($所有文件 as $文件) {
            if (!file_exists($文件['path'])) {
                continue;
            }
            
            $视频列表 = [];
            switch ($文件['type']) {
                case 'json':
                    $视频列表 = 解析JSON文件($文件['path']);
                    break;
                case 'txt':
                    $视频列表 = 解析TXT文件($文件['path']);
                    break;
                case 'm3u':
                    $视频列表 = 解析M3U文件($文件['path']);
                    break;
                case 'db':
                    $视频列表 = 解析数据库文件($文件['path']);
                    break;
            }
            
            if (isset($视频列表['错误'])) {
                continue;
            }
            
            if (count($视频列表) > 100) {
                $视频列表 = array_slice($视频列表, 0, 100);
            }
            
            $所有热门视频 = array_merge($所有热门视频, $视频列表);
            
            if (count($所有热门视频) > 1000) {
                break;
            }
        }
        
        调试日志('热门推荐', "热门视频库构建完成，总计: " . count($所有热门视频) . "个视频");
    }
    
    if (empty($所有热门视频)) {
        结束计时('获取热门视频');
        return [];
    }
    
    $可用视频 = [];
    foreach ($所有热门视频 as $视频) {
        $视频标识 = $视频['vod_id'] ?? '';
        if (!in_array($视频标识, $已使用视频标识)) {
            $可用视频[] = $视频;
        }
    }
    
    if (empty($可用视频)) {
        $已使用视频标识 = [];
        $可用视频 = $所有热门视频;
    }
    
    $选中视频 = [];
    $需要数量 = min($每页数量, count($可用视频));
    
    if ($需要数量 > 0) {
        $随机键 = array_rand($可用视频, $需要数量);
        if (!is_array($随机键)) {
            $随机键 = [$随机键];
        }
        
        foreach ($随机键 as $键) {
            $选中视频项 = $可用视频[$键];
            $选中视频[] = $选中视频项;
            $已使用视频标识[] = $选中视频项['vod_id'] ?? '';
        }
    }
    
    调试日志('热门推荐', "获取热门视频第{$页码}页，返回: " . count($选中视频) . "个视频");
    结束计时('获取热门视频');
    
    return $选中视频;
}

/**
 * 首页数据
 */
function 获取首页() {
    开始计时('获取首页');
    
    $分类列表 = 获取分类列表();
    
    if (empty($分类列表)) {
        调试日志('系统', "未找到任何分类");
        结束计时('获取首页');
        return ['错误' => '未找到任何文件'];
    }
    
    调试日志('系统', "首页数据生成完成，分类数: " . count($分类列表));
    结束计时('获取首页');
    
    return [
        'class' => $分类列表
    ];
}

/**
 * 分类列表
 */
function 获取分类($分类标识, $页码) {
    开始计时('获取分类');
    
    $分类列表 = 获取分类列表();
    
    if (empty($分类列表)) {
        调试日志('系统', "未找到任何分类");
        结束计时('获取分类');
        return ['错误' => '未找到任何分类'];
    }
    
    // 处理热门推荐
    if ($分类标识 === 'hot') {
        $当前页码 = intval($页码);
        if ($当前页码 < 1) $当前页码 = 1;
        
        $热门视频 = 获取热门视频($当前页码, 10);
        
        if (empty($热门视频)) {
            调试日志('热门推荐', "热门推荐第{$当前页码}页无数据");
            结束计时('获取分类');
            return [
                'page' => $当前页码,
                'pagecount' => 9999,
                'limit' => 10,
                'total' => 0,
                'list' => []
            ];
        }
        
        $格式化视频 = [];
        foreach ($热门视频 as $视频) {
            $格式化视频[] = 格式化视频项($视频);
        }
        
        调试日志('热门推荐', "热门推荐第{$当前页码}页返回: " . count($格式化视频) . "个视频");
        结束计时('获取分类');
        
        return [
            'page' => $当前页码,
            'pagecount' => 9999,
            'limit' => 10,
            'total' => 999999,
            'list' => $格式化视频
        ];
    }
    
    // 处理音频媒体库
    if ($分类标识 === 'audio_library') {
        $音频分类 = 获取媒体文件分类('audio');
        
        if (empty($音频分类)) {
            调试日志('音频媒体库', "音频媒体库无数据");
            结束计时('获取分类');
            return [
                'page' => 1,
                'pagecount' => 1,
                'limit' => 10,
                'total' => 0,
                'list' => []
            ];
        }
        
        $格式化分类 = [];
        foreach ($音频分类 as $分类) {
            $格式化分类[] = [
                'vod_id' => $分类['type_id'],
                'vod_name' => $分类['type_name'],
                'vod_pic' => 'https://www.252035.xyz/imgs?t=audio_library',
                'vod_remarks' => '音频分类',
                'vod_year' => date('Y'),
                'vod_area' => '本地文件'
            ];
        }
        
        调试日志('音频媒体库', "音频媒体库返回: " . count($格式化分类) . "个分类");
        结束计时('获取分类');
        
        return [
            'page' => 1,
            'pagecount' => 1,
            'limit' => count($格式化分类),
            'total' => count($格式化分类),
            'list' => $格式化分类
        ];
    }
    
    // 处理视频媒体中心
    if ($分类标识 === 'video_center') {
        $视频分类 = 获取媒体文件分类('video');
        
        if (empty($视频分类)) {
            调试日志('视频媒体中心', "视频媒体中心无数据");
            结束计时('获取分类');
            return [
                'page' => 1,
                'pagecount' => 1,
                'limit' => 10,
                'total' => 0,
                'list' => []
            ];
        }
        
        $格式化分类 = [];
        foreach ($视频分类 as $分类) {
            $格式化分类[] = [
                'vod_id' => $分类['type_id'],
                'vod_name' => $分类['type_name'],
                'vod_pic' => 'https://www.252035.xyz/imgs?t=video_center',
                'vod_remarks' => '视频分类',
                'vod_year' => date('Y'),
                'vod_area' => '本地文件'
            ];
        }
        
        调试日志('视频媒体中心', "视频媒体中心返回: " . count($格式化分类) . "个分类");
        结束计时('获取分类');
        
        return [
            'page' => 1,
            'pagecount' => 1,
            'limit' => count($格式化分类),
            'total' => count($格式化分类),
            'list' => $格式化分类
        ];
    }
    
    // 处理媒体文件夹
    if (strpos($分类标识, 'media_') === 0) {
        $部分 = explode('_', $分类标识);
        if (count($部分) >= 3) {
            $媒体类型 = $部分[1];
            $文件夹索引 = $部分[2];
            
            $媒体分类 = 获取媒体文件分类($媒体类型);
            $目标分类 = null;
            
            foreach ($媒体分类 as $分类) {
                if ($分类['type_id'] === $分类标识) {
                    $目标分类 = $分类;
                    break;
                }
            }
            
            if ($目标分类) {
                $媒体视频 = 解析媒体文件夹($目标分类['source_path'], $媒体类型);
                
                if (empty($媒体视频)) {
                    调试日志('媒体文件夹', "媒体文件夹无内容: {$目标分类['source_path']}");
                    结束计时('获取分类');
                    return [
                        'page' => 1,
                        'pagecount' => 1,
                        'limit' => 10,
                        'total' => 0,
                        'list' => []
                    ];
                }
                
                $每页大小 = 10;
                $总数 = count($媒体视频);
                $总页数 = ceil($总数 / $每页大小);
                $当前页码 = intval($页码);
                
                if ($当前页码 < 1) $当前页码 = 1;
                if ($当前页码 > $总页数) $当前页码 = $总页数;
                
                $起始位置 = ($当前页码 - 1) * $每页大小;
                $分页视频 = array_slice($媒体视频, $起始位置, $每页大小);
                
                $格式化视频 = [];
                foreach ($分页视频 as $视频) {
                    $格式化视频[] = 格式化视频项($视频);
                }
                
                调试日志('媒体文件夹', "媒体文件夹 {$目标分类['source_path']} 第{$当前页码}页返回: " . count($格式化视频) . "个媒体文件");
                结束计时('获取分类');
                
                return [
                    'page' => $当前页码,
                    'pagecount' => $总页数,
                    'limit' => $每页大小,
                    'total' => $总数,
                    'list' => $格式化视频
                ];
            }
        }
    }
    
    $目标分类 = null;
    foreach ($分类列表 as $分类) {
        if ($分类['type_id'] === $分类标识) {
            $目标分类 = $分类;
            break;
        }
    }
    
    if (!$目标分类) {
        调试日志('系统', "分类未找到: {$分类标识}");
        结束计时('获取分类');
        return ['错误' => '分类未找到: ' . $分类标识];
    }
    
    if ($目标分类['source_type'] === 'empty') {
        结束计时('获取分类');
        return [
            'page' => 1,
            'pagecount' => 1,
            'limit' => 10,
            'total' => 0,
            'list' => []
        ];
    }
    
    $分类视频 = [];
    
    if (file_exists($目标分类['source_path'])) {
        switch ($目标分类['source_type']) {
            case 'json':
                $分类视频 = 解析JSON文件($目标分类['source_path']);
                break;
            case 'txt':
                $分类视频 = 解析TXT文件($目标分类['source_path']);
                break;
            case 'm3u':
                $分类视频 = 解析M3U文件($目标分类['source_path']);
                break;
            case 'db':
                $分类视频 = 解析数据库文件($目标分类['source_path']);
                break;
        }
    }
    
    if (isset($分类视频['错误'])) {
        调试日志('系统', "分类解析错误: {$分类视频['错误']}");
        结束计时('获取分类');
        return ['错误' => $分类视频['错误']];
    }
    
    if (empty($分类视频)) {
        调试日志('系统', "分类无内容: {$目标分类['type_name']}");
        结束计时('获取分类');
        return ['错误' => '在文件中未找到视频: ' . $目标分类['type_name']];
    }
    
    $每页大小 = 10;
    $总数 = count($分类视频);
    $总页数 = ceil($总数 / $每页大小);
    $当前页码 = intval($页码);
    
    if ($当前页码 < 1) $当前页码 = 1;
    if ($当前页码 > $总页数) $当前页码 = $总页数;
    
    $起始位置 = ($当前页码 - 1) * $每页大小;
    $分页视频 = array_slice($分类视频, $起始位置, $每页大小);
    
    $格式化视频 = [];
    foreach ($分页视频 as $视频) {
        $格式化视频[] = 格式化视频项($视频);
    }
    
    调试日志('系统', "分类 {$目标分类['type_name']} 第{$当前页码}页返回: " . count($格式化视频) . "个视频");
    结束计时('获取分类');
    
    return [
        'page' => $当前页码,
        'pagecount' => $总页数,
        'limit' => $每页大小,
        'total' => $总数,
        'list' => $格式化视频
    ];
}

/**
 * 格式化视频项
 */
function 格式化视频项($视频) {
    return [
        'vod_id' => $视频['vod_id'] ?? '',
        'vod_name' => $视频['vod_name'] ?? '未知视频',
        'vod_pic' => $视频['vod_pic'] ?? 'https://www.252035.xyz/imgs?t=1335527662',
        'vod_remarks' => $视频['vod_remarks'] ?? '高清',
        'vod_year' => $视频['vod_year'] ?? '',
        'vod_area' => $视频['vod_area'] ?? '中国大陆'
    ];
}

/**
 * 视频详情
 */
function 获取详情($视频标识) {
    开始计时('获取详情');
    
    $标识数组 = explode(',', $视频标识);
    $结果 = [];
    
    foreach ($标识数组 as $标识) {
        $视频 = 按标识查找视频($标识);
        if ($视频) {
            $结果[] = 格式化视频详情($视频);
        } else {
            $结果[] = [
                'vod_id' => $标识,
                'vod_name' => '视频 ' . $标识,
                'vod_pic' => 'https://www.252035.xyz/imgs?t=1335527662',
                'vod_remarks' => '高清',
                'vod_content' => '视频详情内容',
                'vod_play_from' => '在线播放',
                'vod_play_url' => '正片$https://example.com/video'
            ];
        }
    }
    
    调试日志('系统', "获取详情完成: {$视频标识}, 找到: " . count($结果) . "个视频");
    结束计时('获取详情');
    
    return ['list' => $结果];
}

/**
 * 按标识查找视频
 */
function 按标识查找视频($标识) {
    开始计时('按标识查找视频');
    
    $所有文件 = 获取所有文件();
    
    if (strpos($标识, 'txt_') === 0) {
        $部分 = explode('_', $标识);
        if (count($部分) >= 3) {
            $文件哈希 = $部分[1];
            $行号 = $部分[2];
            
            foreach ($所有文件 as $文件) {
                if ($文件['type'] === 'txt' && md5($文件['path']) === $文件哈希) {
                    $视频 = 按行查找TXT视频($文件['path'], $行号);
                    结束计时('按标识查找视频');
                    return $视频;
                }
            }
        }
    } elseif (strpos($标识, 'm3u_') === 0) {
        $部分 = explode('_', $标识);
        if (count($部分) >= 3) {
            $文件哈希 = $部分[1];
            $行号 = $部分[2];
            
            foreach ($所有文件 as $文件) {
                if ($文件['type'] === 'm3u' && md5($文件['path']) === $文件哈希) {
                    $视频 = 按行查找M3U视频($文件['path'], $行号);
                    结束计时('按标识查找视频');
                    return $视频;
                }
            }
        }
    } elseif (strpos($标识, 'db_') === 0) {
        $部分 = explode('_', $标识);
        if (count($部分) >= 4) {
            $文件哈希 = $部分[1];
            $表名 = $部分[2];
            $视频索引 = $部分[3];
            
            foreach ($所有文件 as $文件) {
                if ($文件['type'] === 'db' && md5($文件['path']) === $文件哈希) {
                    $视频 = 按索引查找数据库视频($文件['path'], $表名, $视频索引);
                    结束计时('按标识查找视频');
                    return $视频;
                }
            }
        }
    } elseif (strpos($标识, 'media_') === 0) {
        // 媒体文件直接返回基本信息
        $媒体文件 = 扫描媒体文件('all');
        foreach ($媒体文件 as $文件) {
            if ('media_' . md5($文件['path']) === $标识) {
                $媒体类型 = in_array($文件['type'], ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma']) ? 'audio' : 'video';
                $播放来源 = $媒体类型 === 'audio' ? '🎵 音频文件' : '🎬 视频文件';
                
                $视频 = [
                    'vod_id' => $标识,
                    'vod_name' => $文件['filename'],
                    'vod_pic' => $媒体类型 === 'audio' ? 
                        'https://www.252035.xyz/imgs?t=audio_icon' : 
                        'https://www.252035.xyz/imgs?t=video_icon',
                    'vod_remarks' => $媒体类型 === 'audio' ? '音频' : '视频',
                    'vod_year' => date('Y'),
                    'vod_area' => '本地文件',
                    'vod_content' => $文件['name'] . ' - ' . $文件['relative_path'],
                    'vod_play_from' => $播放来源,
                    'vod_play_url' => '播放$' . $文件['path']
                ];
                结束计时('按标识查找视频');
                return $视频;
            }
        }
    } else {
        foreach ($所有文件 as $文件) {
            if ($文件['type'] === 'json') {
                $视频列表 = 解析JSON文件($文件['path']);
                foreach ($视频列表 as $视频) {
                    if (isset($视频['vod_id']) && $视频['vod_id'] == $标识) {
                        结束计时('按标识查找视频');
                        return $视频;
                    }
                }
            }
        }
    }
    
    调试日志('系统', "未找到视频: {$标识}");
    结束计时('按标识查找视频');
    return null;
}

/**
 * 在TXT文件中按行号查找视频 - 增强磁力链接支持
 */
function 按行查找TXT视频($文件路径, $目标行号) {
    if (!file_exists($文件路径)) {
        return null;
    }
    
    $句柄 = @fopen($文件路径, 'r');
    if (!$句柄) {
        return null;
    }
    
    $当前行 = 0;
    $视频 = null;
    
    $默认图片 = [
        'https://www.252035.xyz/imgs?t=1335527662'
    ];
    
    $首行 = fgets($句柄);
    rewind($句柄);
    $有BOM = (substr($首行, 0, 3) == "\xEF\xBB\xBF");
    if ($有BOM) {
        fseek($句柄, 3);
    }
    
    while (($行 = fgets($句柄)) !== false) {
        $当前行++;
        $行 = trim($行);
        
        if ($行 === '' || $行[0] === '#' || $行[0] === ';') continue;
        
        if ($当前行 == $目标行号) {
            if (strpos($行, 'magnet:') === 0 || strpos($行, 'ed2k://') === 0) {
                $链接 = $行;
                $名称 = 生成视频名称($链接);
            } else {
                $分隔符 = [',', "\t", '|', '$', '#'];
                $分隔符位置 = false;
                
                foreach ($分隔符 as $分隔) {
                    $位置 = strpos($行, $分隔);
                    if ($位置 !== false) {
                        $分隔符位置 = $位置;
                        break;
                    }
                }
                
                if ($分隔符位置 !== false) {
                    $名称 = trim(substr($行, 0, $分隔符位置));
                    $链接 = trim(substr($行, $分隔符位置 + 1));
                } else {
                    $链接 = $行;
                    $名称 = 生成视频名称($链接);
                }
            }
            
            if (!empty($名称) && !empty($链接)) {
                $图片索引 = $当前行 % count($默认图片);
                
                $播放来源 = '在线播放';
                if (strpos($链接, 'magnet:') === 0) {
                    $播放来源 = '🧲磁力链接';
                } elseif (strpos($链接, 'ed2k://') === 0) {
                    $播放来源 = '⚡电驴链接';
                }
                
                $视频 = [
                    'vod_id' => 'txt_' . md5($文件路径) . '_' . $当前行,
                    'vod_name' => $名称,
                    'vod_pic' => $默认图片[$图片索引],
                    'vod_remarks' => '高清',
                    'vod_year' => date('Y'),
                    'vod_area' => '中国大陆',
                    'vod_content' => '《' . $名称 . '》的精彩内容',
                    'vod_play_from' => $播放来源,
                    'vod_play_url' => '正片$' . $链接
                ];
            }
            break;
        }
    }
    
    fclose($句柄);
    
    return $视频;
}

/**
 * 在M3U文件中按行号查找视频
 */
function 按行查找M3U视频($文件路径, $目标行号) {
    if (!file_exists($文件路径)) {
        return null;
    }
    
    $句柄 = @fopen($文件路径, 'r');
    if (!$句柄) {
        return null;
    }
    
    $当前行 = 0;
    $视频 = null;
    $当前名称 = '';
    $当前图标 = '';
    $当前分组 = '';
    
    $默认图片 = [
        'https://www.252035.xyz/imgs?t=1335527662'
    ];
    
    $首行 = fgets($句柄);
    rewind($句柄);
    $有BOM = (substr($首行, 0, 3) == "\xEF\xBB\xBF");
    if ($有BOM) {
        fseek($句柄, 3);
    }
    
    while (($行 = fgets($句柄)) !== false) {
        $当前行++;
        $行 = trim($行);
        if ($行 === '') continue;
        
        if (strpos($行, '#EXTM3U') === 0) {
            continue;
        }
        
        if (strpos($行, '#EXTINF:') === 0) {
            $当前名称 = '';
            $当前图标 = '';
            $当前分组 = '';
            
            $部分 = explode(',', $行, 2);
            if (count($部分) > 1) {
                $当前名称 = trim($部分[1]);
            }
            
            if (preg_match('/tvg-logo="([^"]*)"/i', $行, $图标匹配)) {
                $当前图标 = trim($图标匹配[1]);
            }
            
            if (preg_match('/group-title="([^"]*)"/i', $行, $分组匹配)) {
                $当前分组 = trim($分组匹配[1]);
            }
            continue;
        }
        
        if ((strpos($行, 'http') === 0 || strpos($行, 'rtmp') === 0 || 
             strpos($行, 'rtsp') === 0 || strpos($行, 'udp') === 0 ||
             strpos($行, 'magnet:') === 0 || strpos($行, 'ed2k://') === 0) && 
            !empty($当前名称)) {
            
            if ($当前行 == $目标行号) {
                $图片索引 = $当前行 % count($默认图片);
                
                $视频封面 = $当前图标;
                if (empty($视频封面) || !filter_var($视频封面, FILTER_VALIDATE_URL)) {
                    $视频封面 = $默认图片[$图片索引];
                }
                
                $播放来源 = '直播源';
                if (!empty($当前分组)) {
                    $播放来源 = $当前分组;
                }
                
                if (strpos($行, 'magnet:') === 0) {
                    $播放来源 = '🧲磁力链接';
                } elseif (strpos($行, 'ed2k://') === 0) {
                    $播放来源 = '⚡电驴链接';
                }
                
                $视频 = [
                    'vod_id' => 'm3u_' . md5($文件路径) . '_' . $当前行,
                    'vod_name' => $当前名称,
                    'vod_pic' => $视频封面,
                    'vod_remarks' => '直播',
                    'vod_year' => date('Y'),
                    'vod_area' => '中国大陆',
                    'vod_content' => $当前名称 . '直播频道',
                    'vod_play_from' => $播放来源,
                    'vod_play_url' => '直播$' . $行
                ];
                break;
            }
            
            $当前名称 = '';
            $当前图标 = '';
            $当前分组 = '';
        }
    }
    
    fclose($句柄);
    
    return $视频;
}

/**
 * 在数据库文件中按索引查找视频 - 增强磁力链接支持
 */
function 按索引查找数据库视频($文件路径, $表名, $视频索引) {
    if (!file_exists($文件路径) || !extension_loaded('pdo_sqlite')) {
        return null;
    }
    
    try {
        $数据库 = new PDO("sqlite:" . $文件路径);
        $数据库->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        
        $字段列表 = $数据库->query("PRAGMA table_info($表名)")->fetchAll(PDO::FETCH_ASSOC);
        $字段名称 = array_column($字段列表, 'name');
        
        $名称字段 = null;
        $链接字段 = null;
        $磁力字段 = null;
        $电驴字段 = null;
        $图片字段 = null;
        $描述字段 = null;
        $年份字段 = null;
        $地区字段 = null;
        $JSON字段 = null;
        
        foreach ($字段名称 as $字段) {
            $小写字段 = strtolower($字段);
            if (in_array($小写字段, ['name', 'title', 'vod_name', 'filename', 'video_name'])) {
                $名称字段 = $字段;
            } elseif (in_array($小写字段, ['url', 'link', 'vod_url', 'play_url', 'video_url', 'torrent'])) {
                $链接字段 = $字段;
            } elseif (in_array($小写字段, ['magnet', 'magnet_url', 'magnet_link'])) {
                $磁力字段 = $字段;
            } elseif (in_array($小写字段, ['ed2k', 'ed2k_url', 'ed2k_link'])) {
                $电驴字段 = $字段;
            } elseif (in_array($小写字段, ['pic', 'image', 'cover', 'vod_pic', 'poster'])) {
                $图片字段 = $字段;
            } elseif (in_array($小写字段, ['desc', 'description', 'content', 'vod_content'])) {
                $描述字段 = $字段;
            } elseif (in_array($小写字段, ['year', 'vod_year'])) {
                $年份字段 = $字段;
            } elseif (in_array($小写字段, ['area', 'region', 'vod_area'])) {
                $地区字段 = $字段;
            } elseif (in_array($小写字段, ['json', 'data', 'vod_data'])) {
                $JSON字段 = $字段;
            }
        }
        
        if ($名称字段) {
            $选择字段 = [$名称字段];
            if ($链接字段) $选择字段[] = $链接字段;
            if ($磁力字段) $选择字段[] = $磁力字段;
            if ($电驴字段) $选择字段[] = $电驴字段;
            if ($图片字段) $选择字段[] = $图片字段;
            if ($描述字段) $选择字段[] = $描述字段;
            if ($年份字段) $选择字段[] = $年份字段;
            if ($地区字段) $选择字段[] = $地区字段;
            if ($JSON字段) $选择字段[] = $JSON字段;
            
            $查询SQL = "SELECT " . implode(', ', $选择字段) . " FROM $表名 LIMIT 1 OFFSET " . intval($视频索引);
            
            $语句 = $数据库->query($查询SQL);
            $行数据 = $语句->fetch(PDO::FETCH_ASSOC);
            
            if ($行数据) {
                $默认图片 = [
                    'https://www.252035.xyz/imgs?t=1335527662'
                ];
                
                $视频名称 = $行数据[$名称字段] ?? '未知视频';
                
                if ($JSON字段 && !empty($行数据[$JSON字段])) {
                    $json数据 = json_decode($行数据[$JSON字段], true);
                    if ($json数据 && isset($json数据['name']) && empty($视频名称)) {
                        $视频名称 = $json数据['name'];
                    }
                }
                
                $视频链接 = '';
                $播放来源 = '数据库源';
                
                if ($磁力字段 && !empty($行数据[$磁力字段])) {
                    $视频链接 = $行数据[$磁力字段];
                    $播放来源 = '🧲磁力链接';
                } elseif ($电驴字段 && !empty($行数据[$电驴字段])) {
                    $视频链接 = $行数据[$电驴字段];
                    $播放来源 = '⚡电驴链接';
                } elseif ($链接字段 && !empty($行数据[$链接字段])) {
                    $视频链接 = $行数据[$链接字段];
                    if (strpos($视频链接, 'magnet:') === 0) {
                        $播放来源 = '🧲磁力链接';
                    } elseif (strpos($视频链接, 'ed2k://') === 0) {
                        $播放来源 = '⚡电驴链接';
                    }
                }
                
                if (empty($视频链接)) {
                    $数据库 = null;
                    return null;
                }
                
                $视频封面 = $行数据[$图片字段] ?? $默认图片[intval($视频索引) % count($默认图片)];
                $视频描述 = $行数据[$描述字段] ?? '《' . $视频名称 . '》的精彩内容';
                $视频年份 = $行数据[$年份字段] ?? date('Y');
                $视频地区 = $行数据[$地区字段] ?? '中国大陆';
                
                $视频 = [
                    'vod_id' => 'db_' . md5($文件路径) . '_' . $表名 . '_' . $视频索引,
                    'vod_name' => $视频名称,
                    'vod_pic' => $视频封面,
                    'vod_remarks' => '高清',
                    'vod_year' => $视频年份,
                    'vod_area' => $视频地区,
                    'vod_content' => $视频描述,
                    'vod_play_from' => $播放来源,
                    'vod_play_url' => '正片$' . $视频链接
                ];
                
                $数据库 = null;
                return $视频;
            }
        }
        
        $数据库 = null;
        return null;
        
    } catch (PDOException $异常) {
        return null;
    }
}

/**
 * 搜索
 */
function 搜索($关键词, $页码) {
    开始计时('搜索');
    
    if (empty($关键词)) {
        调试日志('搜索', "搜索关键词为空");
        结束计时('搜索');
        return ['错误' => '请输入搜索关键词'];
    }
    
    $搜索结果 = [];
    $所有文件 = 获取所有文件();
    
    $搜索限制 = 3;
    $已搜索文件 = 0;
    
    foreach ($所有文件 as $文件) {
        if ($已搜索文件 >= $搜索限制) {
            break;
        }
        
        $视频列表 = [];
        switch ($文件['type']) {
            case 'json':
                $视频列表 = 解析JSON文件($文件['path']);
                break;
            case 'txt':
                $视频列表 = 解析TXT文件($文件['path']);
                break;
            case 'm3u':
                $视频列表 = 解析M3U文件($文件['path']);
                break;
            case 'db':
                $视频列表 = 解析数据库文件($文件['path']);
                break;
        }
        
        if (isset($视频列表['错误'])) {
            continue;
        }
        
        $文件匹配数 = 0;
        foreach ($视频列表 as $视频) {
            if (stripos($视频['vod_name'] ?? '', $关键词) !== false) {
                $搜索结果[] = 格式化视频项($视频);
                $文件匹配数++;
                
                if (count($搜索结果) >= 30) {
                    break 2;
                }
            }
        }
        
        $已搜索文件++;
    }
    
    // 搜索媒体文件
    $媒体文件 = 扫描媒体文件('all');
    foreach ($媒体文件 as $文件) {
        if (stripos($文件['filename'], $关键词) !== false) {
            $媒体类型 = in_array($文件['type'], ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma']) ? 'audio' : 'video';
            $播放来源 = $媒体类型 === 'audio' ? '🎵 音频文件' : '🎬 视频文件';
            
            $搜索结果[] = [
                'vod_id' => 'media_' . md5($文件['path']),
                'vod_name' => $文件['filename'],
                'vod_pic' => $媒体类型 === 'audio' ? 
                    'https://www.252035.xyz/imgs?t=audio_icon' : 
                    'https://www.252035.xyz/imgs?t=video_icon',
                'vod_remarks' => $媒体类型 === 'audio' ? '音频' : '视频',
                'vod_year' => date('Y'),
                'vod_area' => '本地文件'
            ];
            
            if (count($搜索结果) >= 50) {
                break;
            }
        }
    }
    
    if (empty($搜索结果)) {
        调试日志('搜索', "未找到相关视频内容: {$关键词}");
        结束计时('搜索');
        return ['错误' => '未找到相关视频内容'];
    }
    
    $每页大小 = 10;
    $总数 = count($搜索结果);
    $总页数 = ceil($总数 / $每页大小);
    $当前页码 = intval($页码);
    
    if ($当前页码 < 1) $当前页码 = 1;
    if ($当前页码 > $总页数) $当前页码 = $总页数;
    
    $起始位置 = ($当前页码 - 1) * $每页大小;
    $分页结果 = array_slice($搜索结果, $起始位置, $每页大小);
    
    调试日志('搜索', "搜索完成: {$关键词}, 第{$当前页码}页, 结果: " . count($分页结果) . "个");
    结束计时('搜索');
    
    return [
        'page' => $当前页码,
        'pagecount' => $总页数,
        'limit' => $每页大小,
        'total' => $总数,
        'list' => $分页结果
    ];
}

/**
 * 格式化视频详情
 */
function 格式化视频详情($视频) {
    return [
        'vod_id' => $视频['vod_id'] ?? '',
        'vod_name' => $视频['vod_name'] ?? '未知视频',
        'vod_pic' => $视频['vod_pic'] ?? 'https://www.252035.xyz/imgs?t=1335527662',
        'vod_remarks' => $视频['vod_remarks'] ?? '高清',
        'vod_year' => $视频['vod_year'] ?? '',
        'vod_area' => $视频['vod_area'] ?? '中国大陆',
        'vod_director' => $视频['vod_director'] ?? '',
        'vod_actor' => $视频['vod_actor'] ?? '',
        'vod_content' => $视频['vod_content'] ?? '视频详情内容',
        'vod_play_from' => $视频['vod_play_from'] ?? 'default',
        'vod_play_url' => $视频['vod_play_url'] ?? ''
    ];
}

/**
 * 获取播放地址 - 增强磁力链接和媒体文件支持
 */
function 获取播放($标志, $标识) {
    开始计时('获取播放');
    
    // 检查是否为媒体文件
    if (strpos($标识, 'media_') === 0) {
        $媒体文件 = 扫描媒体文件('all');
        foreach ($媒体文件 as $文件) {
            if ('media_' . md5($文件['path']) === $标识) {
                调试日志('播放', "播放媒体文件: {$文件['path']}");
                结束计时('获取播放');
                return [
                    'parse' => 0,
                    'playUrl' => '',
                    'url' => $文件['path'],
                    'type' => in_array($文件['type'], ['mp3', 'wav', 'flac', 'aac', 'm4a', 'ogg', 'wma']) ? 'audio' : 'video'
                ];
            }
        }
    }
    
    // 直接返回播放地址，TVBox播放器会处理磁力链接和ed2k链接
    调试日志('播放', "播放链接: {$标识}");
    结束计时('获取播放');
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $标识,
        'type' => 'video'
    ];
}

/**
 * PHP爬虫功能总结：
 * 
 * 1. 文件格式支持：
 *    - JSON文件解析（影视数据）
 *    - TXT文件解析（名称+链接格式）
 *    - M3U文件解析（直播源）
 *    - SQLite数据库解析（多种字段格式）
 *    
 * 2. 链接协议支持：
 *    - HTTP/HTTPS在线视频
 *    - 磁力链接 (magnet:)
 *    - 电驴链接 (ed2k://)
 *    - RTMP/RTSP/UDP流媒体
 *    
 * 3. 媒体库功能：
 *    - 音频媒体库（MP3/WAV/FLAC/AAC等格式）
 *    - 视频媒体中心（MP4/AVI/MKV/MOV等格式）
 *    - 自动扫描根目录及无限子文件夹
 *    - 无资源时自动隐藏分类
 *    
 * 4. 文件夹分类：
 *    - 按文件夹自动分类媒体文件
 *    - 支持文件夹合并显示
 *    - 可控开关（0/1）控制分类显示
 *    
 * 5. 调试系统：
 *    - 完整调试日志记录
 *    - 手动开关控制（0关闭/1开启）
 *    - 性能监控和错误追踪
 *    - 多分类日志文件
 *    
 * 6. 搜索功能：
 *    - 关键词搜索视频和媒体文件
 *    - 分页显示搜索结果
 *    - 支持媒体文件搜索
 *    
 * 7. 热门推荐：
 *    - 随机推荐各分类视频
 *    - 避免重复推荐
 *    - 分页加载
 *    
 * 8. 性能优化：
 *    - 文件缓存机制
 *    - 内存使用控制
 *    - 超时时间设置
 *    - 递归深度限制
 要求：
 1：文件分类和文件夹分类没有完善，它们的开关也没有完善
 2：所有功能都加上自动隐藏功能，如同音/视频的隐藏功能
*/
?>






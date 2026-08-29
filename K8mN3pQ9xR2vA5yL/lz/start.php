<?php
/**
 * 配置同步脚本
 
 * 命令行参数：
 * php start.php insert [--no-scan]   # 扫描并处理配置，可选是否跳过扫描
 * php start.php scan-only             # 只扫描生成本地config.json
 */

// --------------------------------------------------------------------------
// 1. 全局配置定义
// --------------------------------------------------------------------------

// 本地配置文件的完整路径（指向 lz/config.json）
define('LOCAL_CONFIG_FILE', '/storage/emulated/0/lz/config.json');

// 基准模板配置文件的完整路径（指向 lz/lib/config.json）
define('BASE_TEMPLATE_FILE', '/storage/emulated/0/lz/lib/config.json');

// 默认PHP端口（当检测失败时使用）
define('DEFAULT_PHP_PORT', 9980);

// 扫描层级限制（0表示只扫描当前目录，1表示扫描一级子目录，依此类推）
define('MAX_SCAN_DEPTH', 5);

// XBPQ目录关键词配置（用于识别XBPQ目录，支持多个关键词）
define('XBPQ_DIR_KEYWORDS', ['PQ类']);
// XYQ目录关键词配置（用于识别XYQ目录，支持多个关键词）
define('XYQ_DIR_KEYWORDS', ['YQ类']);
// Drpy2目录关键词配置（用于识别Drpy2目录，支持多个关键词）
define('DRPY2_DIR_KEYWORDS', ['JS类']);
// 如果您想要添加多个关键词来识别XBPQ目录，可以这样配置：
// define('XBPQ_DIR_KEYWORDS', ['XBPQ类[XBPQ]', 'XBPQ', '小白盘搜索']);
// 如果您想要添加多个关键词来识别XYQ目录，可以这样配置：
// define('XYQ_DIR_KEYWORDS', ['YQ类[XYQ]', 'XYQ']);
// 如果您想要添加多个关键词来识别Drpy2目录，可以这样配置：
// define('DRPY2_DIR_KEYWORDS', ['JS[Drpy]', 'Drpy2']);
// --------------------------------------------------------------------------
// --------------------------------------------------------------------------
// 2. 辅助函数：动态检测PHP服务端口
// --------------------------------------------------------------------------

/**
 * 检测PHP服务端口（通过进程检测）
 * @return int 检测到的PHP服务端口，失败则返回默认端口
 */
function detectPhpPort() {
    echo "🔍 检测PHP服务端口... ";
    
    // 方法1: 使用ps aux命令
    $port = detectPortByCommand('ps aux');
    if ($port > 0) {
        echo "✅ 检测到端口: {$port}\n";
        return $port;
    }
    
    // 方法2: 使用pgrep命令
    $port = detectPortByCommand('pgrep -lf php');
    if ($port > 0) {
        echo "✅ 检测到端口: {$port}\n";
        return $port;
    }
    
    // 方法3: 使用shell组合命令
    $port = detectPortByShell('ps aux | grep php | grep -v grep');
    if ($port > 0) {
        echo "✅ 检测到端口: {$port}\n";
        return $port;
    }
    
    // 方法4: 使用/proc文件系统（Linux专用）
    $port = detectPortFromProc();
    if ($port > 0) {
        echo "✅ 检测到端口: {$port}\n";
        return $port;
    }
    
    // 所有方法都失败，使用默认端口
    echo "⚠️  无法检测到PHP服务端口，使用默认端口: " . DEFAULT_PHP_PORT . "\n";
    return DEFAULT_PHP_PORT;
}

/**
 * 通过执行命令检测端口
 * @param string $command 要执行的命令
 * @return int 检测到的端口，失败返回0
 */
function detectPortByCommand($command) {
    try {
        $output = [];
        exec($command . ' 2>&1', $output, $returnCode);
        
        if ($returnCode === 0 && !empty($output)) {
            foreach ($output as $line) {
                if (stripos($line, 'php') !== false && stripos($line, 'grep') === false) {
                    // 尝试在行中查找端口
                    if (preg_match('/:(\d{4,5})/', $line, $matches)) {
                        $port = intval($matches[1]);
                        if ($port >= 1024 && $port <= 65535) {
                            return $port;
                        }
                    }
                }
            }
        }
    } catch (Exception $e) {
        // 静默失败，继续尝试其他方法
    }
    
    return 0;
}

/**
 * 通过shell管道检测端口
 * @param string $shellCommand shell命令
 * @return int 检测到的端口，失败返回0
 */
function detectPortByShell($shellCommand) {
    try {
        $output = shell_exec($shellCommand);
        if ($output) {
            $lines = explode("\n", $output);
            foreach ($lines as $line) {
                if (trim($line) && stripos($line, 'php') !== false) {
                    if (preg_match('/:(\d{4,5})/', $line, $matches)) {
                        $port = intval($matches[1]);
                        if ($port >= 1024 && $port <= 65535) {
                            return $port;
                        }
                    }
                }
            }
        }
    } catch (Exception $e) {
        // 静默失败，继续尝试其他方法
    }
    
    return 0;
}

/**
 * 从/proc文件系统检测端口（Linux专用）
 * @return int 检测到的端口，失败返回0
 */
function detectPortFromProc() {
    if (!is_dir('/proc')) {
        return 0; // 不是Linux系统
    }
    
    try {
        $pids = scandir('/proc');
        foreach ($pids as $pid) {
            if (!is_numeric($pid)) {
                continue;
            }
            
            $cmdlineFile = "/proc/{$pid}/cmdline";
            if (file_exists($cmdlineFile)) {
                $cmdline = file_get_contents($cmdlineFile);
                if (stripos($cmdline, 'php') !== false) {
                    // 检查进程是否在监听端口
                    $netFile = "/proc/{$pid}/net/tcp";
                    if (file_exists($netFile)) {
                        $netContent = file_get_contents($netFile);
                        $lines = explode("\n", $netContent);
                        foreach ($lines as $line) {
                            if (strpos($line, ':') !== false) {
                                $parts = preg_split('/\s+/', trim($line));
                                if (count($parts) >= 4) {
                                    $localAddr = $parts[1];
                                    if (strpos($localAddr, ':') !== false) {
                                        $portHex = substr($localAddr, strrpos($localAddr, ':') + 1);
                                        $port = hexdec($portHex);
                                        if ($port >= 1024 && $port <= 65535) {
                                            return $port;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    } catch (Exception $e) {
        // 静默失败
    }
    
    return 0;
}

// --------------------------------------------------------------------------
// 3. 执行扫描功能并生成配置
function generateLocalConfig() {
    // --------------------------------------------------------------------------
    // 1. 全局定义与排除策略
    // --------------------------------------------------------------------------

    /**
     * 文件类型关联配置
     */
    $fileConfig = [
        'wv.js'   => [
            'api'  => 'csp_WvSpider',
            'jar'  => '../lz/lib/WvSpider.jar',
            'type' => 3
        ],
        'txt,m3u,json' => [
            'api'  => 'csp_FileSpider',
            'jar'  => '../lz/lib/WvSpider.jar',
            'type' => 3
        ],
        'php' => [
            'type' => 4,
            'searchable' => 0,
            'quickSearch' => 0
        ],
    ];

    // XBPQ目录的特殊配置
    $xbpqConfig = [
        'api'  => 'csp_XBPQ',
        'jar'  => '../lz/lib/XBPQ.jar',
        'type' => 3
    ];

    // XYQ目录的特殊配置
    $xyqConfig = [
        'api'  => 'csp_XYQHiker',
        'jar'  => '../lz/lib/XYQ.jar',
        'type' => 3
    ];

    // Drpy2目录的特殊配置
    $drpy2Config = [
        'api'  => '../lz/lib/lib/drpy2.min.js',
        'type' => 3
    ];

    // 动态检测PHP服务端口
    $phpPort = detectPhpPort();
    $phpApiPrefix = "http://127.0.0.1:{$phpPort}";

    // 允许处理的文件后缀
    $allowedExtensions = ['js', 'wv.js', 'txt', 'm3u', 'php', 'py', 'json'];

    // 排除遍历的目录
    $excludeDirs = ['lib', '直播转点播辅助文件', 'novel','.', '..'];

    // 指定排除的文件名（不输出至配置）
    $excludeFiles = ['index.php', 'test_runner.php', 'config.php','影书音大全.json','采集大全.json','采集集合.js','🎮小游戏.js', '此文件夹说明.txt', 'start.py'];

    // 直播资源目录名
    $liveDirName = '直播文件';

    // --------------------------------------------------------------------------
    // 2. 站点隐藏配置开关
    // --------------------------------------------------------------------------

    /**
     * 站点文件隐藏开关 - 控制目录名带"[秘]"的站点是否隐藏
     * true: 隐藏 (hide: 1)
     * false: 不隐藏 (hide: 0)
     */
    $hideSecretSites = true; // 可根据需要修改为 true 或 false

    // --------------------------------------------------------------------------
    // 3. 扫描引擎
    // --------------------------------------------------------------------------

    $currentDir = '/storage/emulated/0/lz';
    $scannedSites = [];
    $scannedLives = [];

    /**
     * 辅助：提取后缀信息（支持双重后缀）
     */
    function getFileExtensionInfo($filename) {
        $parts = explode('.', $filename);
        $count = count($parts);
        if ($count >= 3) {
            return [
                'full'   => $parts[$count - 2] . '.' . $parts[$count - 1],
                'simple' => $parts[$count - 1],
                'name'   => implode('.', array_slice($parts, 0, $count - 2))
            ];
        }
        return [
            'full'   => pathinfo($filename, PATHINFO_EXTENSION),
            'simple' => pathinfo($filename, PATHINFO_EXTENSION),
            'name'   => pathinfo($filename, PATHINFO_FILENAME)
        ];
    }

    /**
     * 从目录名中提取标签 - 提取所有类型的标签
     * @param string $dirName 目录名
     * @return string 提取的标签，如[电影]、[电视剧]等
     */
    function extractTagFromDirName($dirName) {
        // 匹配所有可能的标签格式：[xxx]
        if (preg_match('/\[([^\]]+)\]/', $dirName, $matches)) {
            return '[' . $matches[1] . ']';
        }
        return '';
    }

    /**
     * 检查目录名是否包含特定标签并返回处理后的标签
     * @param string $dirName 目录名
     * @return array [过滤后的标签, 目录类型('book', 'comic', 'drama', 'other')]
     */
    function checkDirTypeAndFilterTag($dirName) {
        // 检查是否包含[书]、[画]或[短剧]标签
        $isBookDir = (strpos($dirName, '[书]') !== false);
        $isComicDir = (strpos($dirName, '[画]') !== false);
        $isDramaDir = (strpos($dirName, '[短剧]') !== false);
        
        // 复制目录名用于处理
        $processedDirName = $dirName;
        
        // 如果是书、漫画、短剧目录，移除对应的标签
        $tagToRemove = '';
        $dirType = 'other';
        if ($isBookDir) {
            $tagToRemove = '[书]';
            $dirType = 'book';
        } elseif ($isComicDir) {
            $tagToRemove = '[画]';
            $dirType = 'comic';
        } elseif ($isDramaDir) {
            $tagToRemove = '[短剧]';
            $dirType = 'drama';
        }
        
        if ($tagToRemove !== '') {
            $processedDirName = str_replace($tagToRemove, '', $processedDirName);
        }
        
        // 从处理后的目录名中提取其他标签
        $filteredTag = '';
        if (preg_match('/\[([^\]]+)\]/', $processedDirName, $matches)) {
            $filteredTag = '[' . $matches[1] . ']';
        }
        
        return [$filteredTag, $dirType];
    }

    /**
     * 辅助：构建站点配置成员
     * 新增参数 $phpApiPrefix 用于处理PHP文件的API路径
     * 新增参数 $dirType 用于处理书和漫画目录的特殊字段
     * 新增参数 $filteredTag 用于处理过滤后的标签
     * 新增参数 $isXBPQDir 用于判断是否在XBPQ目录中
     * 新增参数 $isXYQDir 用于判断是否在XYQ目录中
     * 新增参数 $isDrpy2Dir 用于判断是否在Drpy2目录中
     */
    function buildSiteConfig($name, $filteredTag, $extInfo, $localPath, $fileConfig, $phpApiPrefix, $dirType, $isXBPQDir = false, $isXYQDir = false, $isDrpy2Dir = false) {
        $ext = $extInfo['full'];
        $simpleExt = $extInfo['simple'];
        
        // 检查文件名中是否包含[书]、[画]或[短剧]标签
        $hasBookTag = (strpos($name, '[书]') !== false);
        $hasComicTag = (strpos($name, '[画]') !== false);
        $hasDramaTag = (strpos($name, '[短剧]') !== false);
        
        // 移除文件名中的所有方括号标签
        $cleanName = preg_replace('/\[[^\]]*\]/', '', $name);
        
        // 对于书、漫画和短剧目录，不添加目录标签
        if ($dirType === 'book' || $dirType === 'comic' || $dirType === 'drama' || $hasBookTag || $hasComicTag || $hasDramaTag) {
            $fullName = $cleanName . '(' . strtoupper($ext) . ')';
        } else {
            $fullName = $cleanName . $filteredTag . '(' . strtoupper($ext) . ')';
        }
        
        $config = [
            'key'        => $fullName,
            'name'       => $fullName,
            'type'       => 3,
            'api'        => $localPath,
            'searchable' => 1,
            'filterable' => 1,
            'switchable' => 1
        ];

        // 如果是XBPQ目录下的json文件，使用特殊配置
        if ($isXBPQDir && $ext === 'json') {
            $config['api'] = 'csp_XBPQ';
            $config['jar'] = '../lz/lib/XBPQ.jar';
            $config['type'] = 3;
            $config['ext'] = $localPath;
        } 
        // 如果是XYQ目录下的json文件，使用特殊配置
        elseif ($isXYQDir && $ext === 'json') {
            $config['api'] = 'csp_XYQHiker';
            $config['jar'] = '../lz/lib/XYQ.jar';
            $config['type'] = 3;
            $config['ext'] = $localPath;
        } 
        // 如果是Drpy2目录下的js文件，使用特殊配置
        elseif ($isDrpy2Dir && $ext === 'js') {
            $config['api'] = '../lz/lib/lib/drpy2.min.js';
            $config['type'] = 3;
            $config['ext'] = $localPath;
        } else {
            // 否则按原有逻辑处理
            foreach ($fileConfig as $matchExts => $overrides) {
                $extList = array_map('trim', explode(',', $matchExts));
                if (in_array($ext, $extList)) {
                    foreach ($overrides as $key => $val) {
                        if ($key === 'api' && !empty($val)) {
                            $config['api'] = $val;
                            $config['ext'] = $localPath;
                        } else {
                            $config[$key] = $val;
                        }
                    }
                    break;
                }
            }
        }
        
        // 特殊处理PHP文件的API路径
        if ($ext === 'php') {
            // 移除路径开头的"./"
            $cleanPath = ltrim($localPath, './');
            // 拼接HTTP API路径
            $config['api'] = $phpApiPrefix . '/' . $cleanPath;
        }
        
        // 根据目录类型添加特殊字段
        if ($dirType === 'book' || $hasBookTag) {
            // 书目录：添加小说类型相关字段
            $config['title'] = $cleanName;  // 小说名称
            $config['类型'] = '小说';
            $config['lang'] = $simpleExt;  // 文件扩展名作为语言标识
        } elseif ($dirType === 'comic' || $hasComicTag) {
            // 漫画目录：添加漫画类型相关字段
            $config['title'] = $cleanName;  // 漫画名称
            $config['类型'] = '漫画';
            $config['lang'] = $simpleExt;  // 文件扩展名作为语言标识
        } elseif ($dirType === 'drama' || $hasDramaTag) {
            // 短剧目录：添加短剧类型相关字段
            $config['title'] = $cleanName;  // 短剧名称
            $config['类型'] = '短剧';
            $config['lang'] = $simpleExt;  // 文件扩展名作为语言标识
        }
        
        return $config;
    }

    /**
     * 递归扫描目录函数 - 支持多层级目录结构
     * 修改：每个文件只使用其所在直接目录的标签，不继承父目录标签
     * 修改：支持XBPQ、XYQ、Drpy2目录的子目录中的文件识别
     */
    function scanDirectoryRecursive($path, &$scannedSites, &$scannedLives, $currentDir, $fileConfig, $allowedExtensions, $excludeDirs, $excludeFiles, $liveDirName, $hideSecretSites, $phpApiPrefix, $parentIsXBPQDir = false, $parentIsXYQDir = false, $parentIsDrpy2Dir = false, $currentDepth = 0, $maxDepth = MAX_SCAN_DEPTH) {
        // 检查深度限制
        if ($currentDepth > $maxDepth) {
            return;
        }
        
        // 获取当前目录相对于脚本目录的路径
        // 修复：使用更可靠的路径处理方法，确保只替换开头的路径
        $relativeDirPath = '';
        if (strpos($path, $currentDir) === 0) {
            // 确保$currentDir以目录分隔符结尾
            $currentDirWithSlash = rtrim($currentDir, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR;
            if (strpos($path, $currentDirWithSlash) === 0) {
                // 如果路径以$currentDir/开头，替换为./
                $relativeDirPath = './' . substr($path, strlen($currentDirWithSlash));
            } elseif ($path === $currentDir) {
                // 如果路径就是$currentDir，替换为./
                $relativeDirPath = './';
            } else {
                // 其他情况，使用原始路径
                $relativeDirPath = './' . $path;
            }
        } else {
            // 如果路径不在$currentDir下，使用原始路径
            $relativeDirPath = './' . $path;
        }
        // 规范化路径：统一使用/作为分隔符
        $relativeDirPath = str_replace('\\', '/', $relativeDirPath);
        $pathParts = explode('/', ltrim($relativeDirPath, './'));
        
        // 规范化路径以确保一致性（处理尾随斜杠等差异）
        $normalizedPath = rtrim($path, DIRECTORY_SEPARATOR);
        $normalizedCurrentDir = rtrim($currentDir, DIRECTORY_SEPARATOR);
        $isRootDir = ($normalizedPath === $normalizedCurrentDir);
        $isLiveDir = (count($pathParts) === 1 && $pathParts[0] === $liveDirName);
        
        // 获取当前目录名
        $currentDirName = basename($path);
        
        // 判断当前目录是否包含"[秘]"
        $isSecretDir = (strpos($currentDirName, '[秘]') !== false);
        
        // 判断当前目录是否为XBPQ目录，或者父目录是XBPQ目录
        $isXBPQDir = $parentIsXBPQDir; // 先继承父目录的状态
        if (!$isXBPQDir) { // 如果父目录不是XBPQ目录，检查当前目录
            foreach (XBPQ_DIR_KEYWORDS as $keyword) {
                if (strpos($currentDirName, $keyword) !== false) {
                    $isXBPQDir = true;
                    break;
                }
            }
        }
        
        // 判断当前目录是否为XYQ目录，或者父目录是XYQ目录
        $isXYQDir = $parentIsXYQDir; // 先继承父目录的状态
        if (!$isXYQDir) { // 如果父目录不是XYQ目录，检查当前目录
            foreach (XYQ_DIR_KEYWORDS as $keyword) {
                if (strpos($currentDirName, $keyword) !== false) {
                    $isXYQDir = true;
                    break;
                }
            }
        }
        
        // 判断当前目录是否为Drpy2目录，或者父目录是Drpy2目录
        $isDrpy2Dir = $parentIsDrpy2Dir; // 先继承父目录的状态
        if (!$isDrpy2Dir) { // 如果父目录不是Drpy2目录，检查当前目录
            foreach (DRPY2_DIR_KEYWORDS as $keyword) {
                if (strpos($currentDirName, $keyword) !== false) {
                    $isDrpy2Dir = true;
                    break;
                }
            }
        }
        
        // 检查目录类型并获取过滤后的标签
        list($filteredTag, $dirType) = checkDirTypeAndFilterTag($currentDirName);
        
        // 读取目录内容
        $items = scandir($path);
        
        foreach ($items as $item) {
            // 过滤排除目录
            if (in_array($item, $excludeDirs)) continue;
            
            $fullPath = $path . DIRECTORY_SEPARATOR . $item;
            // 修复：使用更可靠的路径处理方法，确保只替换开头的路径
            $localPath = '';
            if (strpos($fullPath, $currentDir) === 0) {
                // 确保$currentDir以目录分隔符结尾
                $currentDirWithSlash = rtrim($currentDir, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR;
                if (strpos($fullPath, $currentDirWithSlash) === 0) {
                    // 如果路径以$currentDir/开头，替换为./
                    $localPath = './' . substr($fullPath, strlen($currentDirWithSlash));
                } elseif ($fullPath === $currentDir) {
                    // 如果路径就是$currentDir，替换为./
                    $localPath = './';
                } else {
                    // 其他情况，使用原始路径
                    $localPath = './' . $fullPath;
                }
            } else {
                // 如果路径不在$currentDir下，使用原始路径
                $localPath = './' . $fullPath;
            }
            // 规范化路径：统一使用/作为分隔符
            $localPath = str_replace('\\', '/', $localPath);

            // 如果是目录且不是根目录，递归扫描
            if (is_dir($fullPath)) {
                // 直播目录下不再深入
                if ($isLiveDir) continue;
                
                // 递归扫描子目录（深度+1），传递当前的特殊目录状态
                scanDirectoryRecursive($fullPath, $scannedSites, $scannedLives, $currentDir, $fileConfig, $allowedExtensions, $excludeDirs, $excludeFiles, $liveDirName, $hideSecretSites, $phpApiPrefix, $isXBPQDir, $isXYQDir, $isDrpy2Dir, $currentDepth + 1, $maxDepth);
                continue;
            }

            // 处理文件
            // 不遍历 config.php 所在目录（根目录）下的文件
            if ($isRootDir) continue;

            // 过滤排除文件
            if (in_array($item, $excludeFiles)) continue;

            $extInfo = getFileExtensionInfo($item);
            $ext = $extInfo['full'];

            // 后缀白名单校验
            if (!in_array($ext, $allowedExtensions) && !in_array($extInfo['simple'], $allowedExtensions)) {
                continue;
            }

            // 解析文件名
            $displayName = $extInfo['name'];

            if ($isLiveDir) {
                // 直播文件 - 使用当前目录标签（过滤后的标签）
                $scannedLives[] = [
                    'name'       => $displayName . $filteredTag,
                    'type'       => 0,
                    'url'        => $localPath,
                    'playerType' => 2,
                    'epg'        => "http://epg.51zmt.top:8000/api/diyp/?ch={name}&date={date}",
                    'logo'       => "https://11.112114.xyz/logo/{$displayName}.png",
                    'ua'         => ''
                ];
            } else {
                // 站点文件：使用过滤后的标签和目录类型，以及是否在特殊目录的判断
                $siteConfig = buildSiteConfig($displayName, $filteredTag, $extInfo, $localPath, $fileConfig, $phpApiPrefix, $dirType, $isXBPQDir, $isXYQDir, $isDrpy2Dir);
                
                // 如果文件在带"[秘]"的目录中，根据开关设置hide字段
                if ($isSecretDir && $hideSecretSites) {
                    $siteConfig['hide'] = 1;
                }
                
                $scannedSites[] = $siteConfig;
            }
        }
    }

    // --------------------------------------------------------------------------
    // 4. 数据合并与结果输出
    // --------------------------------------------------------------------------

    // 1. 加载基准模版 config.json
    $baseConfigPath = BASE_TEMPLATE_FILE;
    $finalData = [];

    if (file_exists($baseConfigPath)) {
        $jsonContent = file_get_contents($baseConfigPath);
        $finalData = json_decode($jsonContent, true) ?: [];
        
        // 注释掉端口自动替换逻辑，保持基准模板中的端口不变
        // if (isset($finalData['sites']) && is_array($finalData['sites'])) {
        //     foreach ($finalData['sites'] as &$site) {
        //         if (isset($site['api']) && strpos($site['api'], 'http://127.0.0.1:') === 0) {
        //             // 更新端口为最新检测到的端口
        //             $site['api'] = preg_replace('/http:\/\/127\.0\.0\.1:\d+/', "http://127.0.0.1:{$phpPort}", $site['api']);
        //         }
        //     }
        // }
    } else {
        echo "   ⚠️  基准模板文件不存在: " . $baseConfigPath . "\n";
    }

    // 2. 执行目录扫描逻辑
    scanDirectoryRecursive($currentDir, $scannedSites, $scannedLives, $currentDir, $fileConfig, $allowedExtensions, $excludeDirs, $excludeFiles, $liveDirName, $hideSecretSites, $phpApiPrefix, false, false, false);

    // 3. 追加扫描到的站点（直接使用基准模板，不做去重）
    if (!isset($finalData['sites']) || !is_array($finalData['sites'])) {
        $finalData['sites'] = [];
    }
    $finalData['sites'] = array_merge($finalData['sites'], $scannedSites);

    // 4. 追加扫描到的直播
    if (!isset($finalData['lives']) || !is_array($finalData['lives'])) {
        $finalData['lives'] = [];
    }
    $finalData['lives'] = array_merge($finalData['lives'], $scannedLives);

    return $finalData;
}

// --------------------------------------------------------------------------
// 4. 核心功能类
// --------------------------------------------------------------------------

class ConfigSync {
    
    /**
     * 检查本地配置文件是否存在
     * @param string $filePath 文件路径
     * @return bool 返回true表示文件存在
     */
    public static function checkLocalConfig($filePath = LOCAL_CONFIG_FILE) {
        return file_exists($filePath);
    }
    
    /**
     * 读取本地配置文件
     * @param string $filePath 文件路径
     * @return array 返回解析后的配置数组
     * @throws Exception 读取或解析失败时抛出异常
     */
    public static function readLocalConfig($filePath = LOCAL_CONFIG_FILE) {
        $json = @file_get_contents($filePath);
        if ($json === false) {
            throw new Exception('无法读取配置文件: ' . $filePath);
        }
        
        $data = json_decode($json, true);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('配置文件JSON格式无效: ' . json_last_error_msg() . ' - ' . $filePath);
        }
        
        return $data;
    }
    
    /**
     * 处理重复的key值，将后面的key按序加后缀重命名
     * @param array $sites 站点数组
     * @return array 返回去重后的站点数组
     */
    public static function deduplicateKeys($sites) {
        $keyCounts = [];
        $processedSites = [];
        
        foreach ($sites as $site) {
            if (!isset($site['key'])) {
                // 如果没有key字段，则跳过
                $processedSites[] = $site;
                continue;
            }
            
            $originalKey = $site['key'];
            $newKey = $originalKey;
            
            // 检查key是否已存在
            if (isset($keyCounts[$originalKey])) {
                // 如果已存在，开始添加后缀
                $counter = 1;
                $newKey = $originalKey . '_' . $counter;
                
                // 循环直到找到一个不重复的key
                while (isset($keyCounts[$newKey])) {
                    $counter++;
                    $newKey = $originalKey . '_' . $counter;
                }
                
                // 记录这个新key
                $keyCounts[$originalKey] = $counter;
                $site['key'] = $newKey;
                $site['name'] = isset($site['name']) ? $site['name'] . " ({$counter})" : $originalKey . " ({$counter})";
                
                // 提示信息
                echo "   发现重复key: '{$originalKey}'，已重命名为: '{$newKey}'\n";
            } else {
                // 首次出现，记录原始key
                $keyCounts[$originalKey] = 0;
            }
            
            // 记录新key
            $keyCounts[$newKey] = true;
            $processedSites[] = $site;
        }
        
        return $processedSites;
    }
    
    /**
     * 检查是否有重复的key值（用于验证去重结果）
     * @param array $sites 站点数组
     * @return bool 返回true表示无重复
     * @throws Exception 发现重复key时抛出异常
     */
    public static function verifyNoDuplicateKeys($sites) {
        $keys = [];
        
        foreach ($sites as $site) {
            if (isset($site['key'])) {
                $key = $site['key'];
                if (in_array($key, $keys)) {
                    throw new Exception("发现重复的key值: '{$key}'，去重逻辑失败");
                }
                $keys[] = $key;
            }
        }
        
        return true;
    }
    
    /**
     * 保存配置文件
     * @param array $config 配置数组
     * @param string $filePath 文件路径
     * @return bool 返回true表示保存成功
     * @throws Exception 保存失败时抛出异常
     */
    public static function saveConfig($config, $filePath = LOCAL_CONFIG_FILE) {
        // 格式化JSON
        $json = json_encode($config, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception('生成JSON时出错: ' . json_last_error_msg());
        }
        
        // 保存文件
        $result = @file_put_contents($filePath, $json);
        if ($result === false) {
            throw new Exception('保存配置文件失败: ' . $filePath);
        }
        
        return true;
    }
    
    /**
     * 切换配置模式
     * 用于在 aa.json 和 config.json 之间互相切换
     */
    public static function switchConfigMode() {
        echo "📌 模式选择：切换配置模式\n";
        echo str_repeat("-", 80) . "\n";
        
        try {
            $aaConfigFile = '/storage/emulated/0/lz/aa.json';
            $configBackupFile = '/storage/emulated/0/lz/config.json.bak';
            $currentConfigFile = LOCAL_CONFIG_FILE;
            
            // 检查当前配置是否是 aa.json（通过比较文件内容或标记判断）
            $isCurrentlyAa = false;
            if (file_exists($currentConfigFile) && file_exists($aaConfigFile)) {
                $currentConfig = self::readLocalConfig($currentConfigFile);
                $aaConfig = self::readLocalConfig($aaConfigFile);
                // 通过比较第一个站点的 key 来判断当前配置
                if (isset($currentConfig['sites'][0]['key']) && isset($aaConfig['sites'][0]['key'])) {
                    $isCurrentlyAa = ($currentConfig['sites'][0]['key'] === $aaConfig['sites'][0]['key']);
                }
            }
            
            if ($isCurrentlyAa) {
                // 当前是 aa.json，切换回 config.json
           //     echo "   当前配置: aa.json\n";
            //    echo "   目标配置: config.json\n";
                
                if (!file_exists($configBackupFile)) {
                    throw new Exception('config.json.bak 备份文件不存在，无法切换回原始配置');
                }
                
                // 读取备份的 config.json
                $config = self::readLocalConfig($configBackupFile);
                
                // 修改 switch-config 站点的名称，显示可以切换到 aa
                $config = self::updateSwitchConfigName($config, 'aa');
                
                // 保存到 config.json
                self::saveConfig($config, $currentConfigFile);
                
                echo "✅ 已成功切换回 LZ原包\n";
            } else {
                // 当前是 config.json，切换到 aa.json
            //    echo "   当前配置: config.json\n";
            //    echo "   目标配置: aa.json\n";
                
                if (!file_exists($aaConfigFile)) {
                    throw new Exception('aa.json 配置文件不存在: ' . $aaConfigFile);
                }
                
                // 先备份当前的 config.json
                if (file_exists($currentConfigFile)) {
                    copy($currentConfigFile, $configBackupFile);
                //    echo "   已备份当前配置到 config.json.bak\n";
                }
                
                // 读取 aa.json 配置
                $aaConfig = self::readLocalConfig($aaConfigFile);
                
                // 修改 switch-config 站点的名称，显示可以切换到 config
                $aaConfig = self::updateSwitchConfigName($aaConfig, 'config');
                
                // 保存到 config.json
                self::saveConfig($aaConfig, $currentConfigFile);
                
                echo "✅ 已成功切换到 增强包\n";
            }
            
            echo "✅ 配置已保存到: " . $currentConfigFile . "\n";
            
        } catch (Exception $e) {
            throw new Exception("切换配置失败: " . $e->getMessage());
        }
        
        echo str_repeat("-", 80) . "\n";
        echo "🎉 切换完成！请切换其他站点享受快乐\n";
    }
    
    /**
     * 更新 switch-config 站点的名称
     * @param array $config 配置数组
     * @param string $targetConfig 目标配置名称 ('aa' 或 'config')
     * @return array 更新后的配置数组
     */
    private static function updateSwitchConfigName($config, $targetConfig) {
        if (isset($config['sites']) && is_array($config['sites'])) {
            foreach ($config['sites'] as $key => $site) {
                if (isset($site['key']) && $site['key'] === 'switch-config') {
                    if ($targetConfig === 'aa') {
                        $config['sites'][$key]['name'] = '🔄切到LZ原包 ';
                    } else {
                        $config['sites'][$key]['name'] = '🔄切到增强包 ';
                    }
                    break;
                }
            }
        }
        return $config;
    }
    
    /**
     * 只执行扫描模式
     * 修改：统一使用基准模板文件
     */
    public static function scanOnlyMode() {
        echo "📌 模式选择：只扫描模式\n";
   /*     echo "   基准模板: " . BASE_TEMPLATE_FILE . "\n";
        echo "   扫描层级限制: " . MAX_SCAN_DEPTH . " 层\n";*/
        echo str_repeat("-", 80) . "\n";
        
        // 0. 执行文件扫描生成本地配置
        echo "0. 执行文件扫描生成本地配置... \n";
        try {
            // 调用集成的config.php功能，使用统一基准模板
            $localConfig = generateLocalConfig();
            
            // 保存生成的配置到本地文件
            $json = json_encode($localConfig, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
            if ($json === false) {
                throw new Exception('生成JSON失败: ' . json_last_error_msg());
            }
            
            $result = file_put_contents(LOCAL_CONFIG_FILE, $json);
            if ($result === false) {
                throw new Exception('保存配置文件失败，请检查文件权限: ' . LOCAL_CONFIG_FILE);
            }
            
            // 统计站点和直播数量
            $siteCount = isset($localConfig['sites']) ? count($localConfig['sites']) : 0;
            $liveCount = isset($localConfig['lives']) ? count($localConfig['lives']) : 0;
            
            echo "✅ 文件扫描完成，生成 {$siteCount} 个站点，{$liveCount} 个直播\n";
            echo "✅ 配置已保存到: " . LOCAL_CONFIG_FILE . "\n";
        } catch (Exception $e) {
            throw new Exception("文件扫描失败: " . $e->getMessage());
        }
        
        echo str_repeat("-", 45) . "\n";
        echo "🎉 刷新完成！请切换其他站点享受快乐！\n";
    }
    
    /**
     * 扫描并处理配置模式
     * 修改：不再调用外部config.php服务，而是集成其功能
     * @param bool $doScan 是否执行扫描步骤
     */
    public static function insertMode($doScan = true) {
        echo "📌 模式选择：扫描并处理配置模式\n";
        echo "   基准模板: " . BASE_TEMPLATE_FILE . "\n";
        echo "   扫描层级限制: " . MAX_SCAN_DEPTH . " 层\n";
        if (!$doScan) {
            echo "   ⚠️  跳过扫描步骤\n";
        }
        echo str_repeat("-", 40) . "\n";
        
        // 0. 执行文件扫描生成本地配置（集成版）
        if ($doScan) {
            echo "0. 执行文件扫描生成本地配置... \n";
            try {
                // 调用集成的config.php功能，使用统一基准模板
                $localConfig = generateLocalConfig();
                
                // 保存生成的配置到本地文件
                $json = json_encode($localConfig, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
                if ($json === false) {
                    throw new Exception('生成JSON失败: ' . json_last_error_msg());
                }
                
                $result = file_put_contents(LOCAL_CONFIG_FILE, $json);
                if ($result === false) {
                    throw new Exception('保存配置文件失败，请检查文件权限: ' . LOCAL_CONFIG_FILE);
                }
                
                // 统计站点和直播数量
                $siteCount = isset($localConfig['sites']) ? count($localConfig['sites']) : 0;
                $liveCount = isset($localConfig['lives']) ? count($localConfig['lives']) : 0;
                
                echo "✅ 文件扫描完成，生成 {$siteCount} 个站点，{$liveCount} 个直播 ({$result} 字节)\n";
            } catch (Exception $e) {
                throw new Exception("文件扫描失败，无法生成本地配置: " . $e->getMessage());
            }
        } else {
            echo "0. 跳过扫描步骤，使用现有配置文件\n";
        }
        
        echo str_repeat("-", 40) . "\n";
        
        // 1. 读取本地配置
        echo "1. 读取本地配置文件... ";
        $localConfig = self::readLocalConfig();
        
        if (!isset($localConfig['sites']) || !is_array($localConfig['sites'])) {
            throw new Exception('本地配置文件缺少sites字段或格式不正确');
        }
        
        $localCount = count($localConfig['sites']);
        echo "✅ 读取成功，共 {$localCount} 个站点\n";
        
        // 2. 处理重复key（按序加后缀重命名）
        echo "2. 处理重复key... ";
        $localConfig['sites'] = self::deduplicateKeys($localConfig['sites']);
        echo "✅ 重复key处理完成\n";
        
        // 3. 验证去重结果
        echo "3. 验证去重结果... ";
        self::verifyNoDuplicateKeys($localConfig['sites']);
        echo "✅ 无重复key\n";
        
        // 4. 更新配置并保存
        echo "4. 保存配置文件... ";
        self::saveConfig($localConfig);
        echo "✅ 保存成功\n";
        
        // 输出统计信息
        echo str_repeat("-", 40) . "\n";
        echo "📊 同步统计信息：\n";
        if ($doScan) {
            echo "   扫描本地站点数: {$localCount}\n";
        } else {
            echo "   原本地站点数: {$localCount}\n";
        }
        echo "   总站点数: " . count($localConfig['sites']) . "\n";
        echo "   扫描层级限制: " . MAX_SCAN_DEPTH . " 层\n";
        echo "   配置文件: " . LOCAL_CONFIG_FILE . "\n";
    }
    

    /**
     * 主执行函数
     * @param string $mode 执行模式：'insert' 或 'scan-only'
     * @param array $options 选项数组，包含 'no-scan' 等
     */
    public static function run($mode = 'insert', $options = []) {
        echo "🚀 开始执行配置同步...\n";
        
        try {
            // 根据参数选择执行模式
            if ($mode === 'scan-only') {
                self::scanOnlyMode();
            } elseif ($mode === 'switch-config') {
                self::switchConfigMode();
            } else {
                // 扫描并处理配置模式，根据选项决定是否扫描
                $doScan = !isset($options['no-scan']) || $options['no-scan'] !== true;
                self::insertMode($doScan);
            }
            
            echo str_repeat("-", 40) . "\n";
            echo "🎉 同步完成！\n";
            
        } catch (Exception $e) {
            echo "❌ 错误: " . $e->getMessage() . "\n";
            echo str_repeat("-", 40) . "\n";
            echo "💡 建议：\n";
            
            if ($mode === 'insert') {
                echo "   1. 确保脚本目录结构正确\n";
                echo "   2. 确认配置文件格式正确\n";
            } elseif ($mode === 'scan-only') {
                echo "   1. 确保脚本目录结构正确\n";
                echo "   2. 检查基准模板文件是否存在: " . BASE_TEMPLATE_FILE . "\n";
                echo "   3. 确认有文件扫描权限\n";
            } elseif ($mode === 'switch-config') {
                echo "   1. 确保 aa.json 配置文件存在\n";
                echo "   2. 确认 aa.json 格式正确\n";
                echo "   3. 确认有文件写入权限\n";
            }
            
            // 不要exit(1)，让异常向上抛出
            throw $e;
        }
    }
}

// --------------------------------------------------------------------------
// 5. 脚本执行入口
// --------------------------------------------------------------------------

// 设置时区（避免时间相关错误）
date_default_timezone_set('Asia/Shanghai');

// 设置错误显示
error_reporting(E_ALL);
ini_set('display_errors', 1);

// 检查是否在CLI模式下运行
if (php_sapi_name() === 'cli') {
    // CLI模式运行，支持参数选择模式
    $mode = 'insert'; // 默认模式
    $options = [];
    
    // 解析命令行参数
    if (isset($argv[1])) {
        $arg = strtolower($argv[1]);
        if ($arg === 'insert') {
            $mode = 'insert';
        } elseif ($arg === 'scan-only') {
            $mode = 'scan-only';
        } elseif ($arg === 'switch-config') {
            $mode = 'switch-config';
        } else {
            echo "❌ 错误：未知模式 '{$argv[1]}'\n";
            echo "💡 用法：\n";
            echo "   扫描并处理配置（默认）：php " . basename(__FILE__) . " insert\n";
            echo "   扫描并处理配置（跳过扫描）：php " . basename(__FILE__) . " insert --no-scan\n";
            echo "   只扫描模式：php " . basename(__FILE__) . " scan-only\n";
            echo "   切换配置模式：php " . basename(__FILE__) . " switch-config\n";
            exit(1);
        }
        
        // 检查是否有--no-scan选项
        if (isset($argv[2]) && $argv[2] == '--no-scan') {
            if ($mode === 'insert') {
                $options['no-scan'] = true;
            } else {
                echo "⚠️  警告：--no-scan 选项只对扫描并处理配置模式有效\n";
            }
        }
    }
    
    ConfigSync::run($mode, $options);
} else {
    // Web模式运行（HTTP访问）
    header('Content-Type: text/plain; charset=utf-8');
    echo "⚠️⚠️⚠️注意：以上错误不影响使用，请忽略。\n";

    echo str_repeat("=", 49) . "\n";
    echo "⏰ 开始时间: " . date('Y-m-d H:i:s') . "\n";
    // Web模式下默认使用扫描并处理配置模式
    $mode = 'insert';
    $options = [];
    
    // 尝试从GET参数获取模式
    if (isset($_GET['mode'])) {
        $arg = strtolower($_GET['mode']);
        if ($arg === 'scan-only' || $arg === 'template') {
            // template 模式与 scan-only 模式相同，都是只扫描生成本地配置
            $mode = 'scan-only';
        } elseif ($arg === 'switch-config') {
            // 切换配置模式，用于切换到 aa.json 配置
            $mode = 'switch-config';
        }
    }
    
    // 检查是否有no-scan参数
    if (isset($_GET['no-scan']) && $_GET['no-scan'] == '1') {
        $options['no-scan'] = true;
    }
    
    // 执行同步
    ob_start();
    try {
        ConfigSync::run($mode, $options);
    } catch (Exception $e) {
        // 异常已经在run方法中处理并输出
    }
    $output = ob_get_clean();
    
    // 输出结果
    echo $output;
    echo "\n" . str_repeat("=", 49) . "\n";
    echo "结束时间: " . date('Y-m-d H:i:s') . "\n";
}
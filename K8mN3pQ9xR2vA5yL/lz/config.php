<?php
/**
 * Copyright 道长所有
 * Date: 2026/01/23
 */
header('Content-Type: application/json; charset=utf-8');
// http://127.0.0.1:9980/config.php
// ==================
// 1. 生成 sites
// ==================
// 动态获取服务器地址（支持局域网访问）
$host = $_SERVER['HTTP_HOST'] ?? $_SERVER['SERVER_ADDR'] ?? '127.0.0.1:9980';
if (strpos($host, ':') === false) {
    $port = $_SERVER['SERVER_PORT'] ?? '9980';
    $host = $host . ':' . $port;
}
$baseUrl = "http://" . $host;

$self = basename(__FILE__);

// 禁止扫描的目录（相对于每个标签目录的路径）
$excludeDirectories = [
    'lib',        // 禁止扫描标签目录下的 lib 目录
    // 可以添加更多禁止扫描的目录
    // 'temp',
    // 'cache',
    // 'config',
];

// XBPQ目录关键词配置（与start.php保持一致）
$XBPQ_DIR_KEYWORDS = ['PQ类'];
// XYQ目录关键词配置（与start.php保持一致）
$XYQ_DIR_KEYWORDS = ['YQ类'];
// Drpy2目录关键词配置（与start.php保持一致）
$DRPY2_DIR_KEYWORDS = ['JS类'];

// 检查目录是否为特殊目录（XBPQ、XYQ、Drpy2）
function checkSpecialDirectory($dirName, $parentIsXBPQDir, $parentIsXYQDir, $parentIsDrpy2Dir) {
    global $XBPQ_DIR_KEYWORDS, $XYQ_DIR_KEYWORDS, $DRPY2_DIR_KEYWORDS;
    
    // 先继承父目录的属性
    $isXBPQDir = $parentIsXBPQDir;
    $isXYQDir = $parentIsXYQDir;
    $isDrpy2Dir = $parentIsDrpy2Dir;
    
    // 如果父目录不是特殊目录，检查当前目录名
    if (!$isXBPQDir) {
        foreach ($XBPQ_DIR_KEYWORDS as $keyword) {
            if (strpos($dirName, $keyword) !== false) {
                $isXBPQDir = true;
                break;
            }
        }
    }
    
    if (!$isXYQDir) {
        foreach ($XYQ_DIR_KEYWORDS as $keyword) {
            if (strpos($dirName, $keyword) !== false) {
                $isXYQDir = true;
                break;
            }
        }
    }
    
    if (!$isDrpy2Dir) {
        foreach ($DRPY2_DIR_KEYWORDS as $keyword) {
            if (strpos($dirName, $keyword) !== false) {
                $isDrpy2Dir = true;
                break;
            }
        }
    }
    
    return [$isXBPQDir, $isXYQDir, $isDrpy2Dir];
}

// 递归扫描目录中的脚本文件（增强版：支持特殊目录属性传递）
function scanScriptFiles($dir, $baseDir = '', $excludeDirs = [], $allowedExtensions = ['php', 'py', 'js', 'wv.js'], $parentIsXBPQDir = false, $parentIsXYQDir = false, $parentIsDrpy2Dir = false) {
    $scriptFiles = [];
    
    if (!is_dir($dir)) {
        return $scriptFiles;
    }
    
    $items = scandir($dir);
    
    // 获取当前目录名
    $currentDirName = basename($dir);
    
    // 检查当前目录是否为特殊目录（继承父目录属性或检查目录名）
    list($isXBPQDir, $isXYQDir, $isDrpy2Dir) = checkSpecialDirectory($currentDirName, $parentIsXBPQDir, $parentIsXYQDir, $parentIsDrpy2Dir);
    
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') {
            continue;
        }
        
        $path = $dir . DIRECTORY_SEPARATOR . $item;
        $relativePath = $baseDir ? $baseDir . '/' . $item : $item;
        
        // 检查当前目录是否在排除列表中
        $shouldExclude = false;
        foreach ($excludeDirs as $excludeDir) {
            // 检查完整路径是否以排除目录开头
            if ($relativePath === $excludeDir || strpos($relativePath, $excludeDir . '/') === 0) {
                $shouldExclude = true;
                break;
            }
        }
        
        if ($shouldExclude) {
            continue; // 跳过排除的目录
        }
        
        if (is_dir($path)) {
            // 递归扫描子目录，传递特殊目录属性
            $subFiles = scanScriptFiles($path, $relativePath, $excludeDirs, $allowedExtensions, $isXBPQDir, $isXYQDir, $isDrpy2Dir);
            $scriptFiles = array_merge($scriptFiles, $subFiles);
        } else {
            // 检查文件扩展名
            $fileExtension = pathinfo($item, PATHINFO_EXTENSION);
            $fileExtensionLower = strtolower($fileExtension);
            
            // 特殊处理.wv.js文件
            if (strtolower(substr($item, -6)) === '.wv.js') {
                $fileExtensionLower = 'wv.js';
            }
            
            if (in_array($fileExtensionLower, $allowedExtensions)) {
                // 添加脚本文件，同时记录目录的特殊属性
                $scriptFiles[] = [
                    'fullPath' => $path,
                    'relativePath' => $relativePath,
                    'filename' => $item,
                    'basename' => pathinfo($item, PATHINFO_FILENAME),
                    'dirname' => dirname($relativePath), // 添加目录信息
                    'extension' => $fileExtensionLower, // 添加扩展名
                    'isXBPQDir' => $isXBPQDir, // 添加是否为XBPQ目录标志
                    'isXYQDir' => $isXYQDir,   // 添加是否为XYQ目录标志
                    'isDrpy2Dir' => $isDrpy2Dir // 添加是否为Drpy2目录标志
                ];
            }
        }
    }
    
    return $scriptFiles;
}

// 扫描当前目录下带有标签的子目录
function scanTagDirectories($baseDir) {
    $tagDirectories = [];
    
    if (!is_dir($baseDir)) {
        return $tagDirectories;
    }
    
    $items = scandir($baseDir);
    
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') {
            continue;
        }
        
        $path = $baseDir . DIRECTORY_SEPARATOR . $item;
        
        if (is_dir($path)) {
            // 检查目录名是否包含标签
            if (strpos($item, '[PHP]') !== false) {
                $tagDirectories[] = [
                    'path' => $path,
                    'name' => $item,
                    'tag' => 'PHP',
                    'dirType' => 'php'  // PHP类型
                ];
            } elseif (strpos($item, '[书]') !== false) {
                $tagDirectories[] = [
                    'path' => $path,
                    'name' => $item,
                    'tag' => '书',
                    'dirType' => 'book'  // 书类型
                ];
            } elseif (strpos($item, '[画]') !== false) {
                $tagDirectories[] = [
                    'path' => $path,
                    'name' => $item,
                    'tag' => '画',
                    'dirType' => 'comic'  // 漫画类型
                ];
            } elseif (strpos($item, '[剧]') !== false) {
                $tagDirectories[] = [
                    'path' => $path,
                    'name' => $item,
                    'tag' => '剧',
                    'dirType' => 'drama'  // 剧类型
                ];
            }
            // +++ 新增 [短剧] 标签支持（独立类型，与 [剧] 区分）+++
            elseif (strpos($item, '[短剧]') !== false) {
                $tagDirectories[] = [
                    'path' => $path,
                    'name' => $item,
                    'tag' => '短剧',
                    'dirType' => 'shortdrama'  // 短剧类型，与 [剧] 分开
                ];
            }
        }
    }
    
    return $tagDirectories;
}

// 移除字符串中的所有方括号标签
function removeAllBracketTags($str) {
    // 移除所有方括号标签，包括方括号本身
    return preg_replace('/\[[^\]]*\]/', '', $str);
}

// 提取直接目录的标签
function extractDirectDirTags($fileInfo) {
    $tags = '';
    
    // 获取文件所在直接目录的名称
    $dirPath = $fileInfo['dirname'];
    if ($dirPath === '.') {
        // 如果是在根目录，则没有标签
        return '';
    }
    
    // 获取直接目录的名称（最后一个目录）
    $directDirName = basename($dirPath);
    
    // 提取直接目录中的所有标签
    preg_match_all('/\[([^\]]+)\]/', $directDirName, $matches);
    
    // 将所有标签组合成一个字符串
    if (!empty($matches[1])) {
        foreach ($matches[1] as $tag) {
            $tags .= '[' . $tag . ']';
        }
    }
    
    return $tags;
}

// 从文件名中提取标签（针对Drpy2目录的特殊逻辑）
function extractTagsFromFileName($fileName) {
    $tags = [];
    $processedName = $fileName;
    
    // 提取所有标签
    if (preg_match_all('/\[([^\]]+)\]/', $fileName, $matches)) {
        $tags = $matches[0]; // 获取所有匹配的标签，包括括号
        // 从文件名中移除所有标签
        foreach ($tags as $tag) {
            $processedName = str_replace($tag, '', $processedName);
        }
    }
    
    return [$tags, $processedName];
}

// 检查目录名是否包含特定标签并返回处理后的标签
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

// 扫描特殊目录（XBPQ、XYQ、Drpy2）
function scanSpecialDirectories($baseDir, $keywords, $type) {
    $specialDirectories = [];
    
    if (!is_dir($baseDir)) {
        return $specialDirectories;
    }
    
    $items = scandir($baseDir);
    
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') {
            continue;
        }
        
        $path = $baseDir . DIRECTORY_SEPARATOR . $item;
        
        if (is_dir($path)) {
            // 检查目录名是否包含关键词
            $isSpecialDir = false;
            foreach ($keywords as $keyword) {
                if (strpos($item, $keyword) !== false) {
                    $isSpecialDir = true;
                    break;
                }
            }
            
            if ($isSpecialDir) {
                $specialDirectories[] = [
                    'path' => $path,
                    'name' => $item,
                    'dirType' => $type  // 'xbpq', 'xyq', 'drpy2'
                ];
            }
        }
    }
    
    return $specialDirectories;
}

// 为特殊目录（XBPQ、XYQ、Drpy2）构建站点配置
function buildSpecialSiteConfig($fileInfo, $specialType, $filteredTag, $baseUrl) {
    global $XBPQ_DIR_KEYWORDS, $XYQ_DIR_KEYWORDS, $DRPY2_DIR_KEYWORDS;
    
    $filename = $fileInfo['basename'];
    $ext = $fileInfo['extension'];
    $relativePath = $fileInfo['relativePath'];
    
    // 从文件名中提取所有标签
    list($tags, $pureName) = extractTagsFromFileName($filename);
    
    // 检查是否包含[书]或[画]标签
    $hasBookTag = in_array('[书]', $tags);
    $hasComicTag = in_array('[画]', $tags);
    
    // 检查文件所在目录是否包含[书]或[画]标签
    $dirPath = $fileInfo['dirname'];
    if ($dirPath !== '.' && $dirPath !== '') {
        $directDirName = basename($dirPath);
        if (strpos($directDirName, '[书]') !== false) {
            $hasBookTag = true;
        }
        if (strpos($directDirName, '[画]') !== false) {
            $hasComicTag = true;
        }
    }
    
    // 根据是否有书画标签决定站点名称格式
    if ($hasBookTag || $hasComicTag) {
        // 有书画标签：原始名称+后缀
        $fullName = $pureName . '(' . strtoupper($ext) . ')';
    } else {
        // 没有书画标签：原始名称+目录标签+后缀
        $fullName = $pureName . $filteredTag . '(' . strtoupper($ext) . ')';
    }
    
    // 根据特殊目录类型设置配置
    if ($specialType === 'xbpq' && $ext === 'json') {
        $config = [
            'key' => $fullName,
            'name' => $fullName,
            'type' => 3,
            'api' => 'csp_XBPQ',
            'jar' => '../lz/lib/XBPQ.jar',
            'searchable' => 1,
            'quickSearch' => 1,
            'filterable' => 1,
            'changeable' => 1,
            'ext' => './' . $relativePath
        ];
        
        // 根据标签设置类型和lang
        if ($hasBookTag) {
            $config['类型'] = '小说';
            $config['lang'] = $ext; // 这里ext是'json'
        } elseif ($hasComicTag) {
            $config['类型'] = '漫画';
            $config['lang'] = $ext;
        }
        
        return $config;
    } elseif ($specialType === 'xyq' && $ext === 'json') {
        $config = [
            'key' => $fullName,
            'name' => $fullName,
            'type' => 3,
            'api' => 'csp_XYQHiker',
            'jar' => '../lz/lib/XYQ.jar',
            'searchable' => 1,
            'quickSearch' => 1,
            'filterable' => 1,
            'changeable' => 1,
            'ext' => './' . $relativePath
        ];
        
        // 根据标签设置类型和lang
        if ($hasBookTag) {
            $config['类型'] = '小说';
            $config['lang'] = $ext; // 这里ext是'json'
        } elseif ($hasComicTag) {
            $config['类型'] = '漫画';
            $config['lang'] = $ext;
        }
        
        return $config;
    } elseif ($specialType === 'drpy2' && $ext === 'js') {
        $config = [
            'key' => $fullName,
            'name' => $fullName,
            'type' => 3,
            'api' => '../lz/lib/lib/drpy2.min.js',
            'searchable' => 1,
            'quickSearch' => 1,
            'filterable' => 1,
            'changeable' => 1,
            'ext' => './' . $relativePath
        ];
        
        // 根据标签设置类型和lang
        if ($hasBookTag) {
            $config['类型'] = '小说';
            $config['lang'] = $ext; // 这里ext是'js'
        } elseif ($hasComicTag) {
            $config['类型'] = '漫画';
            $config['lang'] = $ext;
        }
        
        return $config;
    }
    
    return null;
}

// 排除的文件名列表
$excludeFiles = ['index.php', 'spider.php', 'example_t4.php', 'test_runner.php', 'batch_test.php', 'start.php', 'start.py', 'config.json'];

// 扫描标签目录
$tagDirectories = scanTagDirectories('/storage/emulated/0/lz');
$sites = [];

foreach ($tagDirectories as $tagDir) {
    // 根据目录类型确定要扫描的文件扩展名
    $allowedExtensions = [];
    if ($tagDir['dirType'] === 'php') {
        $allowedExtensions = ['php'];
    } elseif ($tagDir['dirType'] === 'book' || $tagDir['dirType'] === 'comic') {
        $allowedExtensions = ['php', 'py'];
    } elseif ($tagDir['dirType'] === 'drama') {
        $allowedExtensions = ['py', 'js', 'wv.js'];
    }
    // +++ 新增：短剧目录允许扫描 php, py, js, wv.js +++
    elseif ($tagDir['dirType'] === 'shortdrama') {
        $allowedExtensions = ['php', 'py', 'js', 'wv.js'];
    }
    
    // 扫描该标签目录下的脚本文件
    $scriptFiles = scanScriptFiles($tagDir['path'], '', $excludeDirectories, $allowedExtensions, false, false, false);
    
    foreach ($scriptFiles as $fileInfo) {
        // 跳过排除的文件
        if (in_array($fileInfo['filename'], $excludeFiles)) {
            continue;
        }
        
        // 生成站点信息
        $relativeDir = $fileInfo['dirname'];
        if ($relativeDir === '.') {
            $relativeDir = '';
        }
        
        // 生成key：将路径中的斜杠替换为下划线
        $keyPath = str_replace(['/', '\\'], '_', $tagDir['name'] . '_' . $fileInfo['relativePath']);
        $key = pathinfo($keyPath, PATHINFO_FILENAME);
        
        // 生成API路径
        $apiPath = $tagDir['name'];
        if ($relativeDir) {
            $apiPath .= '/' . $relativeDir;
        }
        $apiPath .= '/' . $fileInfo['filename'];
        
        // 生成显示名称（先获取原始名称）
        $displayName = $fileInfo['basename'];
        
        // 根据目录类型和文件扩展名确定基础配置
        $siteConfig = [];
        
        if ($tagDir['dirType'] === 'php') {
            // PHP目录 - 必须是HTTP地址
            $siteConfig = [
                "key"          => $key,
                "name"         => $displayName,  // 默认名称
                "type"         => 4,
                "api"          => $baseUrl . "/" . $apiPath,
                "searchable"   => 1,
                "quickSearch"  => 1,
                "changeable"   => 0
            ];
            
            // 提取直接目录的标签
            $directDirTags = extractDirectDirTags($fileInfo);
            
            // 构建站点名称：清理后的名称 + 直接目录标签
            $cleanDisplayName = removeAllBracketTags($displayName);
            $siteConfig['name'] = $cleanDisplayName . $directDirTags;
            
        } elseif ($tagDir['dirType'] === 'book' || $tagDir['dirType'] === 'comic') {
            // 书或漫画目录
            // 处理目录路径：移除所有方括号标签
            $cleanDisplayName = removeAllBracketTags($displayName);
            
            // 根据文件扩展名添加类型标签
            $typeTag = '';
            if ($fileInfo['extension'] === 'php') {
                $typeTag = '(PHP)';
            } elseif ($fileInfo['extension'] === 'py') {
                $typeTag = '(PY)';
            }
            
            $siteName = $cleanDisplayName . $typeTag;
            
            // 根据文件扩展名设置配置
            if ($fileInfo['extension'] === 'php') {
                // PHP文件使用HTTP地址
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName,
                    "type"         => 4,
                    "api"          => $baseUrl . "/" . $apiPath,
                    "searchable"   => 1,
                    "quickSearch"  => 1,
                    "changeable"   => 0
                ];
            } else {
                // PY文件使用相对路径
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName,
                    "type"         => 3,
                    "api"          => "./" . $apiPath,
                    "searchable"   => 1,
                    "quickSearch"  => 1,
                    "changeable"   => 0
                ];
            }
            
            // 添加类型相关字段
            $siteConfig['title'] = $fileInfo['basename'];
            $siteConfig['类型'] = ($tagDir['dirType'] === 'book') ? '小说' : '漫画';
            $siteConfig['lang'] = $fileInfo['extension'];
            
        } elseif ($tagDir['dirType'] === 'drama') {
            // 剧目录
            // 提取直接目录的标签（与PHP目录相同逻辑）
            $directDirTags = extractDirectDirTags($fileInfo);
            
            // 构建站点名称：清理后的名称 + 直接目录标签 + 文件类型标签
            $cleanDisplayName = removeAllBracketTags($displayName);
            $siteName = $cleanDisplayName . $directDirTags;
            
            // 根据文件扩展名处理
            if ($fileInfo['extension'] === 'wv.js') {
                // .wv.js文件特殊处理
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName . '[剧](WV.JS)',
                    "type"         => 3,
                    "api"          => "csp_WvSpider",
                    "searchable"   => 1,
                    "filterable"   => 1,
                    "switchable"   => 1,
                    "ext"          => "./" . $apiPath,
                    "jar"          => "./lib/WvSpider.jar"
                ];
            } else {
                // .py和.js文件使用相对路径
                $extensionUpper = strtoupper($fileInfo['extension']);
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName . '[剧](' . $extensionUpper . ')',
                    "type"         => 3,
                    "api"          => "./" . $apiPath,
                    "searchable"   => 1,
                    "quickSearch"  => 1,
                    "changeable"   => 1
                ];
            }
        }
        // +++ 新增：短剧目录的处理（区分 PHP 和其他文件）+++
        elseif ($tagDir['dirType'] === 'shortdrama') {
            // 提取直接目录的所有标签，并移除 [短剧] 标签（因为名称中不应包含主类型标签）
            $directDirTags = extractDirectDirTags($fileInfo);
            $directDirTags = str_replace('[短剧]', '', $directDirTags);
            
            // 移除文件名中的所有标签
            $cleanDisplayName = removeAllBracketTags($displayName);
            
            // 根据文件扩展名添加后缀括号
            $extensionUpper = strtoupper($fileInfo['extension']);
            $siteName = $cleanDisplayName . $directDirTags . '(' . $extensionUpper . ')';
            
            // 根据文件扩展名设置配置
            if ($fileInfo['extension'] === 'php') {
                // PHP 文件使用 HTTP 地址
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName,
                    "type"         => 4,
                    "api"          => $baseUrl . "/" . $apiPath,
                    "searchable"   => 1,
                    "quickSearch"  => 1,
                    "changeable"   => 0
                ];
            } elseif ($fileInfo['extension'] === 'wv.js') {
                // .wv.js 文件使用 WvSpider
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName,
                    "type"         => 3,
                    "api"          => "csp_WvSpider",
                    "searchable"   => 1,
                    "filterable"   => 1,
                    "switchable"   => 1,
                    "ext"          => "./" . $apiPath,
                    "jar"          => "./lib/WvSpider.jar"
                ];
            } else {
                // py, js 等文件使用相对路径
                $siteConfig = [
                    "key"          => $key,
                    "name"         => $siteName,
                    "type"         => 3,
                    "api"          => "./" . $apiPath,
                    "searchable"   => 1,
                    "quickSearch"  => 1,
                    "changeable"   => 1
                ];
            }
            
            // 添加短剧类型标识
            $siteConfig['类型'] = '短剧';
            $siteConfig['lang'] = $fileInfo['extension'];
        }
        
        $sites[] = $siteConfig;
    }
}

// ==================
// 新增：扫描特殊目录（XBPQ、XYQ、Drpy2）
// ==================

// 扫描XBPQ目录
$xbpqDirectories = scanSpecialDirectories('/storage/emulated/0/lz', $XBPQ_DIR_KEYWORDS, 'xbpq');
foreach ($xbpqDirectories as $specialDir) {
    // 检查目录类型并获取过滤后的标签
    list($filteredTag, $dirType) = checkDirTypeAndFilterTag($specialDir['name']);
    
    // 扫描XBPQ目录下的所有文件（递归），注意这里传入目录名作为基路径
    // 使用增强版的scanScriptFiles函数，传递特殊目录属性
    $allFiles = scanScriptFiles($specialDir['path'], $specialDir['name'], $excludeDirectories, ['json', 'js', 'php', 'py', 'wv.js'], false, false, false);
    
    foreach ($allFiles as $fileInfo) {
        // 跳过排除的文件
        if (in_array($fileInfo['filename'], $excludeFiles)) {
            continue;
        }
        
        // 只处理json文件（XBPQ目录只处理json）
        if ($fileInfo['extension'] !== 'json') {
            continue;
        }
        
        // 检查文件是否在XBPQ目录下（通过文件信息中的isXBPQDir标志）
        if (!$fileInfo['isXBPQDir']) {
            continue;
        }
        
        // 为XBPQ目录构建站点配置
        $siteConfig = buildSpecialSiteConfig($fileInfo, 'xbpq', $filteredTag, $baseUrl);
        if ($siteConfig) {
            $sites[] = $siteConfig;
        }
    }
}

// 扫描XYQ目录
$xyqDirectories = scanSpecialDirectories('/storage/emulated/0/lz', $XYQ_DIR_KEYWORDS, 'xyq');
foreach ($xyqDirectories as $specialDir) {
    // 检查目录类型并获取过滤后的标签
    list($filteredTag, $dirType) = checkDirTypeAndFilterTag($specialDir['name']);
    
    // 扫描XYQ目录下的所有文件（递归），注意这里传入目录名作为基路径
    // 使用增强版的scanScriptFiles函数，传递特殊目录属性
    $allFiles = scanScriptFiles($specialDir['path'], $specialDir['name'], $excludeDirectories, ['json', 'js', 'php', 'py', 'wv.js'], false, false, false);
    
    foreach ($allFiles as $fileInfo) {
        // 跳过排除的文件
        if (in_array($fileInfo['filename'], $excludeFiles)) {
            continue;
        }
        
        // 只处理json文件（XYQ目录只处理json）
        if ($fileInfo['extension'] !== 'json') {
            continue;
        }
        
        // 检查文件是否在XYQ目录下（通过文件信息中的isXYQDir标志）
        if (!$fileInfo['isXYQDir']) {
            continue;
        }
        
        // 为XYQ目录构建站点配置
        $siteConfig = buildSpecialSiteConfig($fileInfo, 'xyq', $filteredTag, $baseUrl);
        if ($siteConfig) {
            $sites[] = $siteConfig;
        }
    }
}

// 扫描Drpy2目录
$drpy2Directories = scanSpecialDirectories('/storage/emulated/0/lz', $DRPY2_DIR_KEYWORDS, 'drpy2');
foreach ($drpy2Directories as $specialDir) {
    // 检查目录类型并获取过滤后的标签
    list($filteredTag, $dirType) = checkDirTypeAndFilterTag($specialDir['name']);
    
    // 扫描Drpy2目录下的所有文件（递归），注意这里传入目录名作为基路径
    // 使用增强版的scanScriptFiles函数，传递特殊目录属性
    $allFiles = scanScriptFiles($specialDir['path'], $specialDir['name'], $excludeDirectories, ['json', 'js', 'php', 'py', 'wv.js'], false, false, false);
    
    foreach ($allFiles as $fileInfo) {
        // 跳过排除的文件
        if (in_array($fileInfo['filename'], $excludeFiles)) {
            continue;
        }
        
        // 只处理js文件（Drpy2目录只处理js）
        if ($fileInfo['extension'] !== 'js') {
            continue;
        }
        
        // 检查文件是否在Drpy2目录下（通过文件信息中的isDrpy2Dir标志）
        if (!$fileInfo['isDrpy2Dir']) {
            continue;
        }
        
        // 为Drpy2目录构建站点配置
        $siteConfig = buildSpecialSiteConfig($fileInfo, 'drpy2', $filteredTag, $baseUrl);
        if ($siteConfig) {
            $sites[] = $siteConfig;
        }
    }
}

// ==================
// 2. 尝试加载 ../drpy-node/index.json
// ==================
$indexJsonPath = realpath(__DIR__ . '/../drpy-node/index.json');

if ($indexJsonPath && is_file($indexJsonPath)) {
    $content = file_get_contents($indexJsonPath);
    $json = json_decode($content, true);

    // JSON 合法并且是数组
    if (is_array($json)) {
        // 替换 sites
        $json['sites'] = $sites;

        echo json_encode(
            $json,
            JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT
        );
        exit;
    }
}

// ==================
// 3. 找不到或失败，回退只返回 sites
// ==================
echo json_encode(
    ["sites" => $sites],
    JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT
);
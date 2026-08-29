<?php
/**
 * TVBox PHP 爬虫脚本 - 四合一综合版
 * 支持本地文件(JSON/TXT/M3U/DB) + 苹果视频 + 金牌影视
 * 按类型分类归拢显示，12宫格布局，PHP管理置顶
 */

ini_set('memory_limit', '1024M');
// 获取请求参数
$ac = $_GET['ac'] ?? 'detail';
$t = $_GET['t'] ?? '';
$pg = $_GET['pg'] ?? '1';
$ids = $_GET['ids'] ?? '';
$wd = $_GET['wd'] ?? '';
$flag = $_GET['flag'] ?? '';
$id = $_GET['id'] ?? '';
$source = $_GET['source'] ?? 'local'; // 新增：数据源选择

// 设置响应头为 JSON
header('Content-Type: application/json; charset=utf-8');

// 性能优化 - 增加超时时间
@set_time_limit(30);

// 根据不同 action 和数据源返回数据
switch ($ac) {
    case 'detail':
        if ($source === 'apple') {
            echo json_encode(getAppleDetail($ids), JSON_UNESCAPED_UNICODE);
        } elseif ($source === 'jinpai') {
            echo json_encode(getJinPaiDetail($ids), JSON_UNESCAPED_UNICODE);
        } else {
            if (!empty($ids)) {
                echo json_encode(getDetail($ids), JSON_UNESCAPED_UNICODE);
            } elseif (!empty($t)) {
                echo json_encode(getCategory($t, $pg), JSON_UNESCAPED_UNICODE);
            } else {
                echo json_encode(getHome(), JSON_UNESCAPED_UNICODE);
            }
        }
        break;
    
    case 'search':
        if ($source === 'apple') {
            echo json_encode(searchApple($wd, $pg), JSON_UNESCAPED_UNICODE);
        } elseif ($source === 'jinpai') {
            echo json_encode(searchJinPai($wd, $pg), JSON_UNESCAPED_UNICODE);
        } else {
            echo json_encode(search($wd, $pg), JSON_UNESCAPED_UNICODE);
        }
        break;
        
    case 'play':
        if ($source === 'apple') {
            echo json_encode(getApplePlay($flag, $id), JSON_UNESCAPED_UNICODE);
        } elseif ($source === 'jinpai') {
            echo json_encode(getJinPaiPlay($flag, $id), JSON_UNESCAPED_UNICODE);
        } else {
            echo json_encode(getPlay($flag, $id), JSON_UNESCAPED_UNICODE);
        }
        break;

    case 'home':
        if ($source === 'apple') {
            echo json_encode(getAppleHome(), JSON_UNESCAPED_UNICODE);
        } elseif ($source === 'jinpai') {
            echo json_encode(getJinPaiHome(), JSON_UNESCAPED_UNICODE);
        } else {
            echo json_encode(getHome(), JSON_UNESCAPED_UNICODE);
        }
        break;
    
    default:
        echo json_encode(['error' => '未知操作: ' . $ac], JSON_UNESCAPED_UNICODE);
}

// ============================================================================
// 本地文件处理函数 (原四合一功能)
// ============================================================================

/**
 * 获取默认预览图列表
 */
function getDefaultImages() {
    return [
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2874266060.jpg',
        'https://img1.doubanio.com/view/photo/m_ratio_poster/public/p2881321835.jpg',
        'https://img2.doubanio.com/view/photo/m_ratio_poster/public/p2881321836.jpg',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2881321837.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2881321838.jpg',
        'https://img1.doubanio.com/view/photo/m_ratio_poster/public/p2881321839.jpg',
        'https://img2.doubanio.com/view/photo/m_ratio_poster/public/p2881321840.jpg',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2881321841.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2881321842.jpg'
    ];
}

/**
 * 获取随机预览图
 */
function getRandomImage($seed = null) {
    $images = getDefaultImages();
    if ($seed !== null) {
        return $images[abs(crc32($seed)) % count($images)];
    }
    return $images[array_rand($images)];
}

/**
 * 递归扫描目录 - 支持无限级子文件夹
 */
function scanDirectoryRecursive($dir, $types, $currentDepth = 0, $maxDepth = 20) {
    $files = [];
    
    if (!is_dir($dir) || $currentDepth > $maxDepth) {
        return $files;
    }
    
    $items = @scandir($dir);
    if ($items === false) return $files;
    
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') continue;
        
        $path = $dir . $item;
        
        if (is_dir($path)) {
            $subFiles = scanDirectoryRecursive($path . '/', $types, $currentDepth + 1, $maxDepth);
            $files = array_merge($files, $subFiles);
        } else {
            $extension = strtolower(pathinfo($path, PATHINFO_EXTENSION));
            if (in_array($extension, $types)) {
                $relativePath = str_replace('/storage/emulated/0/江湖/', '', $path);
                
                $files[] = [
                    'type' => $extension,
                    'path' => $path,
                    'name' => $item,
                    'filename' => pathinfo($item, PATHINFO_FILENAME),
                    'relative_path' => $relativePath,
                    'depth' => $currentDepth
                ];
            }
        }
    }
    
    return $files;
}

/**
 * 获取所有文件列表 - 移除多媒体文件支持
 */
function getAllFiles() {
    static $allFiles = null;
    
    if ($allFiles === null) {
        $allFiles = [];
        
        $jsonFiles = scanDirectoryRecursive('/storage/emulated/0/江湖/json/影视/', ['json']);
        $txtFiles = scanDirectoryRecursive('/storage/emulated/0/江湖/wj/', ['txt']);
        $m3uFiles = array_merge(
            scanDirectoryRecursive('/storage/emulated/0/江湖/json/影视/', ['m3u']),
            scanDirectoryRecursive('/storage/emulated/0/江湖/wj/', ['m3u'])
        );
        // 添加.db文件扫描
        $dbFiles = array_merge(
            scanDirectoryRecursive('/storage/emulated/0/江湖/json/影视/', ['db']),
            scanDirectoryRecursive('/storage/emulated/0/江湖/wj/', ['db']),
            scanDirectoryRecursive('/storage/emulated/0/江湖/db/', ['db']) // 新增专门目录
        );
        
        // 移除多媒体文件扫描
        
        $allFiles = array_merge($jsonFiles, $txtFiles, $m3uFiles, $dbFiles);
        
        usort($allFiles, function($a, $b) {
            return strcmp($a['relative_path'], $b['relative_path']);
        });
    }
    
    return $allFiles;
}

/**
 * 估算文件中的视频数量（快速估算，不实际解析）
 */
function estimateFileVideoCount($file) {
    $path = $file['path'];
    $type = $file['type'];
    
    if (!file_exists($path)) {
        return 0;
    }
    
    $fileSize = filesize($path);
    
    // 根据文件类型和大小快速估算
    switch ($type) {
        case 'json':
            // JSON文件：假设平均每个视频占用1KB
            return $fileSize > 1024 ? intval($fileSize / 1024) : 1;
            
        case 'txt':
            // TXT文件：按行数估算（假设平均每行100字节）
            $lineCount = $fileSize > 100 ? intval($fileSize / 100) : 1;
            return min($lineCount, 10000);
            
        case 'm3u':
            // M3U文件：每2行一个视频
            $lineCount = $fileSize > 200 ? intval($fileSize / 200) : 1;
            return min($lineCount, 5000);
            
        case 'db':
            // DB文件：根据大小估算，假设平均每个视频记录占用500字节
            return $fileSize > 500 ? intval($fileSize / 500) : 1;
            
        default:
            return 0;
    }
}

/**
 * 获取分类列表 - 按类型归拢显示
 */
function getCategories() {
    static $categories = null;
    
    if ($categories === null) {
        $allFiles = getAllFiles();
        $categories = [];
        
        // PHP管理置顶分类
        $categories[] = [
            'type_id' => 'php_admin',
            'type_name' => '🚀 PHP管理面板',
            'type_file' => 'php_admin',
            'source_path' => 'php_admin',
            'source_type' => 'php_admin'
        ];
        
        // 新增热门推荐分类
        $totalFiles = count($allFiles);
        $categories[] = [
            'type_id' => 'hot',
            'type_name' => '🔥 热门推荐 (' . $totalFiles . '个文件)',
            'type_file' => 'hot_recommend',
            'source_path' => 'hot',
            'source_type' => 'hot'
        ];
        
        // 按文件类型归拢分类
        $fileTypes = [
            'json' => ['icon' => '📊', 'name' => 'JSON资源'],
            'txt' => ['icon' => '📄', 'name' => 'TXT资源'], 
            'm3u' => ['icon' => '📺', 'name' => 'M3U直播'],
            'db' => ['icon' => '🗃️', 'name' => '数据库资源']
        ];
        
        foreach ($fileTypes as $fileType => $typeInfo) {
            $typeFiles = array_filter($allFiles, function($file) use ($fileType) {
                return $file['type'] === $fileType;
            });
            
            if (!empty($typeFiles)) {
                $totalVideos = 0;
                foreach ($typeFiles as $file) {
                    $totalVideos += estimateFileVideoCount($file);
                }
                
                $categories[] = [
                    'type_id' => 'local_' . $fileType,
                    'type_name' => $typeInfo['icon'] . ' ' . $typeInfo['name'] . ' (' . count($typeFiles) . '个文件, ' . number_format($totalVideos) . '个视频)',
                    'type_file' => $fileType . '_collection',
                    'source_path' => $fileType,
                    'source_type' => 'collection'
                ];
            }
        }
        
        // 新增外部数据源分类 - 显示网站名称
        $categories[] = [
            'type_id' => 'apple',
            'type_name' => '🍎 苹果视频 (618041.xyz)',
            'type_file' => 'apple_video',
            'source_path' => 'apple',
            'source_type' => 'external'
        ];
        
        $categories[] = [
            'type_id' => 'jinpai',
            'type_name' => '🥇 金牌影视 (hkybqufgh.com)',
            'type_file' => 'jinpai_video',
            'source_path' => 'jinpai',
            'source_type' => 'external'
        ];
        
        if (empty($allFiles)) {
            $categories[] = [
                'type_id' => '1',
                'type_name' => '❓ 未找到媒体文件',
                'type_file' => 'empty',
                'source_path' => 'empty',
                'source_type' => 'empty'
            ];
        }
    }
    
    return $categories;
}

/**
 * 解析SQLite数据库文件内容
 */
function parseDbFile($filePath) {
    if (!file_exists($filePath)) {
        return ['error' => '数据库文件不存在: ' . $filePath];
    }
    
    // 文件大小检查（1024M）
    $fileSize = filesize($filePath);
    if ($fileSize > 1024 * 1024 * 1024) {
        return ['error' => '数据库文件过大: ' . round($fileSize / (1024 * 1024), 2) . 'MB'];
    }
    
    // 检查SQLite扩展
    if (!extension_loaded('pdo_sqlite')) {
        return ['error' => 'PDO_SQLite扩展不可用，无法读取数据库文件'];
    }
    
    try {
        // 创建数据库连接
        $db = new PDO("sqlite:" . $filePath);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        
        $videos = [];
        
        // 尝试检测表结构并读取数据
        $tables = $db->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(PDO::FETCH_COLUMN);
        
        if (empty($tables)) {
            return ['error' => '数据库中未找到任何数据表'];
        }
        
        $defaultImages = getDefaultImages();
        
        foreach ($tables as $table) {
            // 跳过系统表
            if (strpos($table, 'sqlite_') === 0) continue;
            
            // 获取表结构
            $columns = $db->query("PRAGMA table_info($table)")->fetchAll(PDO::FETCH_ASSOC);
            $columnNames = array_column($columns, 'name');
            
            // 查找可能的视频字段
            $nameColumn = null;
            $urlColumn = null;
            $picColumn = null;
            $descColumn = null;
            $yearColumn = null;
            $areaColumn = null;
            
            foreach ($columnNames as $col) {
                $lowerCol = strtolower($col);
                if (in_array($lowerCol, ['name', 'title', 'vod_name', 'filename', 'video_name'])) {
                    $nameColumn = $col;
                } elseif (in_array($lowerCol, ['url', 'link', 'vod_url', 'play_url', 'video_url'])) {
                    $urlColumn = $col;
                } elseif (in_array($lowerCol, ['pic', 'image', 'cover', 'vod_pic', 'poster'])) {
                    $picColumn = $col;
                } elseif (in_array($lowerCol, ['desc', 'description', 'content', 'vod_content'])) {
                    $descColumn = $col;
                } elseif (in_array($lowerCol, ['year', 'vod_year'])) {
                    $yearColumn = $col;
                } elseif (in_array($lowerCol, ['area', 'region', 'vod_area'])) {
                    $areaColumn = $col;
                }
            }
            
            // 如果有名称和URL字段，则读取数据
            if ($nameColumn && $urlColumn) {
                $selectColumns = [$nameColumn, $urlColumn];
                if ($picColumn) $selectColumns[] = $picColumn;
                if ($descColumn) $selectColumns[] = $descColumn;
                if ($yearColumn) $selectColumns[] = $yearColumn;
                if ($areaColumn) $selectColumns[] = $areaColumn;
                
                $selectSql = "SELECT " . implode(', ', $selectColumns) . " FROM $table";
                
                $stmt = $db->query($selectSql);
                $results = $stmt->fetchAll(PDO::FETCH_ASSOC);
                
                foreach ($results as $index => $row) {
                    $videoName = $row[$nameColumn] ?? '未知视频';
                    $videoUrl = $row[$urlColumn] ?? '';
                    $videoPic = $row[$picColumn] ?? $defaultImages[$index % count($defaultImages)];
                    $videoDesc = $row[$descColumn] ?? '《' . $videoName . '》的精彩内容';
                    $videoYear = $row[$yearColumn] ?? date('Y');
                    $videoArea = $row[$areaColumn] ?? '中国大陆';
                    
                    // 验证URL有效性
                    $validProtocols = ['http://', 'https://', 'rtmp://', 'rtsp://', 'udp://'];
                    $hasValidProtocol = false;
                    foreach ($validProtocols as $protocol) {
                        if (stripos($videoUrl, $protocol) === 0) {
                            $hasValidProtocol = true;
                            break;
                        }
                    }
                    
                    if (!$hasValidProtocol) continue;
                    
                    $videos[] = [
                        'vod_id' => 'db_' . md5($filePath) . '_' . $table . '_' . $index,
                        'vod_name' => $videoName,
                        'vod_pic' => $videoPic,
                        'vod_remarks' => '高清',
                        'vod_year' => $videoYear,
                        'vod_area' => $videoArea,
                        'vod_content' => $videoDesc,
                        'vod_play_from' => '数据库源',
                        'vod_play_url' => '正片$' . $videoUrl
                    ];
                    
                    // 内存保护
                    if (count($videos) >= 1000) break 2;
                }
            }
        }
        
        $db = null; // 关闭连接
        
        return $videos;
        
    } catch (PDOException $e) {
        return ['error' => '数据库读取失败: ' . $e->getMessage()];
    }
}

/**
 * 解析JSON文件内容 - 完整加载
 */
function parseJsonFile($filePath) {
    if (!file_exists($filePath)) {
        return ['error' => 'JSON文件不存在: ' . $filePath];
    }
    
    // 文件大小检查（1024M）
    $fileSize = filesize($filePath);
    if ($fileSize > 1024 * 1024 * 1024) {
        return ['error' => 'JSON文件过大: ' . round($fileSize / (1024 * 1024), 2) . 'MB'];
    }
    
    $jsonContent = @file_get_contents($filePath);
    if ($jsonContent === false) {
        return ['error' => '无法读取JSON文件: ' . $filePath];
    }
    
    // 处理BOM头
    if (substr($jsonContent, 0, 3) == "\xEF\xBB\xBF") {
        $jsonContent = substr($jsonContent, 3);
    }
    
    $data = json_decode($jsonContent, true);
    if (!$data || !isset($data['list']) || !is_array($data['list'])) {
        return ['error' => 'JSON格式无效或缺少list字段: ' . $filePath];
    }
    
    // 确保每个视频都有预览图
    $defaultImages = getDefaultImages();
    foreach ($data['list'] as &$video) {
        if (empty($video['vod_pic'])) {
            $video['vod_pic'] = getRandomImage($video['vod_id'] ?? $video['vod_name']);
        }
    }
    
    return $data['list'];
}

/**
 * 解析TXT文件内容 - 流式处理（支持大文件）
 */
function parseTxtFile($filePath) {
    if (!file_exists($filePath)) {
        return ['error' => 'TXT文件不存在: ' . $filePath];
    }
    
    // 文件大小检查（1024M）
    $fileSize = filesize($filePath);
    if ($fileSize > 1024 * 1024 * 1024) {
        return ['error' => 'TXT文件过大: ' . round($fileSize / (1024 * 1024), 2) . 'MB'];
    }
    
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return ['error' => '无法打开TXT文件: ' . $filePath];
    }
    
    $videos = [];
    $videoCount = 0;
    $lineNumber = 0;
    
    $defaultImages = getDefaultImages();
    
    // 检测BOM头
    $firstLine = fgets($handle);
    rewind($handle);
    $hasBom = (substr($firstLine, 0, 3) == "\xEF\xBB\xBF");
    if ($hasBom) {
        fseek($handle, 3);
    }
    
    $memoryLimit = 1024 * 1024 * 1024; // 1024M
    $startMemory = memory_get_usage();
    
    while (($line = fgets($handle)) !== false) {
        $lineNumber++;
        $line = trim($line);
        
        if ($line === '' || $line[0] === '#' || $line[0] === ';') continue;
        
        $separators = [',', "\t", '|', '$', '#'];
        $separatorPos = false;
        
        foreach ($separators as $sep) {
            $pos = strpos($line, $sep);
            if ($pos !== false) {
                $separatorPos = $pos;
                break;
            }
        }
        
        if ($separatorPos === false) continue;
        
        $name = trim(substr($line, 0, $separatorPos));
        $url = trim(substr($line, $separatorPos + 1));
        
        if (empty($name) || empty($url)) continue;
        
        $validProtocols = ['http://', 'https://', 'rtmp://', 'rtsp://', 'udp://'];
        $hasValidProtocol = false;
        foreach ($validProtocols as $protocol) {
            if (stripos($url, $protocol) === 0) {
                $hasValidProtocol = true;
                break;
            }
        }
        
        if (!$hasValidProtocol) continue;
        
        $imageIndex = $videoCount % count($defaultImages);
        
        $videos[] = [
            'vod_id' => 'txt_' . md5($filePath) . '_' . $lineNumber,
            'vod_name' => $name,
            'vod_pic' => $defaultImages[$imageIndex],
            'vod_remarks' => '高清',
            'vod_year' => date('Y'),
            'vod_area' => '中国大陆',
            'vod_content' => '《' . $name . '》的精彩内容',
            'vod_play_from' => '在线播放',
            'vod_play_url' => '正片$' . $url
        ];
        
        $videoCount++;
        
        // 内存保护
        if ($videoCount % 100 === 0) {
            $currentMemory = memory_get_usage() - $startMemory;
            if ($currentMemory > $memoryLimit) break;
            gc_collect_cycles();
        }
        
        if ($videoCount >= 10000) break;
    }
    
    fclose($handle);
    return $videos;
}

/**
 * 解析M3U文件内容 - 流式处理（支持大文件）
 */
function parseM3uFile($filePath) {
    if (!file_exists($filePath)) {
        return ['error' => 'M3U文件不存在: ' . $filePath];
    }
    
    // 文件大小检查（1024M）
    $fileSize = filesize($filePath);
    if ($fileSize > 1024 * 1024 * 1024) {
        return ['error' => 'M3U文件过大: ' . round($fileSize / (1024 * 1024), 2) . 'MB'];
    }
    
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return ['error' => '无法打开M3U文件: ' . $filePath];
    }
    
    $videos = [];
    $videoCount = 0;
    $currentName = '';
    $currentLogo = '';
    $currentGroup = '';
    
    $defaultImages = getDefaultImages();
    
    // 检测BOM头
    $firstLine = fgets($handle);
    rewind($handle);
    $hasBom = (substr($firstLine, 0, 3) == "\xEF\xBB\xBF");
    if ($hasBom) {
        fseek($handle, 3);
    }
    
    while (($line = fgets($handle)) !== false) {
        $line = trim($line);
        if ($line === '') continue;
        
        if (strpos($line, '#EXTM3U') === 0) continue;
        
        if (strpos($line, '#EXTINF:') === 0) {
            $currentName = '';
            $currentLogo = '';
            $currentGroup = '';
            
            $parts = explode(',', $line, 2);
            if (count($parts) > 1) {
                $currentName = trim($parts[1]);
            }
            
            if (preg_match('/tvg-logo="([^"]*)"/i', $line, $logoMatches)) {
                $currentLogo = trim($logoMatches[1]);
            }
            
            if (preg_match('/group-title="([^"]*)"/i', $line, $groupMatches)) {
                $currentGroup = trim($groupMatches[1]);
            }
            
            continue;
        }
        
        if ((strpos($line, 'http') === 0 || strpos($line, 'rtmp') === 0 || 
             strpos($line, 'rtsp') === 0 || strpos($line, 'udp') === 0) && 
            !empty($currentName)) {
            
            $imageIndex = $videoCount % count($defaultImages);
            
            $vodPic = $currentLogo;
            if (empty($vodPic) || !filter_var($vodPic, FILTER_VALIDATE_URL)) {
                $vodPic = $defaultImages[$imageIndex];
            }
            
            $playFrom = '直播源';
            if (!empty($currentGroup)) {
                $playFrom = $currentGroup;
            }
            
            $videos[] = [
                'vod_id' => 'm3u_' . md5($filePath) . '_' . $videoCount,
                'vod_name' => $currentName,
                'vod_pic' => $vodPic,
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $currentName . '直播频道',
                'vod_play_from' => $playFrom,
                'vod_play_url' => '直播$' . $line
            ];
            
            $videoCount++;
            $currentName = '';
            $currentLogo = '';
            $currentGroup = '';
            
            if ($videoCount >= 5000) break;
        }
    }
    
    fclose($handle);
    return $videos;
}

/**
 * 格式化文件大小
 */
function formatFileSize($bytes) {
    if ($bytes >= 1073741824) {
        return number_format($bytes / 1073741824, 2) . ' GB';
    } elseif ($bytes >= 1048576) {
        return number_format($bytes / 1048576, 2) . ' MB';
    } elseif ($bytes >= 1024) {
        return number_format($bytes / 1024, 2) . ' KB';
    } else {
        return $bytes . ' B';
    }
}

/**
 * 获取热门推荐视频 - 从所有分类中随机获取
 */
function getHotVideos($page, $pageSize = 12) { // 改为12宫格
    static $allHotVideos = null;
    static $usedVideoIds = [];
    
    // 如果是第一页，重新生成随机视频
    if ($page == 1) {
        $usedVideoIds = [];
    }
    
    // 收集所有文件的视频
    if ($allHotVideos === null) {
        $allHotVideos = [];
        $allFiles = getAllFiles();
        
        foreach ($allFiles as $file) {
            if (!file_exists($file['path'])) continue;
            
            $videos = [];
            switch ($file['type']) {
                case 'json':
                    $videos = parseJsonFile($file['path']);
                    break;
                case 'txt':
                    $videos = parseTxtFile($file['path']);
                    break;
                case 'm3u':
                    $videos = parseM3uFile($file['path']);
                    break;
                case 'db':
                    $videos = parseDbFile($file['path']);
                    break;
            }
            
            // 如果是错误信息，跳过
            if (isset($videos['error'])) {
                continue;
            }
            
            // 限制每个文件的视频数量，避免内存问题
            if (count($videos) > 100) {
                $videos = array_slice($videos, 0, 100);
            }
            
            $allHotVideos = array_merge($allHotVideos, $videos);
            
            // 内存保护
            if (count($allHotVideos) > 1000) {
                break;
            }
        }
    }
    
    if (empty($allHotVideos)) {
        return [];
    }
    
    // 过滤掉已经使用过的视频
    $availableVideos = [];
    foreach ($allHotVideos as $video) {
        $videoId = $video['vod_id'] ?? '';
        if (!in_array($videoId, $usedVideoIds)) {
            $availableVideos[] = $video;
        }
    }
    
    // 如果可用视频不足，重新开始（实现无限翻页）
    if (empty($availableVideos)) {
        $usedVideoIds = [];
        $availableVideos = $allHotVideos;
    }
    
    // 随机选择视频
    $selectedVideos = [];
    $neededCount = min($pageSize, count($availableVideos));
    
    if ($neededCount > 0) {
        $randomKeys = array_rand($availableVideos, $neededCount);
        if (!is_array($randomKeys)) {
            $randomKeys = [$randomKeys];
        }
        
        foreach ($randomKeys as $key) {
            $selectedVideo = $availableVideos[$key];
            $selectedVideos[] = $selectedVideo;
            $usedVideoIds[] = $selectedVideo['vod_id'] ?? '';
        }
    }
    
    return $selectedVideos;
}

/**
 * 首页数据
 */
function getHome() {
    $categories = getCategories();
    
    if (empty($categories)) {
        return ['error' => '未找到任何文件'];
    }
    
    return [
        'class' => $categories
    ];
}

/**
 * 分类列表 - 12宫格显示
 */
function getCategory($tid, $pg) {
    $categories = getCategories();
    
    if (empty($categories)) {
        return ['error' => '未找到任何分类'];
    }
    
    // PHP管理面板
    if ($tid === 'php_admin') {
        return [
            'page' => 1,
            'pagecount' => 1,
            'limit' => 12,
            'total' => 0,
            'list' => [
                [
                    'vod_id' => 'php_info',
                    'vod_name' => 'PHP信息',
                    'vod_pic' => getRandomImage('php_info'),
                    'vod_remarks' => '系统信息',
                    'vod_year' => date('Y'),
                    'vod_area' => '系统'
                ],
                [
                    'vod_id' => 'file_manager',
                    'vod_name' => '文件管理',
                    'vod_pic' => getRandomImage('file_manager'),
                    'vod_remarks' => '文件操作',
                    'vod_year' => date('Y'),
                    'vod_area' => '系统'
                ],
                [
                    'vod_id' => 'system_status',
                    'vod_name' => '系统状态',
                    'vod_pic' => getRandomImage('system_status'),
                    'vod_remarks' => '运行状态',
                    'vod_year' => date('Y'),
                    'vod_area' => '系统'
                ]
            ]
        ];
    }
    
    // 热门推荐分类处理
    if ($tid === 'hot') {
        $currentPage = intval($pg);
        if ($currentPage < 1) $currentPage = 1;
        
        $hotVideos = getHotVideos($currentPage, 12); // 12宫格
        
        if (empty($hotVideos)) {
            return [
                'page' => $currentPage,
                'pagecount' => 9999, // 支持无限翻页
                'limit' => 12,
                'total' => 0,
                'list' => []
            ];
        }
        
        $formattedVideos = [];
        foreach ($hotVideos as $video) {
            $formattedVideos[] = formatVideoItem($video);
        }
        
        return [
            'page' => $currentPage,
            'pagecount' => 9999, // 支持无限翻页
            'limit' => 12,
            'total' => 999999, // 大数字表示无限内容
            'list' => $formattedVideos
        ];
    }
    
    // 外部数据源处理
    if ($tid === 'apple') {
        return getAppleCategory($pg);
    }
    
    if ($tid === 'jinpai') {
        return getJinPaiCategory($pg);
    }
    
    // 本地文件类型归拢处理
    if (strpos($tid, 'local_') === 0) {
        $fileType = str_replace('local_', '', $tid);
        $allFiles = getAllFiles();
        
        // 过滤指定类型的文件
        $typeFiles = array_filter($allFiles, function($file) use ($fileType) {
            return $file['type'] === $fileType;
        });
        
        if (empty($typeFiles)) {
            return [
                'page' => 1,
                'pagecount' => 1,
                'limit' => 12,
                'total' => 0,
                'list' => []
            ];
        }
        
        // 合并所有该类型文件的视频
        $allVideos = [];
        foreach ($typeFiles as $file) {
            if (!file_exists($file['path'])) continue;
            
            $videos = [];
            switch ($file['type']) {
                case 'json':
                    $videos = parseJsonFile($file['path']);
                    break;
                case 'txt':
                    $videos = parseTxtFile($file['path']);
                    break;
                case 'm3u':
                    $videos = parseM3uFile($file['path']);
                    break;
                case 'db':
                    $videos = parseDbFile($file['path']);
                    break;
            }
            
            // 跳过错误结果
            if (isset($videos['error'])) {
                continue;
            }
            
            $allVideos = array_merge($allVideos, $videos);
            
            // 内存保护
            if (count($allVideos) > 1000) {
                break;
            }
        }
        
        if (empty($allVideos)) {
            return [
                'page' => 1,
                'pagecount' => 1,
                'limit' => 12,
                'total' => 0,
                'list' => []
            ];
        }
        
        // 分页处理 - 12宫格
        $pageSize = 12;
        $total = count($allVideos);
        $pageCount = ceil($total / $pageSize);
        $currentPage = intval($pg);
        
        if ($currentPage < 1) $currentPage = 1;
        if ($currentPage > $pageCount) $currentPage = $pageCount;
        
        $start = ($currentPage - 1) * $pageSize;
        $pagedVideos = array_slice($allVideos, $start, $pageSize);
        
        $formattedVideos = [];
        foreach ($pagedVideos as $video) {
            $formattedVideos[] = formatVideoItem($video);
        }
        
        return [
            'page' => $currentPage,
            'pagecount' => $pageCount,
            'limit' => $pageSize,
            'total' => $total,
            'list' => $formattedVideos
        ];
    }
    
    return ['error' => '分类未找到: ' . $tid];
}

/**
 * 格式化视频项
 */
function formatVideoItem($video) {
    return [
        'vod_id' => $video['vod_id'] ?? '',
        'vod_name' => $video['vod_name'] ?? '未知视频',
        'vod_pic' => $video['vod_pic'] ?? getRandomImage($video['vod_id'] ?? $video['vod_name']),
        'vod_remarks' => $video['vod_remarks'] ?? '高清',
        'vod_year' => $video['vod_year'] ?? '',
        'vod_area' => $video['vod_area'] ?? '中国大陆'
    ];
}

/**
 * 视频详情
 */
function getDetail($ids) {
    $idArray = explode(',', $ids);
    $result = [];
    
    foreach ($idArray as $id) {
        $video = findVideoById($id);
        if ($video) {
            $result[] = formatVideoDetail($video);
        } else {
            $result[] = [
                'vod_id' => $id,
                'vod_name' => '视频 ' . $id,
                'vod_pic' => getRandomImage($id),
                'vod_remarks' => '高清',
                'vod_content' => '视频详情内容',
                'vod_play_from' => '在线播放',
                'vod_play_url' => '正片$https://example.com/video'
            ];
        }
    }
    
    return ['list' => $result];
}

/**
 * 按ID查找视频
 */
function findVideoById($id) {
    $allFiles = getAllFiles();
    
    if (strpos($id, 'txt_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 3) {
            $fileHash = $parts[1];
            $lineNumber = $parts[2];
            
            foreach ($allFiles as $file) {
                if ($file['type'] === 'txt' && md5($file['path']) === $fileHash) {
                    return findTxtVideoByLine($file['path'], $lineNumber);
                }
            }
        }
    } elseif (strpos($id, 'm3u_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 3) {
            $fileHash = $parts[1];
            $lineNumber = $parts[2];
            
            foreach ($allFiles as $file) {
                if ($file['type'] === 'm3u' && md5($file['path']) === $fileHash) {
                    return findM3uVideoByLine($file['path'], $lineNumber);
                }
            }
        }
    } elseif (strpos($id, 'db_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 4) {
            $fileHash = $parts[1];
            $tableName = $parts[2];
            $videoIndex = $parts[3];
            
            foreach ($allFiles as $file) {
                if ($file['type'] === 'db' && md5($file['path']) === $fileHash) {
                    return findDbVideoByIndex($file['path'], $tableName, $videoIndex);
                }
            }
        }
    } else {
        foreach ($allFiles as $file) {
            if ($file['type'] === 'json') {
                $videos = parseJsonFile($file['path']);
                foreach ($videos as $video) {
                    if (isset($video['vod_id']) && $video['vod_id'] == $id) {
                        return $video;
                    }
                }
            }
        }
    }
    
    return null;
}

/**
 * 在TXT文件中按行号查找视频
 */
function findTxtVideoByLine($filePath, $targetLineNumber) {
    if (!file_exists($filePath)) {
        return null;
    }
    
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return null;
    }
    
    $currentLine = 0;
    $video = null;
    
    $defaultImages = getDefaultImages();
    
    // 检测BOM头
    $firstLine = fgets($handle);
    rewind($handle);
    $hasBom = (substr($firstLine, 0, 3) == "\xEF\xBB\xBF");
    if ($hasBom) {
        fseek($handle, 3);
    }
    
    while (($line = fgets($handle)) !== false) {
        $currentLine++;
        $line = trim($line);
        
        if ($line === '' || $line[0] === '#' || $line[0] === ';') continue;
        
        if ($currentLine == $targetLineNumber) {
            $separators = [',', "\t", '|', '$', '#'];
            $separatorPos = false;
            
            foreach ($separators as $sep) {
                $pos = strpos($line, $sep);
                if ($pos !== false) {
                    $separatorPos = $pos;
                    break;
                }
            }
            
            if ($separatorPos !== false) {
                $name = trim(substr($line, 0, $separatorPos));
                $url = trim(substr($line, $separatorPos + 1));
                
                if (!empty($name) && !empty($url)) {
                    $imageIndex = $currentLine % count($defaultImages);
                    
                    $video = [
                        'vod_id' => 'txt_' . md5($filePath) . '_' . $currentLine,
                        'vod_name' => $name,
                        'vod_pic' => $defaultImages[$imageIndex],
                        'vod_remarks' => '高清',
                        'vod_year' => date('Y'),
                        'vod_area' => '中国大陆',
                        'vod_content' => '《' . $name . '》的精彩内容',
                        'vod_play_from' => '在线播放',
                        'vod_play_url' => '正片$' . $url
                    ];
                }
            }
            break;
        }
    }
    
    fclose($handle);
    return $video;
}

/**
 * 在M3U文件中按行号查找视频
 */
function findM3uVideoByLine($filePath, $targetLineNumber) {
    if (!file_exists($filePath)) {
        return null;
    }
    
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return null;
    }
    
    $currentLine = 0;
    $video = null;
    $currentName = '';
    $currentLogo = '';
    $currentGroup = '';
    
    $defaultImages = getDefaultImages();
    
    // 检测BOM头
    $firstLine = fgets($handle);
    rewind($handle);
    $hasBom = (substr($firstLine, 0, 3) == "\xEF\xBB\xBF");
    if ($hasBom) {
        fseek($handle, 3);
    }
    
    while (($line = fgets($handle)) !== false) {
        $currentLine++;
        $line = trim($line);
        if ($line === '') continue;
        
        if (strpos($line, '#EXTM3U') === 0) {
            continue;
        }
        
        if (strpos($line, '#EXTINF:') === 0) {
            $currentName = '';
            $currentLogo = '';
            $currentGroup = '';
            
            $parts = explode(',', $line, 2);
            if (count($parts) > 1) {
                $currentName = trim($parts[1]);
            }
            
            if (preg_match('/tvg-logo="([^"]*)"/i', $line, $logoMatches)) {
                $currentLogo = trim($logoMatches[1]);
            }
            
            if (preg_match('/group-title="([^"]*)"/i', $line, $groupMatches)) {
                $currentGroup = trim($groupMatches[1]);
            }
            
            continue;
        }
        
        if ((strpos($line, 'http') === 0 || strpos($line, 'rtmp') === 0 || 
             strpos($line, 'rtsp') === 0 || strpos($line, 'udp') === 0) && 
            !empty($currentName)) {
            
            if ($currentLine == $targetLineNumber) {
                $imageIndex = $currentLine % count($defaultImages);
                
                $vodPic = $currentLogo;
                if (empty($vodPic) || !filter_var($vodPic, FILTER_VALIDATE_URL)) {
                    $vodPic = $defaultImages[$imageIndex];
                }
                
                $playFrom = '直播源';
                if (!empty($currentGroup)) {
                    $playFrom = $currentGroup;
                }
                
                $video = [
                    'vod_id' => 'm3u_' . md5($filePath) . '_' . $currentLine,
                    'vod_name' => $currentName,
                    'vod_pic' => $vodPic,
                    'vod_remarks' => '直播',
                    'vod_year' => date('Y'),
                    'vod_area' => '中国大陆',
                    'vod_content' => $currentName . '直播频道',
                    'vod_play_from' => $playFrom,
                    'vod_play_url' => '直播$' . $line
                ];
                break;
            }
            
            $currentName = '';
            $currentLogo = '';
            $currentGroup = '';
        }
    }
    
    fclose($handle);
    return $video;
}

/**
 * 在数据库文件中按索引查找视频
 */
function findDbVideoByIndex($filePath, $tableName, $videoIndex) {
    if (!file_exists($filePath) || !extension_loaded('pdo_sqlite')) {
        return null;
    }
    
    try {
        $db = new PDO("sqlite:" . $filePath);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        
        // 获取表结构
        $columns = $db->query("PRAGMA table_info($tableName)")->fetchAll(PDO::FETCH_ASSOC);
        $columnNames = array_column($columns, 'name');
        
        // 查找可能的视频字段
        $nameColumn = null;
        $urlColumn = null;
        $picColumn = null;
        $descColumn = null;
        $yearColumn = null;
        $areaColumn = null;
        
        foreach ($columnNames as $col) {
            $lowerCol = strtolower($col);
            if (in_array($lowerCol, ['name', 'title', 'vod_name', 'filename', 'video_name'])) {
                $nameColumn = $col;
            } elseif (in_array($lowerCol, ['url', 'link', 'vod_url', 'play_url', 'video_url'])) {
                $urlColumn = $col;
            } elseif (in_array($lowerCol, ['pic', 'image', 'cover', 'vod_pic', 'poster'])) {
                $picColumn = $col;
            } elseif (in_array($lowerCol, ['desc', 'description', 'content', 'vod_content'])) {
                $descColumn = $col;
            } elseif (in_array($lowerCol, ['year', 'vod_year'])) {
                $yearColumn = $col;
            } elseif (in_array($lowerCol, ['area', 'region', 'vod_area'])) {
                $areaColumn = $col;
            }
        }
        
        if ($nameColumn && $urlColumn) {
            $selectColumns = [$nameColumn, $urlColumn];
            if ($picColumn) $selectColumns[] = $picColumn;
            if ($descColumn) $selectColumns[] = $descColumn;
            if ($yearColumn) $selectColumns[] = $yearColumn;
            if ($areaColumn) $selectColumns[] = $areaColumn;
            
            $selectSql = "SELECT " . implode(', ', $selectColumns) . " FROM $tableName LIMIT 1 OFFSET " . intval($videoIndex);
            $stmt = $db->query($selectSql);
            $row = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if ($row) {
                $defaultImages = getDefaultImages();
                
                $videoName = $row[$nameColumn] ?? '未知视频';
                $videoUrl = $row[$urlColumn] ?? '';
                $videoPic = $row[$picColumn] ?? $defaultImages[intval($videoIndex) % count($defaultImages)];
                $videoDesc = $row[$descColumn] ?? '《' . $videoName . '》的精彩内容';
                $videoYear = $row[$yearColumn] ?? date('Y');
                $videoArea = $row[$areaColumn] ?? '中国大陆';
                
                $video = [
                    'vod_id' => 'db_' . md5($filePath) . '_' . $tableName . '_' . $videoIndex,
                    'vod_name' => $videoName,
                    'vod_pic' => $videoPic,
                    'vod_remarks' => '高清',
                    'vod_year' => $videoYear,
                    'vod_area' => $videoArea,
                    'vod_content' => $videoDesc,
                    'vod_play_from' => '数据库源',
                    'vod_play_url' => '正片$' . $videoUrl
                ];
                
                $db = null;
                return $video;
            }
        }
        
        $db = null;
        return null;
        
    } catch (PDOException $e) {
        return null;
    }
}

/**
 * 搜索
 */
function search($keyword, $page) {
    if (empty($keyword)) {
        return ['error' => '请输入搜索关键词'];
    }
    
    $searchResults = [];
    $allFiles = getAllFiles();
    
    $searchLimit = 3;
    $searchedFiles = 0;
    
    foreach ($allFiles as $file) {
        if ($searchedFiles >= $searchLimit) break;
        
        $videos = [];
        switch ($file['type']) {
            case 'json':
                $videos = parseJsonFile($file['path']);
                break;
            case 'txt':
                $videos = parseTxtFile($file['path']);
                break;
            case 'm3u':
                $videos = parseM3uFile($file['path']);
                break;
            case 'db':
                $videos = parseDbFile($file['path']);
                break;
        }
        
        // 跳过错误结果
        if (isset($videos['error'])) {
            continue;
        }
        
        foreach ($videos as $video) {
            if (stripos($video['vod_name'] ?? '', $keyword) !== false) {
                $searchResults[] = formatVideoItem($video);
                
                if (count($searchResults) >= 36) break 2; // 12宫格 x 3页
            }
        }
        
        $searchedFiles++;
    }
    
    if (empty($searchResults)) {
        return ['error' => '未找到相关视频内容'];
    }
    
    $pageSize = 12; // 12宫格
    $total = count($searchResults);
    $pageCount = ceil($total / $pageSize);
    $currentPage = intval($page);
    
    if ($currentPage < 1) $currentPage = 1;
    if ($currentPage > $pageCount) $currentPage = $pageCount;
    
    $start = ($currentPage - 1) * $pageSize;
    $pagedResults = array_slice($searchResults, $start, $pageSize);
    
    return [
        'page' => $currentPage,
        'pagecount' => $pageCount,
        'limit' => $pageSize,
        'total' => $total,
        'list' => $pagedResults
    ];
}

/**
 * 格式化视频详情
 */
function formatVideoDetail($video) {
    return [
        'vod_id' => $video['vod_id'] ?? '',
        'vod_name' => $video['vod_name'] ?? '未知视频',
        'vod_pic' => $video['vod_pic'] ?? getRandomImage($video['vod_id'] ?? $video['vod_name']),
        'vod_remarks' => $video['vod_remarks'] ?? '高清',
        'vod_year' => $video['vod_year'] ?? '',
        'vod_area' => $video['vod_area'] ?? '中国大陆',
        'vod_director' => $video['vod_director'] ?? '',
        'vod_actor' => $video['vod_actor'] ?? '',
        'vod_content' => $video['vod_content'] ?? '视频详情内容',
        'vod_play_from' => $video['vod_play_from'] ?? 'default',
        'vod_play_url' => $video['vod_play_url'] ?? ''
    ];
}

/**
 * 获取播放地址
 */
function getPlay($flag, $id) {
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $id
    ];
}

// ============================================================================
// 苹果视频版功能
// ============================================================================

class AppleVideoSpider {
    private $host = "https://618041.xyz";
    private $apiHost = "https://h5.xxoo168.org";
    private $headers = [
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding: gzip, deflate',
        'Connection: keep-alive',
        'Referer: https://618041.xyz'
    ];
    
    private $specialCategories = ['13', '14', '40', '9'];
    private $session;

    public function __construct() {
        $this->session = $this->createSession();
    }

    private function createSession() {
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_HTTPHEADER => $this->headers
        ]);
        return $ch;
    }

    public function fetch($url, $headers = []) {
        curl_setopt($this->session, CURLOPT_URL, $url);
        if (!empty($headers)) {
            curl_setopt($this->session, CURLOPT_HTTPHEADER, array_merge($this->headers, $headers));
        }
        
        $response = curl_exec($this->session);
        $httpCode = curl_getinfo($this->session, CURLINFO_HTTP_CODE);
        
        if ($response === false || $httpCode !== 200) {
            return null;
        }
        
        return $response;
    }

    private function html($content) {
        $dom = new DOMDocument();
        @$dom->loadHTML('<?xml encoding="UTF-8">' . $content);
        return new DOMXPath($dom);
    }

    private function regStr($pattern, $string, $index = 1) {
        if (preg_match($pattern, $string, $matches)) {
            if (isset($matches[$index])) {
                return $matches[$index];
            }
        }
        return "";
    }

    public function getHomeContent() {
        $classes = [
            ['type_id' => '618041.xyz_1', 'type_name' => '全部视频'],
            ['type_id' => '618041.xyz_13', 'type_name' => '香蕉精品'],
            ['type_id' => '618041.xyz_22', 'type_name' => '制服诱惑'],
            ['type_id' => '618041.xyz_6', 'type_name' => '国产视频'],
            ['type_id' => '618041.xyz_8', 'type_name' => '清纯少女'],
            ['type_id' => '618041.xyz_9', 'type_name' => '辣妹大奶'],
            ['type_id' => '618041.xyz_10', 'type_name' => '女同专属'],
            ['type_id' => '618041.xyz_11', 'type_name' => '素人出演'],
            ['type_id' => '618041.xyz_12', 'type_name' => '角色扮演'],
            ['type_id' => '618041.xyz_20', 'type_name' => '人妻熟女'],
            ['type_id' => '618041.xyz_23', 'type_name' => '日韩剧情'],
            ['type_id' => '618041.xyz_21', 'type_name' => '经典伦理'],
            ['type_id' => '618041.xyz_7', 'type_name' => '成人动漫'],
            ['type_id' => '618041.xyz_14', 'type_name' => '精品二区'],
            ['type_id' => '618041.xyz_53', 'type_name' => '动漫中字'],
            ['type_id' => '618041.xyz_52', 'type_name' => '日本无码'],
            ['type_id' => '618041.xyz_33', 'type_name' => '中文字幕'],
            ['type_id' => '618041.xyz_44', 'type_name' => '国产传媒'],
            ['type_id' => '618041.xyz_32', 'type_name' => '国产自拍']
        ];

        $result = ['class' => $classes, 'list' => []];

        try {
            $rsp = $this->fetch($this->host);
            if ($rsp) {
                $doc = $this->html($rsp);
                $videos = $this->getVideos($doc, 12); // 12宫格
                $result['list'] = $videos;
            }
        } catch (Exception $e) {
            // 记录错误但不影响返回
        }

        return $result;
    }

    public function getCategoryContent($tid, $pg, $extend) {
        try {
            list($domain, $typeId) = explode('_', $tid);
            $url = "https://{$domain}/index.php/vod/type/id/{$typeId}.html";
            
            if ($pg != '1') {
                $url = str_replace('.html', "/page/{$pg}.html", $url);
            }

            $rsp = $this->fetch($url);
            if (!$rsp) {
                return ['list' => []];
            }

            $doc = $this->html($rsp);
            $videos = $this->getVideos($doc, null, $typeId);

            return [
                'list' => $videos,
                'page' => intval($pg),
                'pagecount' => 999,
                'limit' => 12, // 12宫格
                'total' => 19980
            ];
        } catch (Exception $e) {
            return ['list' => []];
        }
    }

    public function getDetailContent($ids) {
        $vid = $ids[0];
        
        try {
            // 检查特殊分区链接
            if (strpos($vid, 'special_') === 0) {
                $parts = explode('_', $vid);
                if (count($parts) >= 4) {
                    $categoryId = $parts[1];
                    $videoId = $parts[2];
                    $encodedUrl = implode('_', array_slice($parts, 3));
                    $playUrl = urldecode($encodedUrl);
                    
                    // 解析播放链接参数
                    $parsedUrl = parse_url($playUrl);
                    parse_str($parsedUrl['query'] ?? '', $queryParams);
                    
                    $videoUrl = $queryParams['v'] ?? '';
                    $picUrl = $queryParams['b'] ?? getRandomImage($videoId);
                    $titleEncrypted = $queryParams['m'] ?? '';
                    
                    $title = $this->decryptTitle($titleEncrypted);
                    
                    return [
                        'list' => [[
                            'vod_id' => $vid,
                            'vod_name' => $title,
                            'vod_pic' => $picUrl,
                            'vod_remarks' => '',
                            'vod_year' => '',
                            'vod_play_from' => '直接播放',
                            'vod_play_url' => "第1集\${$playUrl}"
                        ]]
                    ];
                }
            }

            // 常规处理
            if (substr_count($vid, '_') >= 2) {
                list($domain, $categoryId, $videoId) = explode('_', $vid);
            } else {
                list($domain, $videoId) = explode('_', $vid);
            }

            $detailUrl = "https://{$domain}/index.php/vod/detail/id/{$videoId}.html";
            $rsp = $this->fetch($detailUrl);
            
            if (!$rsp) {
                return ['list' => []];
            }

            $doc = $this->html($rsp);
            $videoInfo = $this->getDetail($doc, $rsp, $vid);
            
            return $videoInfo ? ['list' => [$videoInfo]] : ['list' => []];
        } catch (Exception $e) {
            return ['list' => []];
        }
    }

    public function getSearchContent($key, $pg = 1) {
        try {
            $encodedKey = urlencode($key);
            $searchUrl = "{$this->host}/index.php/vod/type/id/1/wd/{$encodedKey}/page/{$pg}.html";
            
            $rsp = $this->fetch($searchUrl);
            if (!$rsp) {
                return ['list' => []];
            }

            $doc = $this->html($rsp);
            $videos = $this->getVideos($doc, 12); // 12宫格

            // 尝试解析分页信息
            $pagecount = 5;
            $total = 100;

            return [
                'list' => $videos,
                'page' => intval($pg),
                'pagecount' => $pagecount,
                'limit' => 12,
                'total' => $total
            ];
        } catch (Exception $e) {
            return ['list' => []];
        }
    }

    public function getPlayerContent($id) {
        try {
            // 检查特殊分区链接
            if (strpos($id, 'special_') === 0) {
                $parts = explode('_', $id);
                if (count($parts) >= 4) {
                    $categoryId = $parts[1];
                    $videoId = $parts[2];
                    $encodedUrl = implode('_', array_slice($parts, 3));
                    $playUrl = urldecode($encodedUrl);
                    
                    $parsedUrl = parse_url($playUrl);
                    parse_str($parsedUrl['query'] ?? '', $queryParams);
                    $videoUrl = $queryParams['v'] ?? '';
                    
                    if ($videoUrl) {
                        if (strpos($videoUrl, '//') === 0) {
                            $videoUrl = 'https:' . $videoUrl;
                        } elseif (strpos($videoUrl, 'http') !== 0) {
                            $videoUrl = $this->host . '/' . ltrim($videoUrl, '/');
                        }
                        
                        return ['parse' => 0, 'playUrl' => '', 'url' => $videoUrl];
                    }
                }
            }

            // 检查完整URL
            if (strpos($id, 'http') === 0) {
                $parsedUrl = parse_url($id);
                parse_str($parsedUrl['query'] ?? '', $queryParams);
                
                $videoUrl = $queryParams['v'] ?? '';
                if (!$videoUrl) {
                    foreach ($queryParams as $key => $value) {
                        if (in_array($key, ['url', 'src', 'file'])) {
                            $videoUrl = $value;
                            break;
                        }
                    }
                }
                
                if ($videoUrl) {
                    $videoUrl = urldecode($videoUrl);
                    if (strpos($videoUrl, '//') === 0) {
                        $videoUrl = 'https:' . $videoUrl;
                    } elseif (strpos($videoUrl, 'http') !== 0) {
                        $videoUrl = $this->host . '/' . ltrim($videoUrl, '/');
                    }
                    
                    return ['parse' => 0, 'playUrl' => '', 'url' => $videoUrl];
                } else {
                    // 从页面提取视频链接
                    $rsp = $this->fetch($id);
                    if ($rsp) {
                        $videoUrl = $this->extractDirectVideoUrl($rsp);
                        if ($videoUrl) {
                            return ['parse' => 0, 'playUrl' => '', 'url' => $videoUrl];
                        }
                    }
                    
                    return ['parse' => 1, 'playUrl' => '', 'url' => $id];
                }
            }

            // 提取视频ID和分类ID
            $parts = explode('_', $id);
            $videoId = end($parts);
            $categoryId = count($parts) >= 3 ? $parts[1] : '';
            
            // 特殊分类处理
            if ($categoryId && in_array($categoryId, $this->specialCategories)) {
                $playPageUrl = "{$this->host}/index.php/vod/play/id/{$videoId}.html";
                $rsp = $this->fetch($playPageUrl);
                
                if ($rsp) {
                    $videoUrl = $this->extractDirectVideoUrl($rsp);
                    if ($videoUrl) {
                        return ['parse' => 0, 'playUrl' => '', 'url' => $videoUrl];
                    }
                }
                
                return $this->getVideoByApi($id, $videoId);
            } else {
                return $this->getVideoByApi($id, $videoId);
            }
        } catch (Exception $e) {
            $playUrl = strpos($id, '_') !== false ? 
                "https://618041.xyz/html/kkyd.html?m=" . explode('_', $id)[1] : 
                "{$this->host}/html/kkyd.html?m={$id}";
                
            return ['parse' => 1, 'playUrl' => '', 'url' => $playUrl];
        }
    }

    private function getVideoByApi($id, $videoId) {
        try {
            $apiUrl = "{$this->apiHost}/api/v2/vod/reqplay/{$videoId}";
            $apiHeaders = [
                'Referer: ' . $this->host . '/',
                'Origin: ' . $this->host,
                'X-Requested-With: XMLHttpRequest'
            ];
            
            $apiResponse = $this->fetch($apiUrl, $apiHeaders);
            if ($apiResponse) {
                $data = json_decode($apiResponse, true);
                
                if ($data && isset($data['retcode'])) {
                    if ($data['retcode'] == 3) {
                        $videoUrl = $data['data']['httpurl_preview'] ?? '';
                    } else {
                        $videoUrl = $data['data']['httpurl'] ?? '';
                    }
                    
                    if ($videoUrl) {
                        $videoUrl = str_replace('?300', '', $videoUrl);
                        return ['parse' => 0, 'playUrl' => '', 'url' => $videoUrl];
                    }
                }
            }
            
            $playUrl = strpos($id, '_') !== false ? 
                "https://618041.xyz/html/kkyd.html?m=" . explode('_', $id)[1] : 
                "{$this->host}/html/kkyd.html?m={$id}";
                
            return ['parse' => 1, 'playUrl' => '', 'url' => $playUrl];
        } catch (Exception $e) {
            $playUrl = strpos($id, '_') !== false ? 
                "https://618041.xyz/html/kkyd.html?m=" . explode('_', $id)[1] : 
                "{$this->host}/html/kkyd.html?m={$id}";
                
            return ['parse' => 1, 'playUrl' => '', 'url' => $playUrl];
        }
    }

    private function extractDirectVideoUrl($htmlContent) {
        $patterns = [
            '/v=([^&]+\.(?:m3u8|mp4))/',
            '/"url"\s*:\s*["\']([^"\']+\.(?:mp4|m3u8))["\']/',
            '/src\s*=\s*["\']([^"\']+\.(?:mp4|m3u8))["\']/',
            '/http[^\s<>"\'?]+\.(?:mp4|m3u8)/'
        ];
        
        foreach ($patterns as $pattern) {
            if (preg_match_all($pattern, $htmlContent, $matches)) {
                foreach ($matches[1] ?? $matches[0] as $match) {
                    $extractedUrl = str_replace('\\', '', $match);
                    $extractedUrl = urldecode($extractedUrl);
                    
                    if (strpos($extractedUrl, '//') === 0) {
                        $extractedUrl = 'https:' . $extractedUrl;
                    } elseif (strpos($extractedUrl, 'http') === 0) {
                        return $extractedUrl;
                    }
                }
            }
        }
        
        return null;
    }

    private function getVideos($doc, $limit = null, $categoryId = null) {
        $videos = [];
        
        $elements = $doc->query('//a[@class="vodbox"]');
        if (!$elements) {
            return $videos;
        }
        
        foreach ($elements as $element) {
            $video = $this->extractVideo($element, $categoryId);
            if ($video) {
                $videos[] = $video;
            }
        }
        
        return $limit ? array_slice($videos, 0, $limit) : $videos;
    }

    private function extractVideo($element, $categoryId = null) {
        try {
            $link = $element->getAttribute('href');
            if (strpos($link, '/') === 0) {
                $link = $this->host . $link;
            }
            
            $isSpecialLink = strpos($link, 'ar-kk.html') !== false || strpos($link, 'ar.html') !== false;
            
            if ($isSpecialLink && $categoryId && in_array($categoryId, $this->specialCategories)) {
                $parsedUrl = parse_url($link);
                parse_str($parsedUrl['query'] ?? '', $queryParams);
                
                $videoUrl = $queryParams['v'] ?? '';
                if ($videoUrl) {
                    if (preg_match('/\/([a-f0-9-]+)\/video\.m3u8/', $videoUrl, $matches)) {
                        $videoId = $matches[1];
                    } else {
                        $videoId = abs(crc32($link)) % 1000000;
                    }
                } else {
                    $videoId = abs(crc32($link)) % 1000000;
                }
                
                $finalVodId = "special_{$categoryId}_{$videoId}_" . urlencode($link);
            } else {
                $vodId = $this->regStr('/m=(\d+)/', $link);
                if (!$vodId) {
                    $vodId = abs(crc32($link)) % 1000000;
                }
                
                $finalVodId = "618041.xyz_{$vodId}";
                if ($categoryId) {
                    $finalVodId = "618041.xyz_{$categoryId}_{$vodId}";
                }
            }
            
            // 提取标题
            $title = '';
            $titlePaths = [
                './/p[@class="km-script"]/text()',
                './/p[contains(@class, "script")]/text()',
                './/p/text()',
                './/h3/text()',
                './/h4/text()'
            ];
            
            foreach ($titlePaths as $path) {
                $titleNodes = $element->ownerDocument->saveXML($element);
                if (preg_match('/<[^>]*class="[^"]*km-script[^"]*"[^>]*>([^<]*)<\/[^>]*>/', $titleNodes, $matches)) {
                    $title = trim($matches[1]);
                    break;
                }
            }
            
            if (!$title) {
                return null;
            }
            
            $title = $this->decryptTitle($title);
            
            // 提取图片 - 增强图片提取逻辑
            $pic = '';
            $imgPaths = [
                './/img/@data-original',
                './/img/@src',
                './/img/@data-src'
            ];
            
            foreach ($imgPaths as $path) {
                $imgNodes = $element->ownerDocument->saveXML($element);
                if (preg_match('/<img[^>]*(?:data-original|data-src|src)="([^"]*)"/', $imgNodes, $matches)) {
                    $pic = $matches[1];
                    break;
                }
            }
            
            if ($pic) {
                if (strpos($pic, '//') === 0) {
                    $pic = 'https:' . $pic;
                } elseif (strpos($pic, '/') === 0) {
                    $pic = $this->host . $pic;
                }
            } else {
                // 如果没有提取到图片，使用随机图片
                $pic = getRandomImage($finalVodId);
            }
            
            return [
                'vod_id' => $finalVodId,
                'vod_name' => $title,
                'vod_pic' => $pic,
                'vod_remarks' => '',
                'vod_year' => ''
            ];
        } catch (Exception $e) {
            return null;
        }
    }

    private function decryptTitle($encryptedText) {
        $decryptedChars = [];
        for ($i = 0; $i < strlen($encryptedText); $i++) {
            $codePoint = ord($encryptedText[$i]);
            $decryptedCode = $codePoint ^ 128;
            $decryptedChars[] = chr($decryptedCode);
        }
        return implode('', $decryptedChars);
    }

    private function getDetail($doc, $htmlContent, $vid) {
        try {
            $title = $this->getText($doc, [
                '//h1/text()',
                '//title/text()'
            ]);
            
            $pic = $this->getText($doc, [
                '//div[contains(@class,"dyimg")]//img/@src',
                '//img[contains(@class,"poster")]/@src',
                '//meta[@property="og:image"]/@content'
            ]);
            
            if ($pic && strpos($pic, '/') === 0) {
                $pic = $this->host . $pic;
            } elseif (empty($pic)) {
                $pic = getRandomImage($vid);
            }
            
            $desc = $this->getText($doc, [
                '//div[contains(@class,"yp_context")]/text()',
                '//div[contains(@class,"introduction")]//text()',
                '//meta[@name="description"]/@content'
            ]);
            
            $actor = $this->getText($doc, [
                '//span[contains(text(),"主演")]/following-sibling::*/text()'
            ]);
            
            $director = $this->getText($doc, [
                '//span[contains(text(),"导演")]/following-sibling::*/text()'
            ]);

            $playFrom = [];
            $playUrls = [];
            
            // 查找播放链接
            $playerLinkPatterns = [
                '/href="(.*?ar\.html.*?)"/',
                '/href="(.*?kkyd\.html.*?)"/',
                '/href="(.*?ar-kk\.html.*?)"/'
            ];
            
            $playerLinks = [];
            foreach ($playerLinkPatterns as $pattern) {
                if (preg_match_all($pattern, $htmlContent, $matches)) {
                    $playerLinks = array_merge($playerLinks, $matches[1]);
                }
            }
            
            if (!empty($playerLinks)) {
                $episodes = [];
                foreach ($playerLinks as $link) {
                    $fullUrl = $this->resolveUrl($link);
                    $episodes[] = "第1集\${$fullUrl}";
                }
                
                if (!empty($episodes)) {
                    $playFrom[] = "默认播放源";
                    $playUrls[] = implode('#', $episodes);
                }
            }
            
            if (empty($playFrom)) {
                return [
                    'vod_id' => $vid,
                    'vod_name' => $title,
                    'vod_pic' => $pic,
                    'type_name' => '',
                    'vod_year' => '',
                    'vod_area' => '',
                    'vod_remarks' => '',
                    'vod_actor' => $actor,
                    'vod_director' => $director,
                    'vod_content' => $desc,
                    'vod_play_from' => '默认播放源',
                    'vod_play_url' => "第1集\${$vid}"
                ];
            }

            return [
                'vod_id' => $vid,
                'vod_name' => $title,
                'vod_pic' => $pic,
                'type_name' => '',
                'vod_year' => '',
                'vod_area' => '',
                'vod_remarks' => '',
                'vod_actor' => $actor,
                'vod_director' => $director,
                'vod_content' => $desc,
                'vod_play_from' => implode('$$$', $playFrom),
                'vod_play_url' => implode('$$$', $playUrls)
            ];
        } catch (Exception $e) {
            return null;
        }
    }

    private function getText($doc, $selectors) {
        foreach ($selectors as $selector) {
            $nodes = $doc->query($selector);
            if ($nodes && $nodes->length > 0) {
                for ($i = 0; $i < $nodes->length; $i++) {
                    $text = trim($nodes->item($i)->nodeValue);
                    if ($text) {
                        return $text;
                    }
                }
            }
        }
        return '';
    }

    private function resolveUrl($url) {
        if (strpos($url, 'http') === 0) {
            return $url;
        } elseif (strpos($url, '//') === 0) {
            return 'https:' . $url;
        } else {
            return $this->host . '/' . ltrim($url, '/');
        }
    }

    public function __destruct() {
        if ($this->session) {
            curl_close($this->session);
        }
    }
}

/**
 * 苹果视频版首页数据
 */
function getAppleHome() {
    $spider = new AppleVideoSpider();
    return $spider->getHomeContent();
}

/**
 * 苹果视频版分类
 */
function getAppleCategory($pg) {
    $spider = new AppleVideoSpider();
    return $spider->getCategoryContent('618041.xyz_1', $pg, []);
}

/**
 * 苹果视频版详情
 */
function getAppleDetail($ids) {
    $spider = new AppleVideoSpider();
    return $spider->getDetailContent(explode(',', $ids));
}

/**
 * 苹果视频版搜索
 */
function searchApple($keyword, $page) {
    $spider = new AppleVideoSpider();
    return $spider->getSearchContent($keyword, $page);
}

/**
 * 苹果视频版播放
 */
function getApplePlay($flag, $id) {
    $spider = new AppleVideoSpider();
    return $spider->getPlayerContent($id);
}

// ============================================================================
// 金牌影视功能
// ============================================================================

class JinPaiSpider {
    private $host = "https://www.hkybqufgh.com";
    private $headers = [
        'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept' => 'application/json, text/plain, */*',
        'Origin' => 'https://www.hkybqufgh.com',
        'Referer' => 'https://www.hkybqufgh.com/',
        'DNT' => '1'
    ];
    private $session;
    private $key = 'cb808529bae6b6be45ecfab29a4889bc';

    public function __construct($extend = '') {
        if ($extend && isset(json_decode($extend, true)['site'])) {
            $hosts = json_decode($extend, true)['site'];
            $this->host = $this->getFastestHost($hosts);
        }
        $this->session = $this->createSession();
    }

    private function createSession() {
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_FOLLOWLOCATION => true
        ]);
        return $ch;
    }

    private function getFastestHost($hosts) {
        if (is_string($hosts)) {
            $hosts = array_map('trim', explode(',', $hosts));
        }
        
        if (empty($hosts)) {
            return $this->host;
        }
        
        if (count($hosts) === 1) {
            return $hosts[0];
        }

        $results = [];
        $mh = curl_multi_init();
        $handles = [];

        foreach ($hosts as $host) {
            $ch = curl_init();
            curl_setopt_array($ch, [
                CURLOPT_URL => $host,
                CURLOPT_NOBODY => true,
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_HEADER => false,
                CURLOPT_TIMEOUT => 2,
                CURLOPT_FOLLOWLOCATION => false
            ]);
            curl_multi_add_handle($mh, $ch);
            $handles[$host] = $ch;
        }

        do {
            curl_multi_exec($mh, $running);
            curl_multi_select($mh);
        } while ($running > 0);

        foreach ($handles as $host => $ch) {
            $info = curl_getinfo($ch);
            if ($info['http_code'] === 200) {
                $results[$host] = $info['total_time'];
            } else {
                $results[$host] = PHP_FLOAT_MAX;
            }
            curl_multi_remove_handle($mh, $ch);
            curl_close($ch);
        }

        curl_multi_close($mh);

        if (empty($results)) {
            return $hosts[0];
        }

        return array_search(min($results), $results);
    }

    private function buildSign($params) {
        $params['key'] = $this->key;
        $params['t'] = round(microtime(true) * 1000);
        
        $paramStr = $this->buildParamString($params);
        $md5 = md5($paramStr);
        $sign = sha1($md5);
        
        return [
            'sign' => $sign,
            't' => $params['t'],
            'deviceid' => $this->generateDeviceId()
        ];
    }

    private function buildParamString($params) {
        $parts = [];
        foreach ($params as $key => $value) {
            $parts[] = $key . '=' . $value;
        }
        return implode('&', $parts);
    }

    private function generateDeviceId() {
        return sprintf('%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            mt_rand(0, 0xffff), mt_rand(0, 0xffff),
            mt_rand(0, 0xffff),
            mt_rand(0, 0x0fff) | 0x4000,
            mt_rand(0, 0x3fff) | 0x8000,
            mt_rand(0, 0xffff), mt_rand(0, 0xffff), mt_rand(0, 0xffff)
        );
    }

    public function fetch($url, $params = []) {
        $signData = $this->buildSign($params);
        
        $headers = $this->headers;
        $headers['sign'] = $signData['sign'];
        $headers['t'] = $signData['t'];
        $headers['deviceid'] = $signData['deviceid'];
        
        curl_setopt_array($this->session, [
            CURLOPT_URL => $url,
            CURLOPT_HTTPHEADER => $this->buildHeaders($headers)
        ]);
        
        $response = curl_exec($this->session);
        $httpCode = curl_getinfo($this->session, CURLINFO_HTTP_CODE);
        
        if ($response === false || $httpCode !== 200) {
            return null;
        }
        
        return $response;
    }

    private function buildHeaders($headers) {
        $headerArray = [];
        foreach ($headers as $key => $value) {
            $headerArray[] = $key . ': ' . $value;
        }
        return $headerArray;
    }

    public function getHomeContent() {
        // 获取分类数据
        $categoryData = json_decode($this->fetch($this->host . "/api/mw-movie/anonymous/get/filer/type"), true);
        // 获取筛选数据
        $filterData = json_decode($this->fetch($this->host . "/api/mw-movie/anonymous/v1/get/filer/list"), true);
        // 获取首页视频数据
        $homeData = json_decode($this->fetch($this->host . "/api/mw-movie/anonymous/v1/home/all/list"), true);
        // 获取热门搜索数据
        $hotData = json_decode($this->fetch($this->host . "/api/mw-movie/anonymous/home/hotSearch"), true);

        $result = [
            "class" => [],
            "filters" => [],
            "list" => []
        ];

        // 处理分类
        if (isset($categoryData['data'])) {
            foreach ($categoryData['data'] as $category) {
                $result['class'][] = [
                    'type_id' => strval($category['typeId']),
                    'type_name' => $category['typeName']
                ];
            }
        }

        // 处理筛选条件
        if (isset($filterData['data'])) {
            $sortValues = [
                ["n" => "最近更新", "v" => "2"],
                ["n" => "人气高低", "v" => "3"], 
                ["n" => "评分高低", "v" => "4"]
            ];
            
            foreach ($filterData['data'] as $tid => $data) {
                $currentSortValues = $sortValues;
                if ($tid == '1') {
                    array_shift($currentSortValues);
                }
                
                $filters = [
                    [
                        "key" => "type",
                        "name" => "类型",
                        "value" => array_map(function($item) {
                            return ["n" => $item["itemText"], "v" => $item["itemValue"]];
                        }, $data["typeList"])
                    ]
                ];
                
                if (!empty($data["plotList"])) {
                    $filters[] = [
                        "key" => "v_class",
                        "name" => "剧情",
                        "value" => array_map(function($item) {
                            return ["n" => $item["itemText"], "v" => $item["itemText"]];
                        }, $data["plotList"])
                    ];
                }
                
                $filters[] = [
                    "key" => "area", 
                    "name" => "地区",
                    "value" => array_map(function($item) {
                        return ["n" => $item["itemText"], "v" => $item["itemText"]];
                    }, $data["districtList"])
                ];
                
                $filters[] = [
                    "key" => "year",
                    "name" => "年份", 
                    "value" => array_map(function($item) {
                        return ["n" => $item["itemText"], "v" => $item["itemText"]];
                    }, $data["yearList"])
                ];
                
                $filters[] = [
                    "key" => "lang",
                    "name" => "语言",
                    "value" => array_map(function($item) {
                        return ["n" => $item["itemText"], "v" => $item["itemText"]];
                    }, $data["languageList"])
                ];
                
                $filters[] = [
                    "key" => "sort",
                    "name" => "排序", 
                    "value" => $currentSortValues
                ];
                
                $result['filters'][$tid] = $filters;
            }
        }

        // 处理视频列表
        $videos = [];
        if (isset($homeData['data'])) {
            foreach ($homeData['data'] as $categoryVideos) {
                if (isset($categoryVideos['list'])) {
                    foreach ($categoryVideos['list'] as $video) {
                        $convertedVideo = $this->convertVideoFields($video);
                        // 确保有预览图
                        if (empty($convertedVideo['vod_pic'])) {
                            $convertedVideo['vod_pic'] = getRandomImage($convertedVideo['vod_id'] ?? $convertedVideo['vod_name']);
                        }
                        $videos[] = $convertedVideo;
                    }
                }
            }
        }
        
        if (isset($hotData['data'])) {
            foreach ($hotData['data'] as $video) {
                $convertedVideo = $this->convertVideoFields($video);
                // 确保有预览图
                if (empty($convertedVideo['vod_pic'])) {
                    $convertedVideo['vod_pic'] = getRandomImage($convertedVideo['vod_id'] ?? $convertedVideo['vod_name']);
                }
                $videos[] = $convertedVideo;
            }
        }
        
        $result['list'] = $videos;

        return $result;
    }

    public function getCategoryContent($tid, $pg, $extend) {
        $params = [
            "area" => $extend['area'] ?? '',
            "filterStatus" => "1",
            "lang" => $extend['lang'] ?? '',
            "pageNum" => $pg,
            "pageSize" => "12", // 12宫格
            "sort" => $extend['sort'] ?? '1',
            "sortBy" => "1",
            "type" => $extend['type'] ?? '',
            "type1" => $tid,
            "v_class" => $extend['v_class'] ?? '',
            "year" => $extend['year'] ?? ''
        ];

        $url = $this->host . "/api/mw-movie/anonymous/video/list?" . $this->buildParamString($params);
        $response = json_decode($this->fetch($url, $params), true);

        $result = [
            "list" => [],
            "page" => intval($pg),
            "pagecount" => 9999,
            "limit" => 12, // 12宫格
            "total" => 999999
        ];

        if (isset($response['data']['list'])) {
            foreach ($response['data']['list'] as $video) {
                $convertedVideo = $this->convertVideoFields($video);
                // 确保有预览图
                if (empty($convertedVideo['vod_pic'])) {
                    $convertedVideo['vod_pic'] = getRandomImage($convertedVideo['vod_id'] ?? $convertedVideo['vod_name']);
                }
                $result['list'][] = $convertedVideo;
            }
        }

        return $result;
    }

    public function getDetailContent($ids) {
        $params = ['id' => $ids[0]];
        $url = $this->host . "/api/mw-movie/anonymous/video/detail?id=" . $ids[0];
        $response = json_decode($this->fetch($url, $params), true);

        $result = ["list" => []];

        if (isset($response['data'])) {
            $video = $this->convertVideoFields($response['data']);
            
            // 确保有预览图
            if (empty($video['vod_pic'])) {
                $video['vod_pic'] = getRandomImage($video['vod_id'] ?? $video['vod_name']);
            }
            
            // 处理播放列表
            if (isset($video['episodelist']) && is_array($video['episodelist'])) {
                $playUrls = [];
                foreach ($video['episodelist'] as $episode) {
                    $episodeName = count($video['episodelist']) > 1 ? 
                        $episode['name'] : $video['vod_name'];
                    $playUrls[] = $episodeName . '$' . $ids[0] . '@@' . $episode['nid'];
                }
                
                $video['vod_play_from'] = '金牌影视';
                $video['vod_play_url'] = implode('#', $playUrls);
                unset($video['episodelist']);
            }
            
            $result['list'][] = $video;
        }

        return $result;
    }

    public function getSearchContent($key, $pg = 1) {
        $params = [
            "keyword" => $key,
            "pageNum" => $pg,
            "pageSize" => "12", // 12宫格
            "sourceCode" => "1"
        ];

        $url = $this->host . "/api/mw-movie/anonymous/video/searchByWord?" . $this->buildParamString($params);
        $response = json_decode($this->fetch($url, $params), true);

        $result = ["list" => []];

        if (isset($response['data']['result']['list'])) {
            foreach ($response['data']['result']['list'] as $video) {
                $convertedVideo = $this->convertVideoFields($video);
                // 确保有预览图
                if (empty($convertedVideo['vod_pic'])) {
                    $convertedVideo['vod_pic'] = getRandomImage($convertedVideo['vod_id'] ?? $convertedVideo['vod_name']);
                }
                $result['list'][] = $convertedVideo;
            }
        }

        $result['page'] = $pg;
        return $result;
    }

    public function getPlayerContent($id) {
        $ids = explode('@@', $id);
        if (count($ids) < 2) {
            return ["parse" => 1, "playUrl" => "", "url" => ""];
        }

        $params = [
            'clientType' => '1',
            'id' => $ids[0],
            'nid' => $ids[1]
        ];

        $url = $this->host . "/api/mw-movie/anonymous/v2/video/episode/url?clientType=1&id=" . $ids[0] . "&nid=" . $ids[1];
        $response = json_decode($this->fetch($url, $params), true);

        $result = ["parse" => 0, "playUrl" => "", "url" => ""];
        $vlist = [];

        if (isset($response['data']['list'])) {
            foreach ($response['data']['list'] as $quality) {
                $vlist[] = $quality['resolutionName'];
                $vlist[] = $quality['url'];
            }
            $result['url'] = $vlist;
        }

        return $result;
    }

    private function convertVideoFields($video) {
        $converted = [];
        foreach ($video as $key => $value) {
            $newKey = $this->convertFieldName($key);
            $converted[$newKey] = $value;
        }
        return $converted;
    }

    private function convertFieldName($field) {
        $field = strtolower($field);
        if (strpos($field, 'vod') === 0 && strlen($field) > 3) {
            $field = 'vod_' . substr($field, 3);
        }
        if (strpos($field, 'type') === 0 && strlen($field) > 4) {
            $field = 'type_' . substr($field, 4);
        }
        return $field;
    }

    public function __destruct() {
        if ($this->session) {
            curl_close($this->session);
        }
    }
}

/**
 * 金牌影视首页数据
 */
function getJinPaiHome() {
    $spider = new JinPaiSpider();
    return $spider->getHomeContent();
}

/**
 * 金牌影视分类
 */
function getJinPaiCategory($pg) {
    $spider = new JinPaiSpider();
    return $spider->getCategoryContent('1', $pg, []);
}

/**
 * 金牌影视详情
 */
function getJinPaiDetail($ids) {
    $spider = new JinPaiSpider();
    return $spider->getDetailContent(explode(',', $ids));
}

/**
 * 金牌影视搜索
 */
function searchJinPai($keyword, $page) {
    $spider = new JinPaiSpider();
    return $spider->getSearchContent($keyword, $page);
}

/**
 * 金牌影视播放
 */
function getJinPaiPlay($flag, $id) {
    $spider = new JinPaiSpider();
    return $spider->getPlayerContent($id);
}

?>
<?php
ini_set('memory_limit', '-1');

$ac = $_GET['ac'] ?? 'detail';
$t = $_GET['t'] ?? '';
$pg = $_GET['pg'] ?? '1';
$ids = $_GET['ids'] ?? '';
$wd = $_GET['wd'] ?? '';
$flag = $_GET['flag'] ?? '';
$id = $_GET['id'] ?? '';

header('Content-Type: application/json; charset=utf-8');

@set_time_limit(60);

switch ($ac) {
    case 'detail':
        if (!empty($ids)) {
            echo json_encode(getDetail($ids));
        } elseif (!empty($t)) {
            echo json_encode(getCategory($t, $pg));
        } else {
            echo json_encode(getHome());
        }
        break;
    
    case 'search':
        echo json_encode(search($wd, $pg));
        break;
        
    case 'play':
        echo json_encode(getPlay($flag, $id));
        break;
    
    default:
        echo json_encode(['error' => 'Unknown action: ' . $ac]);
}

function scanDirectoryFast($dir, $types) {
    $files = [];
    
    if (!is_dir($dir)) {
        return $files;
    }
    
    $items = @scandir($dir);
    if ($items === false) return $files;
    
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') continue;
        
        $path = $dir . $item;
        
        if (is_dir($path)) {
            $subFiles = scanDirectoryFast($path . '/', $types);
            $files = array_merge($files, $subFiles);
        } else {
            $extension = pathinfo($path, PATHINFO_EXTENSION);
            if (in_array($extension, $types)) {
                $fileSize = @filesize($path);
                if ($fileSize > 100 * 1024 * 1024) {
                    continue;
                }
                
                $files[] = [
                    'type' => $extension,
                    'path' => $path,
                    'name' => $item,
                    'filename' => pathinfo($item, PATHINFO_FILENAME),
                    'size' => $fileSize
                ];
            }
        }
    }
    
    return $files;
}

function getAllFilesFast() {
    static $allFiles = null;
    
    if ($allFiles === null) {
        $allFiles = [];
        
        // 现有数据文件类型
        $jsonFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', ['json']);
        $txtFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', ['txt']);
        $m3uFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', ['m3u']);
        $dbFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', ['db']);
        
        // 新增媒体文件类型 - 单独存储用于媒体库分类
        $audioFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', [
            'mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg', 'wma'
        ]);
        
        $videoFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', [
            'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp'
        ]);
        
        $imageFiles = scanDirectoryFast('/storage/emulated/0/lz/php/', [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'
        ]);
        
        // 存储媒体文件用于媒体库分类
        $GLOBALS['media_files'] = [
            'audio' => $audioFiles,
            'video' => $videoFiles,
            'image' => $imageFiles
        ];
        
        $allFiles = array_merge(
            $jsonFiles, $txtFiles, $m3uFiles, $dbFiles
            // 注意：这里不合并媒体文件，让它们只在媒体库中显示
        );
    }
    
    return $allFiles;
}

function getTutorialVideo() {
    return [
        'vod_id' => 'tutorial_1',
        'vod_name' => '📚 TVBox 使用教程',
        'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'vod_remarks' => '教程',
        'vod_year' => '2025',
        'vod_area' => '教程',
        'vod_content' => "📱 TVBox 使用教程\n\n" .
                        "🎯 文件放置位置：\n" .
                        "   • JSON文件：/storage/emulated/0/lz/php/\n" .
                        "   • TXT文件：/storage/emulated/0/lz/php/\n" .
                        "   • M3U文件：可放在以上任意目录\n" .
                        "   • 数据库文件：/storage/emulated/0/lz/php/\n" .
                        "   • 媒体文件：/storage/emulated/0/lz/php/\n\n" .
                        "📝 文件格式要求：\n" .
                        "   • JSON：标准TVBox格式，包含list数组\n" .
                        "   • TXT：视频名称,视频URL 格式（一行一个）\n" .
                        "   • M3U：标准直播源格式\n" .
                        "   • DB：SQLite数据库文件\n" .
                        "   • 媒体：MP3/MP4等常见音视频格式\n\n" .
                        "📷 媒体库功能：\n" .
                        "   • 自动扫描本地音频、视频、图片文件\n" .
                        "   • 支持直接播放本地媒体文件\n" .
                        "   • 分类显示不同类型的媒体\n\n" .
                        "🔥 推荐分类说明：\n" .
                        "   • 真懒加载模式，每次翻页只读10个视频\n" .
                        "   • 支持无限翻页浏览所有文件\n" .
                        "   • 首页显示扫描到的文件数量统计",
        'vod_play_from' => '教程',
        'vod_play_url' => '教程$https://d6.qyshare.store/s/TBVWTxUNFQcFUQQHKFCVA50wKFCVA50FGlQEKFCVA50QIaKFCVA501EHVhoOD1EBGgEBUwBRKFCVA50VFRBVYPDxUbFVhERH9YREMVDRVYREQZRk5CWRlYRVKFCVA50VGxVYRER8Uk4VDRVCR1tYVlMYBQcFKFCVA50hgGBxgFKFCVA50RgFUgJWDgMGUxoHUQ9SGgNWU1IaDlFVDxpRBwVVUQcGKFCVA50Q8KFCVA50BQ4ZVV5ZFRsVVlQVDRUGDlMFBFQGBBoBKFCVA50wYEGgNRKFCVA50w4aDlICBhoPBw8FVQ8PVgNWVVIVGxVZVlpSFQ0VKFCVA50mgBBKFCVA50QBKFCVA50Q4DDgcEKFCVA50wYEKFCVA50QKFCVA50KFCVA50KFCVA50gQHGVpHKFCVA50xUbFVRYWUNSWUNjTkdSFQ0VQV5TUlgYWkcDFRsVVlMVDRUPBwVWBQUBVRoEKFCVA501IEGgMDUgEaVQQFURoBBgcCDgYOVVMEDlIVSg=='
    ];
}

function getRecommendVideos($page) {
    $allFiles = getAllFilesFast();
    $videos = [];
    
    $tutorialVideo = getTutorialVideo();
    $videos[] = $tutorialVideo;
    
    $otherVideos = [];
    
    foreach ($allFiles as $file) {
        if ($file['type'] !== 'json') {
            continue;
        }
        
        try {
            $fileVideos = parseJsonFile($file['path']);
            if (!empty($fileVideos)) {
                foreach ($fileVideos as $video) {
                    $otherVideos[] = formatVideoItem($video);
                }
            }
        } catch (Exception $e) {
            continue;
        }
    }
    
    $pageSize = 10;
    $otherVideosCount = count($otherVideos);
    
    if ($otherVideosCount > 0) {
        $startIndex = ($page - 1) * ($pageSize - 1);
        
        if ($startIndex < $otherVideosCount) {
            $selectedVideos = array_slice($otherVideos, $startIndex, $pageSize - 1);
            $videos = array_merge($videos, $selectedVideos);
        }
    }
    
    return $videos;
}

function getHome() {
    $categories = getCategoriesFast();
    
    if (empty($categories)) {
        return ['error' => 'No files found in json or wj folders'];
    }
    
    return [
        'class' => $categories
    ];
}

function getCategoriesFast() {
    static $categories = null;
    
    if ($categories === null) {
        $allFiles = getAllFilesFast();
        $categories = [];
        
        // 统计各类文件数量
        $jsonCount = 0;
        $txtCount = 0;
        $m3uCount = 0;
        $dbCount = 0;
        $audioCount = 0;
        $videoCount = 0;
        $imageCount = 0;
        
        foreach ($allFiles as $file) {
            switch ($file['type']) {
                case 'json': $jsonCount++; break;
                case 'txt': $txtCount++; break;
                case 'm3u': $m3uCount++; break;
                case 'db': $dbCount++; break;
            }
        }
        
        // 统计媒体文件数量
        if (isset($GLOBALS['media_files'])) {
            $audioCount = count($GLOBALS['media_files']['audio']);
            $videoCount = count($GLOBALS['media_files']['video']);
            $imageCount = count($GLOBALS['media_files']['image']);
        }
        
        $totalFiles = count($allFiles);
        $totalMedia = $audioCount + $videoCount + $imageCount;
        
        // 1. 推荐分类
        $categories[] = [
            'type_id' => 'recommend',
            'type_name' => '🔥 热门推荐 (扫描到' . $totalFiles . '个数据文件)',
            'type_file' => 'recommend',
            'source_path' => 'recommend',
            'source_type' => 'recommend',
            'file_size' => 'JSON:' . $jsonCount . ' TXT:' . $txtCount . ' M3U:' . $m3uCount . ' DB:' . $dbCount
        ];
        
        // 2. 媒体库分类
        if ($totalMedia > 0) {
            $categories[] = [
                'type_id' => 'media_library',
                'type_name' => '📷 媒体库 (' . $totalMedia . '个媒体文件)',
                'type_file' => 'media_library',
                'source_path' => 'media_library',
                'source_type' => 'media_library',
                'file_size' => '音频:' . $audioCount . ' 视频:' . $videoCount . ' 图片:' . $imageCount
            ];
        }
        
        // 3. 原有的数据文件分类
        foreach ($allFiles as $index => $file) {
            $fileType = '';
            $typeIcon = '';
            
            switch ($file['type']) {
                case 'json':
                    $fileType = '[JSON] ';
                    $typeIcon = '📊 ';
                    break;
                case 'txt':
                    $fileType = '[TXT] ';
                    $typeIcon = '📄 ';
                    break;
                case 'm3u':
                    $fileType = '[M3U] ';
                    $typeIcon = '📺 ';
                    break;
                case 'db':
                    $fileType = '[数据库] ';
                    $typeIcon = '🗃️ ';
                    break;
            }
            
            $fileSize = $file['size'] ? round($file['size'] / 1024, 1) . 'KB' : '未知';
            
            $categories[] = [
                'type_id' => (string)($index + 1000),
                'type_name' => $typeIcon . $fileType . $file['filename'],
                'type_file' => $file['name'],
                'source_path' => $file['path'],
                'source_type' => $file['type'],
                'file_size' => $fileSize
            ];
        }
        
        if (empty($allFiles) && $totalMedia === 0) {
            $categories[] = [
                'type_id' => '1000',
                'type_name' => '❓ 未找到任何文件',
                'type_file' => 'empty',
                'source_path' => 'empty',
                'source_type' => 'empty',
                'file_size' => '请添加文件'
            ];
        }
    }
    
    return $categories;
}

function getMediaLibraryCategory($page) {
    if (!isset($GLOBALS['media_files'])) {
        return ['error' => '媒体文件未初始化'];
    }
    
    $mediaFiles = $GLOBALS['media_files'];
    $allMedia = [];
    
    // 处理音频文件
    foreach ($mediaFiles['audio'] as $audio) {
        $allMedia[] = [
            'vod_id' => 'audio_' . md5($audio['path']),
            'vod_name' => '🎵 ' . $audio['filename'],
            'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
            'vod_remarks' => '音频 · ' . strtoupper($audio['type']),
            'vod_year' => date('Y'),
            'vod_area' => '本地文件',
            'vod_content' => '音频文件: ' . $audio['name'] . "\n文件大小: " . round($audio['size'] / 1024, 1) . 'KB',
            'vod_play_from' => '本地音频',
            'vod_play_url' => '播放$' . $audio['path']
        ];
    }
    
    // 处理视频文件
    foreach ($mediaFiles['video'] as $video) {
        $allMedia[] = [
            'vod_id' => 'video_' . md5($video['path']),
            'vod_name' => '🎬 ' . $video['filename'],
            'vod_pic' => 'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg',
            'vod_remarks' => '视频 · ' . strtoupper($video['type']),
            'vod_year' => date('Y'),
            'vod_area' => '本地文件',
            'vod_content' => '视频文件: ' . $video['name'] . "\n文件大小: " . round($video['size'] / 1024 / 1024, 1) . 'MB',
            'vod_play_from' => '本地视频',
            'vod_play_url' => '播放$' . $video['path']
        ];
    }
    
    // 处理图片文件
    foreach ($mediaFiles['image'] as $image) {
        $allMedia[] = [
            'vod_id' => 'image_' . md5($image['path']),
            'vod_name' => '🖼️ ' . $image['filename'],
            'vod_pic' => $image['path'],
            'vod_remarks' => '图片 · ' . strtoupper($image['type']),
            'vod_year' => date('Y'),
            'vod_area' => '本地文件',
            'vod_content' => '图片文件: ' . $image['name'] . "\n文件大小: " . round($image['size'] / 1024, 1) . 'KB',
            'vod_play_from' => '本地图片',
            'vod_play_url' => '查看$' . $image['path']
        ];
    }
    
    if (empty($allMedia)) {
        return ['error' => '媒体库中没有找到媒体文件'];
    }
    
    // 分页处理
    $pageSize = 10;
    $total = count($allMedia);
    $pageCount = ceil($total / $pageSize);
    $currentPage = intval($page);
    
    if ($currentPage < 1) $currentPage = 1;
    if ($currentPage > $pageCount) $currentPage = $pageCount;
    
    $start = ($currentPage - 1) * $pageSize;
    $pagedMedia = array_slice($allMedia, $start, $pageSize);
    
    $formattedMedia = [];
    foreach ($pagedMedia as $media) {
        $formattedMedia[] = formatVideoItem($media);
    }
    
    return [
        'page' => $currentPage,
        'pagecount' => $pageCount,
        'limit' => $pageSize,
        'total' => $total,
        'list' => $formattedMedia
    ];
}

/**
 * 解析SQLite数据库文件内容
 */
function parseDbFile($filePath) {
    if (!file_exists($filePath)) {
        return ['error' => '数据库文件不存在: ' . $filePath];
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
        
        $defaultImages = [
            'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
            'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
            'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
        ];
        
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
                
                $selectSql = "SELECT " . implode(', ', $selectColumns) . " FROM $table LIMIT 100";
                
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
                    if (count($videos) >= 100) break 2;
                }
            }
        }
        
        $db = null; // 关闭连接
        
        return $videos;
        
    } catch (PDOException $e) {
        return ['error' => '数据库读取失败: ' . $e->getMessage()];
    }
}

function parseJsonFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $fileSize = @filesize($filePath);
    if ($fileSize > 50 * 1024 * 1024) {
        return parseLargeJsonFile($filePath);
    }
    
    $jsonContent = @file_get_contents($filePath);
    if ($jsonContent === false) {
        return [];
    }
    
    if (substr($jsonContent, 0, 3) == "\xEF\xBB\xBF") {
        $jsonContent = substr($jsonContent, 3);
    }
    
    $data = json_decode($jsonContent, true);
    if (!$data || !isset($data['list']) || !is_array($data['list'])) {
        return [];
    }
    
    return $data['list'];
}

function parseLargeJsonFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $content = '';
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return [];
    }
    
    $content = fread($handle, 102400);
    fclose($handle);
    
    if (empty($content)) {
        return [];
    }
    
    if (substr($content, 0, 3) == "\xEF\xBB\xBF") {
        $content = substr($content, 3);
    }
    
    $listPos = strpos($content, '"list":');
    if ($listPos === false) {
        return [];
    }
    
    $listContent = substr($content, $listPos + 6);
    $braceCount = 0;
    $inString = false;
    $escape = false;
    $result = '';
    
    for ($i = 0; $i < strlen($listContent); $i++) {
        $char = $listContent[$i];
        
        if ($escape) {
            $escape = false;
            continue;
        }
        
        if ($char === '\\') {
            $escape = true;
            continue;
        }
        
        if ($char === '"' && !$escape) {
            $inString = !$inString;
        }
        
        if (!$inString) {
            if ($char === '[') {
                $braceCount++;
            } elseif ($char === ']') {
                $braceCount--;
            }
        }
        
        $result .= $char;
        
        if ($braceCount === 0 && $char === ']') {
            break;
        }
    }
    
    $listData = json_decode('[' . $result, true);
    if (!is_array($listData)) {
        return [];
    }
    
    return $listData;
}

function parseTxtFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $fileSize = @filesize($filePath);
    if ($fileSize > 5 * 1024 * 1024) {
        return parseLargeTxtFile($filePath);
    }
    
    $content = @file_get_contents($filePath);
    if ($content === false) {
        return [];
    }
    
    if (substr($content, 0, 3) == "\xEF\xBB\xBF") {
        $content = substr($content, 3);
    }
    
    $lines = explode("\n", $content);
    $videos = [];
    $videoCount = 0;
    
    $defaultImages = [
        'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
    ];
    
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') continue;
        
        $commaPos = strpos($line, ',');
        if ($commaPos === false) continue;
        
        $name = trim(substr($line, 0, $commaPos));
        $url = trim(substr($line, $commaPos + 1));
        
        if (empty($name) || empty($url)) continue;
        if (strpos($url, 'http') !== 0) continue;
        
        $imageIndex = $videoCount % count($defaultImages);
        
        $videos[] = [
            'vod_id' => 'txt_' . md5($filePath) . '_' . $videoCount,
            'vod_name' => $name,
            'vod_pic' => $defaultImages[$imageIndex],
            'vod_remarks' => 'HD',
            'vod_year' => date('Y'),
            'vod_area' => '中国大陆',
            'vod_content' => '《' . $name . '》的精彩内容',
            'vod_play_from' => '在线播放',
            'vod_play_url' => '正片$' . $url
        ];
        
        $videoCount++;
        if ($videoCount >= 100) break;
    }
    
    return $videos;
}

function parseLargeTxtFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return [];
    }
    
    $videos = [];
    $videoCount = 0;
    $defaultImages = [
        'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
    ];
    
    while (($line = fgets($handle)) !== false && $videoCount < 50) {
        $line = trim($line);
        if ($line === '' || $line[0] === '#') continue;
        
        $commaPos = strpos($line, ',');
        if ($commaPos === false) continue;
        
        $name = trim(substr($line, 0, $commaPos));
        $url = trim(substr($line, $commaPos + 1));
        
        if (empty($name) || empty($url)) continue;
        if (strpos($url, 'http') !== 0) continue;
        
        $imageIndex = $videoCount % count($defaultImages);
        
        $videos[] = [
            'vod_id' => 'txt_' . md5($filePath) . '_' . $videoCount,
            'vod_name' => $name,
            'vod_pic' => $defaultImages[$imageIndex],
            'vod_remarks' => 'HD',
            'vod_year' => date('Y'),
            'vod_area' => '中国大陆',
            'vod_content' => '《' . $name . '》的精彩内容',
            'vod_play_from' => '在线播放',
            'vod_play_url' => '正片$' . $url
        ];
        
        $videoCount++;
    }
    
    fclose($handle);
    return $videos;
}

function parseM3uFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $content = @file_get_contents($filePath);
    if ($content === false) {
        return [];
    }
    
    $lines = explode("\n", $content);
    $videos = [];
    $videoCount = 0;
    $currentName = '';
    
    $defaultImages = [
        'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
    ];
    
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '') continue;
        
        if (strpos($line, '#EXTINF:') === 0) {
            $parts = explode(',', $line);
            if (count($parts) > 1) {
                $currentName = trim($parts[1]);
                
                $tvgLogo = '';
                if (preg_match('/tvg-logo="([^"]*)"/', $line, $matches)) {
                    $tvgLogo = $matches[1];
                }
            }
        } elseif (strpos($line, 'http') === 0 && !empty($currentName)) {
            $imageIndex = $videoCount % count($defaultImages);
            $imageUrl = !empty($tvgLogo) ? $tvgLogo : $defaultImages[$imageIndex];
            
            $videos[] = [
                'vod_id' => 'm3u_' . md5($filePath) . '_' . $videoCount,
                'vod_name' => $currentName,
                'vod_pic' => $imageUrl,
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $currentName . '直播频道',
                'vod_play_from' => '直播源',
                'vod_play_url' => '直播$' . $line
            ];
            
            $videoCount++;
            $currentName = '';
            $tvgLogo = '';
            if ($videoCount >= 100) break;
        }
    }
    
    return $videos;
}

function getCategory($tid, $page) {
    $categories = getCategoriesFast();
    
    if (empty($categories)) {
        return ['error' => 'No categories found'];
    }
    
    if ($tid === 'recommend') {
        return getRecommendCategory($page);
    }
    
    // 新增媒体库处理
    if ($tid === 'media_library') {
        return getMediaLibraryCategory($page);
    }
    
    $targetCategory = null;
    foreach ($categories as $category) {
        if ($category['type_id'] === $tid) {
            $targetCategory = $category;
            break;
        }
    }
    
    if (!$targetCategory) {
        return ['error' => 'Category not found'];
    }
    
    if ($targetCategory['source_type'] === 'empty') {
        return [
            'page' => 1,
            'pagecount' => 1,
            'limit' => 10,
            'total' => 0,
            'list' => []
        ];
    }
    
    $categoryVideos = [];
    
    if (file_exists($targetCategory['source_path'])) {
        switch ($targetCategory['source_type']) {
            case 'json':
                $categoryVideos = parseJsonFile($targetCategory['source_path']);
                break;
            case 'txt':
                $categoryVideos = parseTxtFile($targetCategory['source_path']);
                break;
            case 'm3u':
                $categoryVideos = parseM3uFile($targetCategory['source_path']);
                break;
            case 'db':
                $categoryVideos = parseDbFile($targetCategory['source_path']);
                break;
        }
    }
    
    // 检查是否是错误信息
    if (isset($categoryVideos['error'])) {
        return ['error' => $categoryVideos['error']];
    }
    
    if (empty($categoryVideos)) {
        return ['error' => 'No videos found in: ' . $targetCategory['type_name']];
    }
    
    $pageSize = 10;
    $total = count($categoryVideos);
    $pageCount = ceil($total / $pageSize);
    $currentPage = intval($page);
    
    if ($currentPage < 1) $currentPage = 1;
    if ($currentPage > $pageCount) $currentPage = $pageCount;
    
    $start = ($currentPage - 1) * $pageSize;
    $pagedVideos = array_slice($categoryVideos, $start, $pageSize);
    
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

function getRecommendCategory($page) {
    $recommendVideos = getRecommendVideos($page);
    
    if (empty($recommendVideos)) {
        return ['error' => 'No recommend videos found'];
    }
    
    $allFiles = getAllFilesFast();
    $totalVideos = 1;
    
    foreach ($allFiles as $file) {
        if ($file['type'] === 'json') {
            try {
                $fileVideos = parseJsonFile($file['path']);
                $totalVideos += count($fileVideos);
            } catch (Exception $e) {
                continue;
            }
        }
    }
    
    $pageSize = 10;
    $pageCount = ceil($totalVideos / ($pageSize - 1));
    $currentPage = intval($page);
    
    if ($currentPage < 1) $currentPage = 1;
    if ($currentPage > $pageCount) $currentPage = $pageCount;
    
    $formattedVideos = [];
    foreach ($recommendVideos as $video) {
        $formattedVideos[] = formatVideoItem($video);
    }
    
    return [
        'page' => $currentPage,
        'pagecount' => $pageCount,
        'limit' => $pageSize,
        'total' => $totalVideos,
        'list' => $formattedVideos
    ];
}

function formatVideoItem($video) {
    return [
        'vod_id' => $video['vod_id'] ?? '',
        'vod_name' => $video['vod_name'] ?? '',
        'vod_pic' => $video['vod_pic'] ?? '',
        'vod_remarks' => $video['vod_remarks'] ?? 'HD',
        'vod_year' => $video['vod_year'] ?? '',
        'vod_area' => $video['vod_area'] ?? ''
    ];
}

function getDetail($ids) {
    $idArray = explode(',', $ids);
    $result = [];
    
    foreach ($idArray as $id) {
        $video = findVideoByIdLazy($id);
        if ($video) {
            $result[] = formatVideoDetail($video);
        } else {
            if (strpos($id, 'tutorial_') === 0) {
                $result[] = getTutorialVideo();
            } elseif (strpos($id, 'audio_') === 0 || strpos($id, 'video_') === 0 || strpos($id, 'image_') === 0) {
                // 媒体文件详情
                $result[] = getMediaFileDetail($id);
            } else {
                $result[] = [
                    'vod_id' => $id,
                    'vod_name' => '视频 ' . $id,
                    'vod_pic' => 'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
                    'vod_remarks' => 'HD',
                    'vod_content' => '视频详情内容',
                    'vod_play_from' => '在线播放',
                    'vod_play_url' => '正片$https://d6.qyshare.store/s/TBVWTxUNFQcFUQQHKFCVA50wKFCVA50FGlQEKFCVA50QIaKFCVA501EHVhoOD1EBGgEBUwBRKFCVA50VFRBVYPDxUbFVhERH9YREMVDRVYREQZRk5CWRlYRVKFCVA50VGxVYRER8Uk4VDRVCR1tYVlMYBQcFKFCVA50hgGBxgFKFCVA50RgFUgJWDgMGUxoHUQ9SGgNWU1IaDlFVDxpRBwVVUQcGKFCVA50Q8KFCVA50BQ4ZVV5ZFRsVVlQVDRUGDlMFBFQGBBoBKFCVA50wYEGgNRKFCVA50w4aDlICBhoPBw8FVQ8PVgNWVVIVGxVZVlpSFQ0VKFCVA50mgBBKFCVA50QBKFCVA50Q4DDgcEKFCVA50wYEKFCVA50QKFCVA50KFCVA50KFCVA50gQHGVpHKFCVA50xUbFVRYWUNSWUNjTkdSFQ0VQV5TUlgYWkcDFRsVVlMVDRUPBwVWBQUBVRoEKFCVA501IEGgMDUgEaVQQFURoBBgcCDgYOVVMEDlIVSg=='
                ];
            }
        }
    }
    
    return ['list' => $result];
}

function getMediaFileDetail($id) {
    if (!isset($GLOBALS['media_files'])) {
        return [
            'vod_id' => $id,
            'vod_name' => '媒体文件',
            'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
            'vod_remarks' => '未知',
            'vod_content' => '媒体文件详情加载失败',
            'vod_play_from' => '本地媒体',
            'vod_play_url' => '播放$'
        ];
    }
    
    $mediaFiles = $GLOBALS['media_files'];
    $allMedia = [];
    
    // 合并所有媒体文件
    $allMedia = array_merge($mediaFiles['audio'], $mediaFiles['video'], $mediaFiles['image']);
    
    foreach ($allMedia as $media) {
        $mediaId = '';
        if (strpos($id, 'audio_') === 0) {
            $mediaId = 'audio_' . md5($media['path']);
        } elseif (strpos($id, 'video_') === 0) {
            $mediaId = 'video_' . md5($media['path']);
        } elseif (strpos($id, 'image_') === 0) {
            $mediaId = 'image_' . md5($media['path']);
        }
        
        if ($mediaId === $id) {
            $fileType = strtoupper($media['type']);
            $fileSize = $media['size'] ? round($media['size'] / 1024, 1) . 'KB' : '未知大小';
            
            if (strpos($id, 'audio_') === 0) {
                return [
                    'vod_id' => $id,
                    'vod_name' => '🎵 ' . $media['filename'],
                    'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
                    'vod_remarks' => '音频 · ' . $fileType,
                    'vod_year' => date('Y'),
                    'vod_area' => '本地文件',
                    'vod_content' => "音频文件详情\n\n文件名: " . $media['name'] . "\n文件类型: " . $fileType . "\n文件大小: " . $fileSize . "\n文件路径: " . $media['path'],
                    'vod_play_from' => '本地音频',
                    'vod_play_url' => '播放$' . $media['path']
                ];
            } elseif (strpos($id, 'video_') === 0) {
                return [
                    'vod_id' => $id,
                    'vod_name' => '🎬 ' . $media['filename'],
                    'vod_pic' => 'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg',
                    'vod_remarks' => '视频 · ' . $fileType,
                    'vod_year' => date('Y'),
                    'vod_area' => '本地文件',
                    'vod_content' => "视频文件详情\n\n文件名: " . $media['name'] . "\n文件类型: " . $fileType . "\n文件大小: " . $fileSize . "\n文件路径: " . $media['path'],
                    'vod_play_from' => '本地视频',
                    'vod_play_url' => '播放$' . $media['path']
                ];
            } elseif (strpos($id, 'image_') === 0) {
                return [
                    'vod_id' => $id,
                    'vod_name' => '🖼️ ' . $media['filename'],
                    'vod_pic' => $media['path'],
                    'vod_remarks' => '图片 · ' . $fileType,
                    'vod_year' => date('Y'),
                    'vod_area' => '本地文件',
                    'vod_content' => "图片文件详情\n\n文件名: " . $media['name'] . "\n文件类型: " . $fileType . "\n文件大小: " . $fileSize . "\n文件路径: " . $media['path'],
                    'vod_play_from' => '本地图片',
                    'vod_play_url' => '查看$' . $media['path']
                ];
            }
        }
    }
    
    return [
        'vod_id' => $id,
        'vod_name' => '媒体文件未找到',
        'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'vod_remarks' => '错误',
        'vod_content' => '找不到对应的媒体文件',
        'vod_play_from' => '本地媒体',
        'vod_play_url' => '播放$'
    ];
}

function findVideoByIdLazy($id) {
    $allFiles = getAllFilesFast();
    
    if (strpos($id, 'txt_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 3) {
            $fileHash = $parts[1];
            $videoIndex = $parts[2];
            
            foreach ($allFiles as $file) {
                if ($file['type'] === 'txt' && md5($file['path']) === $fileHash) {
                    $videos = parseTxtFile($file['path']);
                    if (isset($videos[$videoIndex])) {
                        return $videos[$videoIndex];
                    }
                }
            }
        }
    } elseif (strpos($id, 'm3u_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 3) {
            $fileHash = $parts[1];
            $videoIndex = $parts[2];
            
            foreach ($allFiles as $file) {
                if ($file['type'] === 'm3u' && md5($file['path']) === $fileHash) {
                    $videos = parseM3uFile($file['path']);
                    if (isset($videos[$videoIndex])) {
                        return $videos[$videoIndex];
                    }
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
                $defaultImages = [
                    'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
                    'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
                    'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
                ];
                
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

function search($keyword, $page) {
    if (empty($keyword)) {
        return ['error' => 'Keyword is required'];
    }
    
    $searchResults = [];
    $allFiles = getAllFilesFast();
    
    $searchLimit = 500;
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
                
                if (count($searchResults) >= 50) break 2;
            }
        }
        
        $searchedFiles++;
    }
    
    // 搜索媒体文件
    if (isset($GLOBALS['media_files'])) {
        $mediaFiles = $GLOBALS['media_files'];
        $allMedia = array_merge($mediaFiles['audio'], $mediaFiles['video'], $mediaFiles['image']);
        
        foreach ($allMedia as $media) {
            if (stripos($media['filename'], $keyword) !== false || stripos($media['name'], $keyword) !== false) {
                if (in_array($media['type'], ['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg', 'wma'])) {
                    $searchResults[] = [
                        'vod_id' => 'audio_' . md5($media['path']),
                        'vod_name' => '🎵 ' . $media['filename'],
                        'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
                        'vod_remarks' => '音频',
                        'vod_year' => date('Y'),
                        'vod_area' => '本地文件'
                    ];
                } elseif (in_array($media['type'], ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp'])) {
                    $searchResults[] = [
                        'vod_id' => 'video_' . md5($media['path']),
                        'vod_name' => '🎬 ' . $media['filename'],
                        'vod_pic' => 'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg',
                        'vod_remarks' => '视频',
                        'vod_year' => date('Y'),
                        'vod_area' => '本地文件'
                    ];
                }
                
                if (count($searchResults) >= 50) break;
            }
        }
    }
    
    if (empty($searchResults)) {
        return ['error' => 'No search results'];
    }
    
    $pageSize = 10;
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

function formatVideoDetail($video) {
    return [
        'vod_id' => $video['vod_id'] ?? '',
        'vod_name' => $video['vod_name'] ?? '',
        'vod_pic' => $video['vod_pic'] ?? '',
        'vod_remarks' => $video['vod_remarks'] ?? 'HD',
        'vod_year' => $video['vod_year'] ?? '',
        'vod_area' => $video['vod_area'] ?? '',
        'vod_director' => $video['vod_director'] ?? '',
        'vod_actor' => $video['vod_actor'] ?? '',
        'vod_content' => $video['vod_content'] ?? '',
        'vod_play_from' => $video['vod_play_from'] ?? 'default',
        'vod_play_url' => $video['vod_play_url'] ?? ''
    ];
}

function getPlay($flag, $id) {
    if (strpos($id, 'tutorial_') === 0) {
        return [
            'parse' => 0,
            'playUrl' => '',
            'url' => ''
        ];
    }
    
    // 支持直接播放本地媒体文件路径
    if (file_exists($id)) {
        return [
            'parse' => 0,
            'playUrl' => '',
            'url' => $id
        ];
    }
    
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $id
    ];
}
?>
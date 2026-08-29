<?php
/**
 * TVBox PHP 爬虫脚本 - 三合一懒加载版本（优化超时和大文件处理）
 * 支持JSON、TXT、M3U文件
 * 🔥推荐分类包含JSON内容和教程示例
 */

// 获取请求参数
$ac = $_GET['ac'] ?? 'detail';
$t = $_GET['t'] ?? '';
$pg = $_GET['pg'] ?? '1';
$ids = $_GET['ids'] ?? '';
$wd = $_GET['wd'] ?? '';
$flag = $_GET['flag'] ?? '';
$id = $_GET['id'] ?? '';

// 设置响应头为 JSON
header('Content-Type: application/json; charset=utf-8');

// 性能优化 - 增加超时时间，特别是大文件处理
@set_time_limit(30); // 增加到30秒

// 根据不同 action 返回数据
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

/**
 * 快速扫描目录 - 支持多种文件类型
 */
function scanDirectoryFast($dir, $types, $maxDepth = 2, $currentDepth = 0) {
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
            $subFiles = scanDirectoryFast($path . '/', $types, $maxDepth, $currentDepth + 1);
            $files = array_merge($files, $subFiles);
        } else {
            $extension = pathinfo($path, PATHINFO_EXTENSION);
            if (in_array($extension, $types)) {
                $fileSize = @filesize($path);
                // 跳过过大的文件（超过500MB），避免内存溢出
                if ($fileSize > 500 * 1024 * 1024) {
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

/**
 * 获取文件列表 - 支持JSON、TXT、M3U
 */
function getAllFilesFast() {
    static $allFiles = null;
    
    if ($allFiles === null) {
        $allFiles = [];
        
        // 扫描JSON文件
        $jsonFiles = scanDirectoryFast('/storage/emulated/0/TVBoxPhpJar/江湖/wj/', ['json']);
        // 扫描TXT文件
        $txtFiles = scanDirectoryFast('/storage/emulated/0/TVBoxPhpJar/江湖/wj/', ['txt']);
        // 扫描M3U文件
        $m3uFiles = array_merge(
            scanDirectoryFast('/storage/emulated/0/TVBoxPhpJar/江湖/wj/', ['m3u']),
            scanDirectoryFast('/storage/emulated/0/TVBoxPhpJar/江湖/wj/', ['m3u'])
        );
        
        $allFiles = array_merge($jsonFiles, $txtFiles, $m3uFiles);
    }
    
    return $allFiles;
}

/**
 * 获取分类列表 - 包含🔥推荐分类和文件分类
 */
function getCategoriesFast() {
    static $categories = null;
    
    if ($categories === null) {
        $allFiles = getAllFilesFast();
        $categories = [];
        
        // 统计各类文件数量
        $jsonCount = 0;
        $txtCount = 0;
        $m3uCount = 0;
        
        foreach ($allFiles as $file) {
            switch ($file['type']) {
                case 'json': $jsonCount++; break;
                case 'txt': $txtCount++; break;
                case 'm3u': $m3uCount++; break;
            }
        }
        
        $totalFiles = count($allFiles);
        
        // 添加🔥推荐分类（包含JSON和教程）- 显示文件统计
        $categories[] = [
            'type_id' => 'recommend',
            'type_name' => '🔥 热门推荐 (扫描到' . $totalFiles . '个文件)',
            'type_file' => 'recommend',
            'source_path' => 'recommend',
            'source_type' => 'recommend',
            'file_size' => 'JSON:' . $jsonCount . ' TXT:' . $txtCount . ' M3U:' . $m3uCount
        ];
        
        // 添加文件分类 - 带图标标识
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
        
        // 如果没有找到任何文件，添加提示分类
        if (empty($allFiles)) {
            $categories[] = [
                'type_id' => '1000',
                'type_name' => '❓ 未找到媒体文件',
                'type_file' => 'empty',
                'source_path' => 'empty',
                'source_type' => 'empty',
                'file_size' => '请添加文件'
            ];
        }
    }
    
    return $categories;
}

/**
 * 获取所有推荐视频 - 懒加载版本（包含JSON和教程示例）
 */
function getAllRecommendVideos() {
    static $allVideos = null;
    
    if ($allVideos === null) {
        $allVideos = [];
        $allFiles = getAllFilesFast();
        
        // 首先添加教程示例视频（置顶）- 只保留一个综合教程
        $tutorialVideos = getTutorialVideos();
        foreach ($tutorialVideos as $tutorial) {
            $allVideos[] = $tutorial;
        }
        
        // 处理JSON文件
        foreach ($allFiles as $file) {
            if ($file['type'] !== 'json') {
                continue; // 跳过TXT和M3U文件
            }
            
            try {
                $videos = parseJsonFile($file['path']);
                if (!empty($videos)) {
                    // 限制每个文件最多取15个视频，避免内存过大
                    $limitedVideos = array_slice($videos, 0, 15);
                    foreach ($limitedVideos as $video) {
                        $allVideos[] = formatVideoItem($video);
                    }
                }
            } catch (Exception $e) {
                // 忽略单个文件解析错误，继续处理其他文件
                error_log("解析JSON文件失败: " . $file['path'] . " - " . $e->getMessage());
                continue;
            }
        }
        
        // 如果除了教程没有其他视频，添加一些示例视频
        if (count($allVideos) <= count($tutorialVideos)) {
            $sampleVideos = getSampleVideos();
            foreach ($sampleVideos as $sample) {
                $allVideos[] = $sample;
            }
        }
        
        // 随机打乱视频顺序（但保持教程视频在前）
        $tutorials = array_slice($allVideos, 0, count($tutorialVideos));
        $otherVideos = array_slice($allVideos, count($tutorialVideos));
        shuffle($otherVideos);
        $allVideos = array_merge($tutorials, $otherVideos);
    }
    
    return $allVideos;
}

/**
 * 获取教程示例视频（置顶显示）- 合并为一个综合教程
 */
function getTutorialVideos() {
    return [
        [
            'vod_id' => 'tutorial_1',
            'vod_name' => '📚 TVBox 使用教程大全',
            'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
            'vod_remarks' => '完整指南',
            'vod_year' => '2024',
            'vod_area' => '使用教程',
            'vod_content' => "📱 TVBox 完整使用教程\n\n" .
                            "🎯 文件放置位置：\n" .
                            "   • JSON文件：/storage/emulated/0/lz/json/\n" .
                            "   • TXT文件：/storage/emulated/0/lz/wj/\n" .
                            "   • M3U文件：可放在以上任意目录\n\n" .
                            "📝 文件格式要求：\n" .
                            "   • JSON：标准TVBox格式，包含list数组\n" .
                            "   • TXT：视频名称,视频URL 格式（一行一个）\n" .
                            "   • M3U：标准直播源格式\n\n" .
                            "🔥 推荐分类说明：\n" .
                            "   • 随机显示所有JSON文件的内容\n" .
                            "   • 首页显示扫描到的文件数量统计\n" .
                            "   • 支持翻页浏览\n\n" .
                            "❓ 常见问题解答：\n" .
                            "   Q: 为什么推荐分类没有内容？\n" .
                            "   A: 请检查是否在指定目录放置了JSON格式的媒体文件\n\n" .
                            "   Q: 大文件加载超时怎么办？\n" .
                            "   A: 系统已优化大文件处理，建议将大文件分割成小文件\n\n" .
                            "   Q: 搜索不到内容？\n" .
                            "   A: 确保文件格式正确，且包含视频名称信息\n\n" .
                            "   Q: 如何确认文件被正确识别？\n" .
                            "   A: 在首页查看文件分类列表，确认文件显示正常\n\n" .
                            "⚡ 性能优化建议：\n" .
                            "   • 单个JSON文件建议不超过30MB\n" .
                            "   • 将大文件按分类分割成多个小文件\n" .
                            "   • 使用压缩后的图片链接\n" .
                            "   • 定期清理不再使用的文件\n\n" .
                            "🔍 搜索功能：\n" .
                            "   • 支持关键词搜索所有文件内容\n" .
                            "   • 自动限制搜索范围，提高性能\n" .
                            "   • 支持分页显示搜索结果",
            'vod_play_from' => '教程',
            'vod_play_url' => '教程$https://d6.qyshare.store/s/TBVWTxUNFQcFUQQHKFCVA50wKFCVA50FGlQEKFCVA50QIaKFCVA501EHVhoOD1EBGgEBUwBRKFCVA50VFRBVYPDxUbFVhERH9YREMVDRVYREQZRk5CWRlYRVKFCVA50VGxVYRER8Uk4VDRVCR1tYVlMYBQcFKFCVA50hgGBxgFKFCVA50RgFUgJWDgMGUxoHUQ9SGgNWU1IaDlFVDxpRBwVVUQcGKFCVA50Q8KFCVA50BQ4ZVV5ZFRsVVlQVDRUGDlMFBFQGBBoBKFCVA50wYEGgNRKFCVA50w4aDlICBhoPBw8FVQ8PVgNWVVIVGxVZVlpSFQ0VKFCVA50mgBBKFCVA50QBKFCVA50Q4DDgcEKFCVA50wYEKFCVA50QKFCVA50KFCVA50KFCVA50gQHGVpHKFCVA50xUbFVRYWUNSWUNjTkdSFQ0VQV5TUlgYWkcDFRsVVlMVDRUPBwVWBQUBVRoEKFCVA501IEGgMDUgEaVQQFURoBBgcCDgYOVVMEDlIVSg=='
        ]
    ];
}

/**
 * 获取示例视频（当没有真实文件时显示）
 */
function getSampleVideos() {
    return [
        [
            'vod_id' => 'sample_1',
            'vod_name' => '🎬 示例电影：动作大片',
            'vod_pic' => 'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
            'vod_remarks' => 'HD',
            'vod_year' => '2024',
            'vod_area' => '示例'
        ],
        [
            'vod_id' => 'sample_2',
            'vod_name' => '📺 示例电视剧：悬疑推理',
            'vod_pic' => 'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
            'vod_remarks' => '更新至第10集',
            'vod_year' => '2024',
            'vod_area' => '示例'
        ],
        [
            'vod_id' => 'sample_3',
            'vod_name' => '🌍 示例纪录片：自然风光',
            'vod_pic' => 'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg',
            'vod_remarks' => '4K',
            'vod_year' => '2023',
            'vod_area' => '示例'
        ],
        [
            'vod_id' => 'sample_4',
            'vod_name' => '🎵 示例音乐：流行金曲',
            'vod_pic' => 'https://img1.doubanio.com/view/photo/m_ratio_poster/public/p2881322276.jpg',
            'vod_remarks' => '音乐',
            'vod_year' => '2024',
            'vod_area' => '示例'
        ],
        [
            'vod_id' => 'sample_5',
            'vod_name' => '⚽ 示例体育：精彩赛事',
            'vod_pic' => 'https://img2.doubanio.com/view/photo/m_ratio_poster/public/p2881322277.jpg',
            'vod_remarks' => '直播',
            'vod_year' => '2024',
            'vod_area' => '示例'
        ]
    ];
}

/**
 * 首页数据 - 只显示分类，不显示推荐视频
 */
function getHome() {
    $categories = getCategoriesFast();
    
    if (empty($categories)) {
        return ['error' => 'No files found in json or wj folders'];
    }
    
    // 首页只显示分类，没有任何视频内容
    return [
        'class' => $categories
    ];
}

/**
 * 解析JSON文件内容 - 优化大文件处理
 */
function parseJsonFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    // 检查文件大小，大文件使用流式读取
    $fileSize = @filesize($filePath);
    if ($fileSize > 10 * 1024 * 1024) { // 超过1MB
        return parseLargeJsonFile($filePath);
    }
    
    $jsonContent = @file_get_contents($filePath);
    if ($jsonContent === false) {
        return [];
    }
    
    // 处理BOM头
    if (substr($jsonContent, 0, 3) == "\xEF\xBB\xBF") {
        $jsonContent = substr($jsonContent, 3);
    }
    
    $data = json_decode($jsonContent, true);
    if (!$data || !isset($data['list']) || !is_array($data['list'])) {
        return [];
    }
    
    return $data['list'];
}

/**
 * 解析大JSON文件 - 使用流式处理避免内存溢出
 */
function parseLargeJsonFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $content = '';
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return [];
    }
    
    // 读取前100KB内容，通常足够获取视频列表
    $content = fread($handle, 102400);
    fclose($handle);
    
    if (empty($content)) {
        return [];
    }
    
    // 处理BOM头
    if (substr($content, 0, 3) == "\xEF\xBB\xBF") {
        $content = substr($content, 3);
    }
    
    // 尝试找到list数组的开始位置
    $listPos = strpos($content, '"list":');
    if ($listPos === false) {
        return [];
    }
    
    // 提取list数组部分
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
    
    // 解析提取的list数组
    $listData = json_decode('[' . $result, true);
    if (!is_array($listData)) {
        return [];
    }
    
    return $listData;
}

/**
 * 解析TXT文件内容 - 优化大文件处理
 */
function parseTxtFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    // 检查文件大小，大文件使用流式读取
    $fileSize = @filesize($filePath);
    if ($fileSize > 1 * 1024 * 1024) { // 超过1MB
        return parseLargeTxtFile($filePath);
    }
    
    $content = @file_get_contents($filePath);
    if ($content === false) {
        return [];
    }
    
    // 处理BOM头
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
        if (strpos($name, '采集电影') !== false) continue;
        
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
        if ($videoCount >= 100) break; // 限制大文件的视频数量
    }
    
    return $videos;
}

/**
 * 解析大TXT文件 - 使用流式处理
 */
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
        if (strpos($name, '采集电影') !== false) continue;
        
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

/**
 * 解析M3U文件内容 - 修复图片获取并添加大文件流式处理
 */
function parseM3uFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    // 检查文件大小，大文件使用流式读取
    $fileSize = @filesize($filePath);
    if ($fileSize > 1 * 1024 * 1024) { // 超过1MB
        return parseLargeM3uFile($filePath);
    }
    
    $content = @file_get_contents($filePath);
    if ($content === false) {
        return [];
    }
    
    $lines = explode("\n", $content);
    $videos = [];
    $videoCount = 0;
    $currentName = '';
    $currentLogo = '';
    
    $defaultImages = [
        'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
    ];
    
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '') continue;
        
        // M3U文件格式：以#EXTINF:开头的是频道信息，下一行是URL
        if (strpos($line, '#EXTINF:') === 0) {
            // 重置当前信息
            $currentName = '';
            $currentLogo = '';
            
            // 提取频道名称和logo
            $parts = explode(',', $line);
            if (count($parts) > 1) {
                $currentName = trim($parts[1]);
            }
            
            // 提取tvg-logo图片
            if (preg_match('/tvg-logo="([^"]*)"/i', $line, $logoMatches)) {
                $currentLogo = trim($logoMatches[1]);
            }
            // 如果上面没匹配到，尝试其他格式
            elseif (preg_match('/tvg-logo=([^ ,]*)/i', $line, $logoMatches)) {
                $currentLogo = trim($logoMatches[1]);
            }
            
        } elseif (strpos($line, 'http') === 0 && !empty($currentName)) {
            // 这是URL行，且前面有频道名称
            $imageIndex = $videoCount % count($defaultImages);
            
            // 优先使用M3U文件中的logo，如果没有则使用默认图片
            $vodPic = $currentLogo;
            if (empty($vodPic) || !filter_var($vodPic, FILTER_VALIDATE_URL)) {
                $vodPic = $defaultImages[$imageIndex];
            }
            
            $videos[] = [
                'vod_id' => 'm3u_' . md5($filePath) . '_' . $videoCount,
                'vod_name' => $currentName,
                'vod_pic' => $vodPic,
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $currentName . '直播频道',
                'vod_play_from' => '直播源',
                'vod_play_url' => '直播$' . $line,
                'original_logo' => $currentLogo // 调试用，记录原始logo
            ];
            
            $videoCount++;
            $currentName = ''; // 重置名称
            $currentLogo = ''; // 重置logo
            if ($videoCount >= 100) break; // 限制数量
        }
    }
    
    return $videos;
}

/**
 * 解析大M3U文件 - 使用流式处理避免内存溢出
 */
function parseLargeM3uFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $handle = @fopen($filePath, 'r');
    if (!$handle) {
        return [];
    }
    
    $videos = [];
    $videoCount = 0;
    $currentName = '';
    $currentLogo = '';
    
    $defaultImages = [
        'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
        'https://img3.doubanio.com/view/photo/m_ratio_poster/public/p2921303452.jpg',
        'https://img9.doubanio.com/view/photo/m_ratio_poster/public/p2578045524.jpg'
    ];
    
    while (($line = fgets($handle)) !== false && $videoCount < 200) {
        $line = trim($line);
        if ($line === '') continue;
        
        // M3U文件格式：以#EXTINF:开头的是频道信息，下一行是URL
        if (strpos($line, '#EXTINF:') === 0) {
            // 重置当前信息
            $currentName = '';
            $currentLogo = '';
            
            // 提取频道名称和logo
            $parts = explode(',', $line);
            if (count($parts) > 1) {
                $currentName = trim($parts[1]);
            }
            
            // 提取tvg-logo图片
            if (preg_match('/tvg-logo="([^"]*)"/i', $line, $logoMatches)) {
                $currentLogo = trim($logoMatches[1]);
            }
            // 如果上面没匹配到，尝试其他格式
            elseif (preg_match('/tvg-logo=([^ ,]*)/i', $line, $logoMatches)) {
                $currentLogo = trim($logoMatches[1]);
            }
            
        } elseif (strpos($line, 'http') === 0 && !empty($currentName)) {
            // 这是URL行，且前面有频道名称
            $imageIndex = $videoCount % count($defaultImages);
            
            // 优先使用M3U文件中的logo，如果没有则使用默认图片
            $vodPic = $currentLogo;
            if (empty($vodPic) || !filter_var($vodPic, FILTER_VALIDATE_URL)) {
                $vodPic = $defaultImages[$imageIndex];
            }
            
            $videos[] = [
                'vod_id' => 'm3u_' . md5($filePath) . '_' . $videoCount,
                'vod_name' => $currentName,
                'vod_pic' => $vodPic,
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $currentName . '直播频道',
                'vod_play_from' => '直播源',
                'vod_play_url' => '直播$' . $line,
                'original_logo' => $currentLogo // 调试用，记录原始logo
            ];
            
            $videoCount++;
            $currentName = ''; // 重置名称
            $currentLogo = ''; // 重置logo
        }
    }
    
    fclose($handle);
    return $videos;
}

/**
 * 分类列表 - 支持🔥推荐分类和文件分类
 */
function getCategory($tid, $page) {
    $categories = getCategoriesFast();
    
    if (empty($categories)) {
        return ['error' => 'No categories found'];
    }
    
    // 如果是🔥推荐分类
    if ($tid === 'recommend') {
        return getRecommendCategory($page);
    }
    
    // 找到对应的文件分类
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
    
    // 特殊处理空分类
    if ($targetCategory['source_type'] === 'empty') {
        return [
            'page' => 1,
            'pagecount' => 1,
            'limit' => 10,
            'total' => 0,
            'list' => []
        ];
    }
    
    // 现在才读取文件内容
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
        }
    }
    
    if (empty($categoryVideos)) {
        return ['error' => 'No videos found in: ' . $targetCategory['type_name']];
    }
    
    // 分页处理
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

/**
 * 🔥推荐分类处理 - 支持分页（包含JSON和教程）
 */
function getRecommendCategory($page) {
    $allRecommendVideos = getAllRecommendVideos();
    
    if (empty($allRecommendVideos)) {
        return ['error' => 'No recommend videos found'];
    }
    
    // 分页处理
    $pageSize = 10;
    $total = count($allRecommendVideos);
    $pageCount = ceil($total / $pageSize);
    $currentPage = intval($page);
    
    if ($currentPage < 1) $currentPage = 1;
    if ($currentPage > $pageCount) $currentPage = $pageCount;
    
    $start = ($currentPage - 1) * $pageSize;
    $pagedVideos = array_slice($allRecommendVideos, $start, $pageSize);
    
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

/**
 * 格式化视频项（列表用）
 */
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

/**
 * 视频详情 - 按需查找
 */
function getDetail($ids) {
    $idArray = explode(',', $ids);
    $result = [];
    
    foreach ($idArray as $id) {
        $video = findVideoByIdLazy($id);
        if ($video) {
            $result[] = formatVideoDetail($video);
        } else {
            // 检查是否是教程或示例视频
            if (strpos($id, 'tutorial_') === 0 || strpos($id, 'sample_') === 0) {
                $result[] = getTutorialVideoDetail($id);
            } else {
                // 默认详情
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

/**
 * 获取教程视频详情
 */
function getTutorialVideoDetail($id) {
    $tutorials = getTutorialVideos();
    foreach ($tutorials as $tutorial) {
        if ($tutorial['vod_id'] === $id) {
            return $tutorial;
        }
    }
    
    $samples = getSampleVideos();
    foreach ($samples as $sample) {
        if ($sample['vod_id'] === $id) {
            return array_merge($sample, [
                'vod_content' => '这是一个示例视频，当您添加真实的媒体文件后，这里会显示实际的内容。',
                'vod_play_from' => '示例播放',
                'vod_play_url' => '正片$https://d6.qyshare.store/s/TBVWTxUNFQcFUQQHKFCVA50wKFCVA50FGlQEKFCVA50QIaKFCVA501EHVhoOD1EBGgEBUwBRKFCVA50VFRBVYPDxUbFVhERH9YREMVDRVYREQZRk5CWRlYRVKFCVA50VGxVYRER8Uk4VDRVCR1tYVlMYBQcFKFCVA50hgGBxgFKFCVA50RgFUgJWDgMGUxoHUQ9SGgNWU1IaDlFVDxpRBwVVUQcGKFCVA50Q8KFCVA50BQ4ZVV5ZFRsVVlQVDRUGDlMFBFQGBBoBKFCVA50wYEGgNRKFCVA50w4aDlICBhoPBw8FVQ8PVgNWVVIVGxVZVlpSFQ0VKFCVA50mgBBKFCVA50QBKFCVA50Q4DDgcEKFCVA50wYEKFCVA50QKFCVA50KFCVA50KFCVA50gQHGVpHKFCVA50xUbFVRYWUNSWUNjTkdSFQ0VQV5TUlgYWkcDFRsVVlMVDRUPBwVWBQUBVRoEKFCVA501IEGgMDUgEaVQQFURoBBgcCDgYOVVMEDlIVSg=='
            ]);
        }
    }
    
    return [
        'vod_id' => $id,
        'vod_name' => '教程内容',
        'vod_pic' => 'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
        'vod_remarks' => '教程',
        'vod_content' => '教程详情内容',
        'vod_play_from' => '教程',
        'vod_play_url' => '教程$https://d6.qyshare.store/s/TBVWTxUNFQcFUQQHKFCVA50wKFCVA50FGlQEKFCVA50QIaKFCVA501EHVhoOD1EBGgEBUwBRKFCVA50VFRBVYPDxUbFVhERH9YREMVDRVYREQZRk5CWRlYRVKFCVA50VGxVYRER8Uk4VDRVCR1tYVlMYBQcFKFCVA50hgGBxgFKFCVA50RgFUgJWDgMGUxoHUQ9SGgNWU1IaDlFVDxpRBwVVUQcGKFCVA50Q8KFCVA50BQ4ZVV5ZFRsVVlQVDRUGDlMFBFQGBBoBKFCVA50wYEGgNRKFCVA50w4aDlICBhoPBw8FVQ8PVgNWVVIVGxVZVlpSFQ0VKFCVA50mgBBKFCVA50QBKFCVA50Q4DDgcEKFCVA50wYEKFCVA50QKFCVA50KFCVA50KFCVA50gQHGVpHKFCVA50xUbFVRYWUNSWUNjTkdSFQ0VQV5TUlgYWkcDFRsVVlMVDRUPBwVWBQUBVRoEKFCVA501IEGgMDUgEaVQQFURoBBgcCDgYOVVMEDlIVSg=='
    ];
}

/**
 * 按ID查找视频 - 支持三种文件类型
 */
function findVideoByIdLazy($id) {
    $allFiles = getAllFilesFast();
    
    // 根据ID前缀判断文件类型
    if (strpos($id, 'txt_') === 0) {
        // TXT文件视频
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
        // M3U文件视频
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
    } else {
        // JSON文件视频
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
 * 搜索 - 懒加载搜索，支持三种文件类型
 */
function search($keyword, $page) {
    if (empty($keyword)) {
        return ['error' => 'Keyword is required'];
    }
    
    $searchResults = [];
    $allFiles = getAllFilesFast();
    
    // 限制搜索的文件数量，提高性能
    $searchLimit = 5;
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
        }
        
        foreach ($videos as $video) {
            if (stripos($video['vod_name'] ?? '', $keyword) !== false) {
                $searchResults[] = formatVideoItem($video);
                
                // 限制搜索结果总数
                if (count($searchResults) >= 50) break 2;
            }
        }
        
        $searchedFiles++;
    }
    
    if (empty($searchResults)) {
        return ['error' => 'No search results'];
    }
    
    // 分页处理
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

/**
 * 格式化视频详情
 */
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

/**
 * 获取播放地址
 */
function getPlay($flag, $id) {
    // 教程和示例视频返回空播放地址
    if (strpos($id, 'tutorial_') === 0 || strpos($id, 'sample_') === 0) {
        return [
            'parse' => 0,
            'playUrl' => '',
            'url' => ''
        ];
    }
    
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $id
    ];
}
?>
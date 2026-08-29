<?php
/**
 * TVBox PHP 爬虫脚本 - 二合一懒加载版本
 * 支持JSON、TXT、M3U文件
 * 包含🔥推荐分类，支持翻页
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

// 性能优化
@set_time_limit(30);

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
                $files[] = [
                    'type' => $extension,
                    'path' => $path,
                    'name' => $item,
                    'filename' => pathinfo($item, PATHINFO_FILENAME),
                    'size' => @filesize($path)
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
        $jsonFiles = scanDirectoryFast('/storage/emulated/0/lz/json/', ['json']);
        // 扫描TXT文件
        $txtFiles = scanDirectoryFast('/storage/emulated/0/lz/wj/', ['txt']);
        // 扫描M3U文件
        $m3uFiles = array_merge(
            scanDirectoryFast('/storage/emulated/0/lz/json/', ['m3u']),
            scanDirectoryFast('/storage/emulated/0/lz/wj/', ['m3u'])
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
        
        // 添加🔥推荐分类（可以翻页）
        $categories[] = [
            'type_id' => 'recommend',
            'type_name' => '🔥 三合一热门推荐',
            'type_file' => 'recommend',
            'source_path' => 'recommend',
            'source_type' => 'recommend',
            'file_size' => '可翻页'
        ];
        
        // 添加文件分类
        foreach ($allFiles as $index => $file) {
            $fileType = '';
            switch ($file['type']) {
                case 'json':
                    $fileType = '[JSON] ';
                    break;
                case 'txt':
                    $fileType = '[TXT] ';
                    break;
                case 'm3u':
                    $fileType = '[M3U] ';
                    break;
            }
            
            $fileSize = $file['size'] ? round($file['size'] / 1024, 1) . 'KB' : '未知';
            
            $categories[] = [
                'type_id' => (string)($index + 1000),
                'type_name' => $fileType . $file['filename'],
                'type_file' => $file['name'],
                'source_path' => $file['path'],
                'source_type' => $file['type'],
                'file_size' => $fileSize
            ];
        }
    }
    
    return $categories;
}

/**
 * 获取所有推荐视频 - 懒加载版本（JSON文件参与推荐）
 */
function getAllRecommendVideos() {
    static $allVideos = null;
    
    if ($allVideos === null) {
        $allVideos = [];
        $allFiles = getAllFilesFast();
        
        // 只从JSON文件中获取推荐视频
        $jsonFiles = array_filter($allFiles, function($file) {
            return $file['type'] === 'json';
        });
        
        // 处理所有JSON文件获取推荐视频
        foreach ($jsonFiles as $file) {
            $videos = parseJsonFile($file['path']);
            if (!empty($videos)) {
                foreach ($videos as $video) {
                    $allVideos[] = formatVideoItem($video);
                }
            }
        }
        
        // 随机打乱视频顺序
        shuffle($allVideos);
    }
    
    return $allVideos;
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
 * 解析JSON文件内容
 */
function parseJsonFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    $jsonContent = @file_get_contents($filePath);
    if ($jsonContent === false) {
        return [];
    }
    
    $data = json_decode($jsonContent, true);
    if (!$data || !isset($data['list']) || !is_array($data['list'])) {
        return [];
    }
    
    return $data['list'];
}

/**
 * 解析TXT文件内容
 */
function parseTxtFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
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
    }
    
    return $videos;
}

/**
 * 解析M3U文件内容
 */
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
        
        // M3U文件格式：以#EXTINF:开头的是频道信息，下一行是URL
        if (strpos($line, '#EXTINF:') === 0) {
            // 提取频道名称
            $parts = explode(',', $line);
            if (count($parts) > 1) {
                $currentName = trim($parts[1]);
            }
        } elseif (strpos($line, 'http') === 0 && !empty($currentName)) {
            // 这是URL行，且前面有频道名称
            $imageIndex = $videoCount % count($defaultImages);
            
            $videos[] = [
                'vod_id' => 'm3u_' . md5($filePath) . '_' . $videoCount,
                'vod_name' => $currentName,
                'vod_pic' => $defaultImages[$imageIndex],
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $currentName . '直播频道',
                'vod_play_from' => '直播源',
                'vod_play_url' => '直播$' . $line
            ];
            
            $videoCount++;
            $currentName = ''; // 重置名称
        }
    }
    
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
    $pageSize = 20;
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
 * 🔥推荐分类处理 - 支持分页（只包含JSON文件内容）
 */
function getRecommendCategory($page) {
    $allRecommendVideos = getAllRecommendVideos();
    
    if (empty($allRecommendVideos)) {
        return ['error' => 'No recommend videos found'];
    }
    
    // 分页处理
    $pageSize = 20;
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
            // 默认详情
            $result[] = [
                'vod_id' => $id,
                'vod_name' => '视频 ' . $id,
                'vod_pic' => 'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
                'vod_remarks' => 'HD',
                'vod_content' => '视频详情内容',
                'vod_play_from' => '在线播放',
                'vod_play_url' => '正片$https://example.com/video.m3u8'
            ];
        }
    }
    
    return ['list' => $result];
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
    $pageSize = 20;
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
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $id
    ];
}
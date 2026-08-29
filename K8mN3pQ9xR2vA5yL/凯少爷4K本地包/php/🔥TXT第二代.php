<?php
// TXT版本PHP爬虫脚本 - 高效精简版本
header('Content-Type: application/json; charset=utf-8');

// 使用Apple CMS标准参数
$ac = $_GET['ac'] ?? 'detail';
$t = $_GET['t'] ?? '';
$pg = $_GET['pg'] ?? '1';
$ids = $_GET['ids'] ?? '';
$wd = $_GET['wd'] ?? '';
$flag = $_GET['flag'] ?? '';
$id = $_GET['id'] ?? '';

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
 * 递归获取TXT文件 - 高效版本
 */
function getAllTxtFiles($dir = null) {
    if ($dir === null) {
        $dir = '/storage/emulated/0/lz/wj/';
    }
    
    $files = [];
    
    if (!is_dir($dir)) {
        return $files;
    }
    
    $items = @scandir($dir);
    if ($items === false) {
        return $files;
    }
    
    foreach ($items as $item) {
        if ($item === '.' || $item === '..') continue;
        
        $path = $dir . $item;
        
        if (is_dir($path)) {
            $subFiles = getAllTxtFiles($path . '/');
            $files = array_merge($files, $subFiles);
        } elseif (pathinfo($path, PATHINFO_EXTENSION) === 'txt') {
            $files[] = [
                'path' => $path,
                'name' => $item,
                'filename' => pathinfo($item, PATHINFO_FILENAME)
            ];
        }
    }
    
    return $files;
}

/**
 * 解析TXT文件内容 - 高效版本
 */
function parseTxtFile($filePath) {
    if (!file_exists($filePath)) {
        return [];
    }
    
    // 使用更高效的文件读取方式
    $content = @file_get_contents($filePath);
    if ($content === false || empty($content)) {
        return [];
    }
    
    // 处理BOM头
    if (substr($content, 0, 3) == "\xEF\xBB\xBF") {
        $content = substr($content, 3);
    }
    
    // 统一换行符并分割
    $content = str_replace(["\r\n", "\r"], "\n", $content);
    $lines = explode("\n", $content);
    
    $videos = [];
    $videoId = 1;
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
        
        if (empty($name) || empty($url) || strpos($url, 'http') !== 0) continue;
        if (strpos($name, '采集电影') !== false || strpos($name, '#genere#') !== false) continue;
        
        $imageIndex = ($videoId - 1) % count($defaultImages);
        
        $videos[] = [
            'vod_id' => 'txt_' . pathinfo($filePath, PATHINFO_FILENAME) . '_' . $videoId,
            'vod_name' => $name,
            'vod_pic' => $defaultImages[$imageIndex],
            'vod_remarks' => 'HD',
            'vod_year' => date('Y'),
            'vod_area' => '中国大陆',
            'vod_director' => '未知',
            'vod_actor' => '未知',
            'vod_content' => '《' . $name . '》的精彩内容',
            'vod_play_from' => '在线播放',
            'vod_play_url' => '正片$' . $url
        ];
        
        $videoId++;
        if ($videoId > 500) break; // 限制数量提高性能
    }
    
    return $videos;
}

/**
 * 获取所有推荐视频 - 懒加载版本
 */
function getAllRecommendVideos() {
    static $allVideos = null;
    
    if ($allVideos === null) {
        $allVideos = [];
        $txtFiles = getAllTxtFiles();
        
        // 处理所有TXT文件获取所有视频
        foreach ($txtFiles as $file) {
            $videos = parseTxtFile($file['path']);
            if (!empty($videos)) {
                foreach ($videos as $video) {
                    $allVideos[] = [
                        'vod_id' => $video['vod_id'],
                        'vod_name' => $video['vod_name'],
                        'vod_pic' => $video['vod_pic'],
                        'vod_remarks' => $video['vod_remarks'],
                        'vod_year' => $video['vod_year'],
                        'vod_area' => $video['vod_area']
                    ];
                }
            }
        }
        
        // 随机打乱视频顺序
        shuffle($allVideos);
    }
    
    return $allVideos;
}

/**
 * 获取所有分类 - 带🔥推荐分类
 */
function getCategories() {
    static $categories = null;
    
    if ($categories === null) {
        $txtFiles = getAllTxtFiles();
        $categories = [];
        
        // 添加🔥推荐分类
        $categories[] = [
            'type_id' => 'recommend',
            'type_name' => '🔥 TXT热门推荐',
            'type_file' => 'recommend',
            'source_path' => 'recommend'
        ];
        
        // 添加原始TXT文件分类
        $typeId = 1000;
        foreach ($txtFiles as $file) {
            $categories[] = [
                'type_id' => (string)$typeId,
                'type_name' => $file['filename'],
                'type_file' => $file['name'],
                'source_path' => $file['path']
            ];
            $typeId++;
        }
    }
    
    return $categories;
}

/**
 * 首页数据
 */
function getHome() {
    $categories = getCategories();
    
    if (empty($categories)) {
        return ['error' => 'No TXT files found in wj folder'];
    }
    
    return [
        'class' => $categories
    ];
}

/**
 * 分类列表 - 支持🔥推荐分类和普通分类
 */
function getCategory($tid, $page) {
    $categories = getCategories();
    
    if (empty($categories)) {
        return ['error' => 'No categories found'];
    }
    
    // 如果是🔥推荐分类
    if ($tid === 'recommend') {
        return getRecommendCategory($page);
    }
    
    // 找到对应的普通分类
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
    
    // 文件内容缓存
    static $fileCache = [];
    $cacheKey = $targetCategory['source_path'];
    
    if (!isset($fileCache[$cacheKey])) {
        $fileCache[$cacheKey] = parseTxtFile($targetCategory['source_path']);
    }
    
    $categoryVideos = $fileCache[$cacheKey];
    
    if (empty($categoryVideos)) {
        return ['error' => 'No videos found in this TXT file'];
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
        $formattedVideos[] = [
            'vod_id' => $video['vod_id'],
            'vod_name' => $video['vod_name'],
            'vod_pic' => $video['vod_pic'],
            'vod_remarks' => $video['vod_remarks']
        ];
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
 * 🔥推荐分类处理 - 支持分页
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
    
    return [
        'page' => $currentPage,
        'pagecount' => $pageCount,
        'limit' => $pageSize,
        'total' => $total,
        'list' => $pagedVideos
    ];
}

/**
 * 视频详情 - 优化查找
 */
function getDetail($ids) {
    $idArray = explode(',', $ids);
    $result = [];
    
    // 预加载所有文件数据
    static $allVideos = null;
    if ($allVideos === null) {
        $allVideos = [];
        $txtFiles = getAllTxtFiles();
        foreach ($txtFiles as $file) {
            $videos = parseTxtFile($file['path']);
            foreach ($videos as $video) {
                $allVideos[$video['vod_id']] = $video;
            }
        }
    }
    
    foreach ($idArray as $id) {
        if (isset($allVideos[$id])) {
            $video = $allVideos[$id];
            $result[] = [
                'vod_id' => $video['vod_id'],
                'vod_name' => $video['vod_name'],
                'vod_pic' => $video['vod_pic'],
                'vod_remarks' => $video['vod_remarks'],
                'vod_year' => $video['vod_year'],
                'vod_area' => $video['vod_area'],
                'vod_director' => $video['vod_director'],
                'vod_actor' => $video['vod_actor'],
                'vod_content' => $video['vod_content'],
                'vod_play_from' => $video['vod_play_from'],
                'vod_play_url' => $video['vod_play_url']
            ];
        } else {
            // 默认详情
            $result[] = [
                'vod_id' => $id,
                'vod_name' => '视频 ' . $id,
                'vod_pic' => 'https://2uspicc12tche.hitv.app/350/upload/vod/20240415-1/2636d5210e5cf7a6f0cff5c737e6c7b5.webp',
                'vod_remarks' => 'HD',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_director' => '未知',
                'vod_actor' => '未知',
                'vod_content' => '视频详情内容',
                'vod_play_from' => '在线播放',
                'vod_play_url' => '正片$https://example.com/video.m3u8'
            ];
        }
    }
    
    return ['list' => $result];
}

/**
 * 搜索 - 使用预加载数据
 */
function search($keyword, $page) {
    if (empty($keyword)) {
        return ['error' => 'Keyword is required'];
    }
    
    // 使用预加载的所有视频数据
    static $allVideos = null;
    if ($allVideos === null) {
        $allVideos = [];
        $txtFiles = getAllTxtFiles();
        foreach ($txtFiles as $file) {
            $videos = parseTxtFile($file['path']);
            foreach ($videos as $video) {
                $allVideos[] = $video;
            }
        }
    }
    
    $searchResults = [];
    foreach ($allVideos as $video) {
        if (stripos($video['vod_name'], $keyword) !== false) {
            $searchResults[] = [
                'vod_id' => $video['vod_id'],
                'vod_name' => $video['vod_name'],
                'vod_pic' => $video['vod_pic'],
                'vod_remarks' => $video['vod_remarks'],
                'vod_year' => $video['vod_year'],
                'vod_area' => $video['vod_area']
            ];
        }
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
 * 获取播放地址
 */
function getPlay($flag, $id) {
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $id
    ];
}
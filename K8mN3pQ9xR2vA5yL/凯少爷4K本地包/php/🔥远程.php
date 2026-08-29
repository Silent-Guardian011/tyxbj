<?php
/**
 * TVBox 远程文件加载脚本 - 带🔥推荐分类
 * 支持远程 TXT、JSON、M3U 文件
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

// 远程文件配置
$remoteFiles = [
    [
        "name" => "油管-CCTV纪录片",
        "url" => "http://127.0.0.1:9978/file/lz/wj/油管-CCTV纪录片.txt",
        "type" => "txt"
    ],
    [
        "name" => "随机m3u-远程测试", 
        "url" => "https://aries.yuanwangokk.nyc.mn/8int",
        "type" => "m3u"
    ],
    [
        "name" => "歌曲txt-远程测试",
        "url" => "https://aries.yuanwangokk.nyc.mn/2t7w",
        "type" => "txt"
    ],
    [
        "name" => "成龙json-远程测试", 
        "url" => "https://aries.yuanwangokk.nyc.mn/bfWk",
        "type" => "json"
    ],
    // 可以继续添加更多远程文件
];

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
 * 获取远程文件内容
 */
function getRemoteContent($url) {
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]);
    
    $content = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($httpCode === 200 && !empty($content)) {
        return $content;
    }
    
    return null;
}

/**
 * 解析远程JSON文件
 */
function parseRemoteJson($url) {
    $content = getRemoteContent($url);
    if (!$content) return [];
    
    // 处理BOM头
    if (substr($content, 0, 3) == "\xEF\xBB\xBF") {
        $content = substr($content, 3);
    }
    
    $data = json_decode($content, true);
    if (!$data || !isset($data['list']) || !is_array($data['list'])) {
        return [];
    }
    
    return $data['list'];
}

/**
 * 解析远程TXT文件
 */
function parseRemoteTxt($url) {
    $content = getRemoteContent($url);
    if (!$content) return [];
    
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
        $videoUrl = trim(substr($line, $commaPos + 1));
        
        if (empty($name) || empty($videoUrl)) continue;
        if (strpos($videoUrl, 'http') !== 0) continue;
        if (strpos($name, '采集电影') !== false) continue;
        
        $imageIndex = $videoCount % count($defaultImages);
        
        $videos[] = [
            'vod_id' => 'remote_txt_' . md5($url) . '_' . $videoCount,
            'vod_name' => $name,
            'vod_pic' => $defaultImages[$imageIndex],
            'vod_remarks' => 'HD',
            'vod_year' => date('Y'),
            'vod_area' => '中国大陆',
            'vod_content' => '《' . $name . '》的精彩内容',
            'vod_play_from' => '在线播放',
            'vod_play_url' => $videoUrl,
            'real_url' => $videoUrl,
            'source_type' => 'txt'
        ];
        
        $videoCount++;
    }
    
    return $videos;
}

/**
 * 解析远程M3U文件
 */
function parseRemoteM3u($url) {
    $content = getRemoteContent($url);
    if (!$content) return [];
    
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
                $currentName = preg_replace('/#[^,]*/', '', $currentName);
                $currentName = trim($currentName);
            }
        } elseif (strpos($line, 'http') === 0 && !empty($currentName)) {
            $imageIndex = $videoCount % count($defaultImages);
            
            $videos[] = [
                'vod_id' => 'remote_m3u_' . md5($url) . '_' . $videoCount,
                'vod_name' => $currentName,
                'vod_pic' => $defaultImages[$imageIndex],
                'vod_remarks' => '直播',
                'vod_year' => date('Y'),
                'vod_area' => '中国大陆',
                'vod_content' => $currentName . '直播频道',
                'vod_play_from' => '直播源',
                'vod_play_url' => $line,
                'real_url' => $line,
                'source_type' => 'm3u'
            ];
            
            $videoCount++;
            $currentName = '';
        }
    }
    
    return $videos;
}

/**
 * 获取所有远程推荐视频 - 懒加载版本
 */
function getAllRemoteRecommendVideos() {
    static $allVideos = null;
    
    if ($allVideos === null) {
        global $remoteFiles;
        $allVideos = [];
        
        // 只处理TXT和M3U文件作为推荐内容
        foreach ($remoteFiles as $file) {
            if ($file['type'] === 'json') {
                continue; // 跳过JSON文件，只推荐TXT和M3U内容
            }
            
            $videos = [];
            switch ($file['type']) {
                case 'txt':
                    $videos = parseRemoteTxt($file['url']);
                    break;
                case 'm3u':
                    $videos = parseRemoteM3u($file['url']);
                    break;
            }
            
            if (!empty($videos)) {
                foreach ($videos as $video) {
                    $allVideos[] = $video;
                }
            }
        }
        
        // 随机打乱视频顺序，增加推荐效果
        shuffle($allVideos);
    }
    
    return $allVideos;
}

/**
 * 首页数据 - 显示🔥推荐分类和远程文件分类
 */
function getHome() {
    global $remoteFiles;
    
    $categories = [];
    
    // 添加🔥推荐分类（只包含TXT和M3U内容）
    $categories[] = [
        'type_id' => 'remote_recommend',
        'type_name' => '🔥 热门推荐',
        'type_file' => 'remote_recommend',
        'source_url' => 'recommend',
        'source_type' => 'recommend',
        'file_size' => '可翻页'
    ];
    
    // 添加远程文件分类
    foreach ($remoteFiles as $index => $file) {
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
        
        $categories[] = [
            'type_id' => (string)($index + 2000),
            'type_name' => $fileType . $file['name'],
            'type_file' => basename($file['url']),
            'source_url' => $file['url'],
            'source_type' => $file['type'],
            'file_size' => '远程文件'
        ];
    }
    
    if (empty($categories)) {
        return ['error' => 'No remote files configured'];
    }
    
    return [
        'class' => $categories
    ];
}

/**
 * 分类列表 - 远程文件分类
 */
function getCategory($tid, $page) {
    global $remoteFiles;
    
    // 如果是🔥推荐分类
    if ($tid === 'remote_recommend') {
        return getRemoteRecommendCategory($page);
    }
    
    $targetIndex = intval($tid) - 2000;
    if ($targetIndex < 0 || $targetIndex >= count($remoteFiles)) {
        return ['error' => 'Category not found'];
    }
    
    $targetFile = $remoteFiles[$targetIndex];
    $videos = [];
    
    // 根据文件类型解析远程内容
    switch ($targetFile['type']) {
        case 'json':
            $videos = parseRemoteJson($targetFile['url']);
            break;
        case 'txt':
            $videos = parseRemoteTxt($targetFile['url']);
            break;
        case 'm3u':
            $videos = parseRemoteM3u($targetFile['url']);
            break;
    }
    
    if (empty($videos)) {
        return ['error' => 'No videos found in remote file: ' . $targetFile['name']];
    }
    
    // 分页处理
    $pageSize = 20;
    $total = count($videos);
    $pageCount = ceil($total / $pageSize);
    $currentPage = intval($page);
    
    if ($currentPage < 1) $currentPage = 1;
    if ($currentPage > $pageCount) $currentPage = $pageCount;
    
    $start = ($currentPage - 1) * $pageSize;
    $pagedVideos = array_slice($videos, $start, $pageSize);
    
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
 * 🔥推荐分类处理 - 支持分页（只包含TXT和M3U内容）
 */
function getRemoteRecommendCategory($page) {
    $allRecommendVideos = getAllRemoteRecommendVideos();
    
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
 * 视频详情
 */
function getDetail($ids) {
    global $remoteFiles;
    
    $idArray = explode(',', $ids);
    $result = [];
    
    foreach ($idArray as $id) {
        $video = findRemoteVideoById($id);
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
                'vod_play_url' => '正片$' . $id
            ];
        }
    }
    
    return ['list' => $result];
}

/**
 * 按ID查找远程视频
 */
function findRemoteVideoById($id) {
    global $remoteFiles;
    
    // 根据ID前缀判断文件类型和来源
    if (strpos($id, 'remote_txt_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 4) {
            $fileHash = $parts[2];
            $videoIndex = $parts[3];
            
            foreach ($remoteFiles as $file) {
                if ($file['type'] === 'txt' && md5($file['url']) === $fileHash) {
                    $videos = parseRemoteTxt($file['url']);
                    if (isset($videos[$videoIndex])) {
                        return $videos[$videoIndex];
                    }
                }
            }
        }
    } elseif (strpos($id, 'remote_m3u_') === 0) {
        $parts = explode('_', $id);
        if (count($parts) >= 4) {
            $fileHash = $parts[2];
            $videoIndex = $parts[3];
            
            foreach ($remoteFiles as $file) {
                if ($file['type'] === 'm3u' && md5($file['url']) === $fileHash) {
                    $videos = parseRemoteM3u($file['url']);
                    if (isset($videos[$videoIndex])) {
                        return $videos[$videoIndex];
                    }
                }
            }
        }
    } else {
        // JSON文件视频
        foreach ($remoteFiles as $file) {
            if ($file['type'] === 'json') {
                $videos = parseRemoteJson($file['url']);
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
 * 格式化视频详情 - 修复播放URL格式
 */
function formatVideoDetail($video) {
    $realUrl = $video['real_url'] ?? $video['vod_play_url'] ?? '';
    
    $playUrl = '';
    if (!empty($realUrl)) {
        if (strpos($realUrl, '$') !== false) {
            $playUrl = $realUrl;
        } else {
            $playUrl = '正片$' . $realUrl;
        }
    } else {
        $playUrl = '正片$' . ($video['vod_id'] ?? '');
    }
    
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
        'vod_play_from' => $video['vod_play_from'] ?? '在线播放',
        'vod_play_url' => $playUrl,
        'real_url' => $realUrl
    ];
}

/**
 * 获取播放地址 - 修复播放URL问题
 */
function getPlay($flag, $id) {
    $video = findRemoteVideoById($id);
    
    if ($video && !empty($video['real_url'])) {
        $playUrl = $video['real_url'];
    } else {
        if (strpos($id, 'http') === 0) {
            $playUrl = $id;
        } else {
            $playUrl = $id;
        }
    }
    
    return [
        'parse' => 0,
        'playUrl' => '',
        'url' => $playUrl
    ];
}

/**
 * 搜索远程文件内容
 */
function search($keyword, $page) {
    global $remoteFiles;
    
    if (empty($keyword)) {
        return ['error' => 'Keyword is required'];
    }
    
    $searchResults = [];
    
    $searchLimit = 3;
    $searchedFiles = 0;
    
    foreach ($remoteFiles as $file) {
        if ($searchedFiles >= $searchLimit) break;
        
        $videos = [];
        switch ($file['type']) {
            case 'json':
                $videos = parseRemoteJson($file['url']);
                break;
            case 'txt':
                $videos = parseRemoteTxt($file['url']);
                break;
            case 'm3u':
                $videos = parseRemoteM3u($file['url']);
                break;
        }
        
        foreach ($videos as $video) {
            if (stripos($video['vod_name'] ?? '', $keyword) !== false) {
                $searchResults[] = formatVideoItem($video);
                
                if (count($searchResults) >= 50) break 2;
            }
        }
        
        $searchedFiles++;
    }
    
    if (empty($searchResults)) {
        return ['error' => 'No search results'];
    }
    
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
?>
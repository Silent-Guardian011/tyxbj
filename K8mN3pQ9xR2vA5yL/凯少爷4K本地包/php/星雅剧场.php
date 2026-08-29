<?php
// 星芽剧场爬虫 - 严格数据结构
header('Content-Type: application/json; charset=utf-8');

// 配置
$xurl = "https://app.whjzjx.cn";
$cache_dir = __DIR__ . '/cache/';
$cache_ttl = 300;

// 创建缓存目录
if (!is_dir($cache_dir)) mkdir($cache_dir, 0755, true);

// 获取Authorization - 
function get_authorization() {
    $times = round(microtime(true) * 1000);
    
    $data = [
        "device" => "2a50580e69d38388c94c93605241fb306",
        "package_name" => "com.jz.xydj",
        "android_id" => "ec1280db12795506",
        "install_first_open" => true,
        "first_install_time" => 1752505243345,
        "last_update_time" => 1752505243345,
        "report_link_url" => "",
        "authorization" => "",
        "timestamp" => $times
    ];
    
    $plain_text = json_encode($data, JSON_UNESCAPED_UNICODE);
    $key = "B@ecf920Od8A4df7";
    
    $ciphertext = openssl_encrypt(
        $plain_text,
        'AES-128-ECB',
        $key,
        OPENSSL_RAW_DATA,
        ''
    );
    
    $encrypted = base64_encode($ciphertext);
    
    $headerf = [
        "platform: 1",
        "user-agent: Mozilla/5.0 (Linux; Android 9; V1938T Build/PQ3A.190705.08211809; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Safari/537.36",
        "content-type: application/json; charset=utf-8"
    ];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => "https://u.shytkjgs.com/user/v3/account/login",
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $encrypted,
        CURLOPT_HTTPHEADER => $headerf,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_TIMEOUT => 10
    ]);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    if ($response) {
        $response_data = json_decode($response, true);
        return $response_data['data']['token'] ?? '';
    }
    
    return '';
}

// 发送API请求
function http_request($url, $post_data = null) {
    static $authorization = null;
    
    if ($authorization === null) {
        $authorization = get_authorization();
    }
    
    $headers = [
        'authorization: ' . $authorization,
        'platform: 1',
        'version_name: 3.8.3.1',
        'user-agent: Mozilla/5.0 (Linux; Android 12; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36'
    ];
    
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_HTTPHEADER => $headers
    ]);
    
    if ($post_data !== null) {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($post_data));
        $headers[] = 'content-type: application/json';
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    }
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    if ($http_code == 200 && $response) {
        return json_decode($response, true);
    }
    
    return null;
}

// 参数解析
$ac = $_GET['ac'] ?? 'detail';
$t = $_GET['t'] ?? '';
$pg = $_GET['pg'] ?? '1';
$f = $_GET['f'] ?? '';
$ids = $_GET['ids'] ?? '';
$wd = $_GET['wd'] ?? '';
$flag = $_GET['flag'] ?? '';
$id = $_GET['id'] ?? '';

// 主逻辑 - 的数据结构
switch ($ac) {
    case 'detail':
        if (!empty($ids)) {
            // 视频详情 - 的detailContent方法
            $did = $ids;
            $data = http_request("{$xurl}/v2/theater_parent/detail?theater_parent_id={$did}");
            
            if (!$data) {
                $result = ['list' => []];
            } else {
                // 获取解析代码 - 代码
                $code_url = 'https://fs-im-kefu.7moor-fs1.com/ly/4d2c3f00-7d4c-11e5-af15-41bf63ae4ea0/1732707176882/jiduo.txt';
                $ch = curl_init();
                curl_setopt_array($ch, [
                    CURLOPT_URL => $code_url,
                    CURLOPT_RETURNTRANSFER => true,
                    CURLOPT_TIMEOUT => 10
                ]);
                $code = curl_exec($ch);
                curl_close($ch);
                
                // 提取密钥 - 代码
                preg_match("/s1='(.*?)'/", $code, $name_match);
                preg_match("/s2='(.*?)'/", $code, $jumps_match);
                $name_key = $name_match[1] ?? '';
                $jumps = $jumps_match[1] ?? '';
                
                $content = '剧情：' . ($data['data']['introduction'] ?? '');
                $area = $data['data']['desc_tags'][0] ?? '';
                $remarks = $data['data']['filing'] ?? '';
                
                // 处理播放地址 - 严格逻辑
                $xianlu = '星芽';
                $bofang = '';
                
                if (!empty($data['data']['theaters'])) {
                    foreach ($data['data']['theaters'] as $sou) {
                        $bofang .= $sou['num'] . '$' . $sou['son_video_url'] . '#';
                    }
                    $bofang = rtrim($bofang, '#');
                } elseif (!empty($data['data']['video_url'])) {
                    $bofang = '1$' . $data['data']['video_url'];
                } else {
                    $bofang = $jumps;
                    $xianlu = '1';
                }
                
                $video = [
                    'vod_id' => $did,
                    'vod_name' => $data['data']['title'] ?? '',
                    'vod_pic' => $data['data']['cover_url'] ?? '',
                    'vod_content' => $content,
                    'vod_area' => $area,
                    'vod_remarks' => $remarks,
                    'vod_play_from' => $xianlu,
                    'vod_play_url' => $bofang
                ];
                
                $result = ['list' => [$video]];
            }
        } elseif (!empty($t)) {
            // 分类列表 - 的categoryContent方法
            $page = max(1, intval($pg));
            $data = http_request("{$xurl}/v1/theater/home_page?theater_class_id={$t}&page_num={$page}&page_size=24");
            
            $videos = [];
            if ($data && !empty($data['data']['list'])) {
                foreach ($data['data']['list'] as $vod) {
                    $theater = $vod['theater'];
                    // 严格数据结构
                    $videos[] = [
                        'vod_id' => $theater['id'],
                        'vod_name' => $theater['title'],
                        'vod_pic' => $theater['cover_url'],
                        'vod_remarks' => $theater['theme'] ?? $theater['play_amount_str'] ?? ''
                    ];
                }
            }
            
            $result = [
                'list' => $videos,
                'page' => $page,
                'pagecount' => 9999,
                'limit' => 90,
                'total' => 999999
            ];
        } else {
            // 首页分类 - 的homeContent方法
            $result = [
                'class' => [
                    ['type_id' => '1', 'type_name' => '剧场'],
                    ['type_id' => '3', 'type_name' => '新剧'],
                    ['type_id' => '2', 'type_name' => '热播'],
                    ['type_id' => '7', 'type_name' => '星选'],
                    ['type_id' => '5', 'type_name' => '阳光']
                ]
            ];
        }
        break;
    
    case 'search':
        // 搜索 - 的searchContentPage方法
        $page = max(1, intval($pg));
        $key = $wd;
        
        $payload = ["text" => $key];
        $data = http_request("{$xurl}/v3/search", $payload);
        
        $videos = [];
        if ($data && !empty($data['data']['theater']['search_data'])) {
            foreach ($data['data']['theater']['search_data'] as $vod) {
                // 严格数据结构
                $videos[] = [
                    'vod_id' => $vod['id'],
                    'vod_name' => $vod['title'],
                    'vod_pic' => $vod['cover_url'],
                    'vod_remarks' => $vod['score_str'] ?? ''
                ];
            }
        }
        
        $result = [
            'list' => $videos,
            'page' => $page,
            'pagecount' => 9999,
            'limit' => 90,
            'total' => 999999
        ];
        break;
        
    case 'play':
        // 播放 - 核心修改：返回与detail分支一致的格式，确保前端识别
        $result = ['list' => []]; // 前端默认读取list数组中的视频数据
        $detail_data = http_request("{$xurl}/v2/theater_parent/detail?theater_parent_id={$id}");
        
        if ($detail_data && !empty($detail_data['data'])) {
            $video_data = $detail_data['data'];
            $xianlu = '星芽';
            $bofang = '';

            // 复用detail分支的播放地址处理逻辑，保证格式统一
            if (!empty($video_data['theaters'])) {
                // 多集视频：按“集数$地址#集数$地址”格式拼接
                foreach ($video_data['theaters'] as $sou) {
                    $bofang .= $sou['num'] . '$' . $sou['son_video_url'] . '#';
                }
                $bofang = rtrim($bofang, '#'); // 去除最后一个#号
            } elseif (!empty($video_data['video_url'])) {
                // 单集视频：固定“1$地址”格式
                $bofang = '1$' . $video_data['video_url'];
            } else {
                // 无地址时返回提示，避免前端报错
                $bofang = '1$无有效播放地址';
                $xianlu = '无';
            }

            // 构造前端能识别的vod结构（与detail分支字段完全对齐）
            $video = [
                'vod_id' => $id,
                'vod_name' => $video_data['title'] ?? '未知视频',
                'vod_pic' => $video_data['cover_url'] ?? '',
                'vod_content' => '剧情：' . ($video_data['introduction'] ?? '暂无剧情'),
                'vod_area' => $video_data['desc_tags'][0] ?? '未知地区',
                'vod_remarks' => $video_data['filing'] ?? '暂无备注',
                'vod_play_from' => $xianlu, // 播放源名称，与detail一致
                'vod_play_url' => $bofang  // 前端核心读取的播放地址字段
            ];
            $result['list'] = [$video]; // 将视频数据放入list数组，符合前端预期
        } else {
            // 接口请求失败时，返回空list避免前端崩溃
            $result['list'] = [
                [
                    'vod_id' => $id,
                    'vod_name' => '获取失败',
                    'vod_play_from' => '无',
                    'vod_play_url' => '1$获取视频数据失败，请检查网络'
                ]
            ];
        }
        break;
    
    default:
        $result = ['error' => 'Unknown action: ' . $ac];
}

echo json_encode($result, JSON_UNESCAPED_UNICODE);
?>
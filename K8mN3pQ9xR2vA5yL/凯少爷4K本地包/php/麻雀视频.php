<?php
/**
 * 麻雀视频 - PHP版本
 * 修复电影播放URL获取问题
 */

class Spider extends BaseSpider {
    
    private $host = 'https://www.mqtv.cc';
    private $key = 'Mcxos@mucho!nmme';
    
    private $def_headers = [
        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'accept-language: zh-CN,zh;q=0.9',
        'sec-ch-ua: "Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'cache-control: no-cache',
        'pragma: no-cache',
        'sec-ch-ua-mobile: ?0',
        'sec-ch-ua-platform: "Windows"',
        'sec-fetch-site: same-origin'
    ];
    
    public function init($extend = '') {
        if ($extend && strpos($extend, 'http') === 0) {
            $this->host = rtrim($extend, '/');
        }
        return '';
    }
    
    public function getName() {
        return '麻雀视频';
    }
    
    public function isVideoFormat($url) {
        return true;
    }
    
    public function manualVideoCheck() {
        return false;
    }
    
    public function destroy() {
    }
    
    public function homeContent($filter = false) {
        return [
            'class' => [
              //  ['type_id' => '/type/movie', 'type_name' => '电影'],
                ['type_id' => '/type/tv', 'type_name' => '电视剧'],
                ['type_id' => '/type/va', 'type_name' => '综艺'],
                ['type_id' => '/type/ct', 'type_name' => '动漫']
            ]
        ];
    }
    
    public function homeVideoContent() {
        return ['list' => []];
    }
    
    // ========== 辅助函数 ==========
    
    private function arr2vods($arr) {
        $result = [];
        if (is_array($arr)) {
            foreach ($arr as $i) {
                if (is_array($i)) {
                    $result[] = [
                        'vod_id' => $i['url'] ?? '',
                        'vod_name' => $i['title'] ?? '',
                        'vod_pic' => $i['img'] ?? '',
                        'vod_remarks' => $i['remark'] ?? '',
                        'vod_year' => null
                    ];
                }
            }
        }
        return $result;
    }
    
    private function strToBase64($str) {
        return base64_encode($str);
    }
    
    private function base64ToStr($b64) {
        return base64_decode($b64);
    }
    
    private function encodeData($data) {
        $jsonStr = json_encode($data);
        $b64_1 = $this->strToBase64($jsonStr);
        
        $xor_result = '';
        $keyLen = strlen($this->key);
        for ($i = 0; $i < strlen($b64_1); $i++) {
            $charCode = ord($b64_1[$i]) ^ ord($this->key[$i % $keyLen]);
            $xor_result .= chr($charCode);
        }
        
        $b64_2 = $this->strToBase64($xor_result);
        return urlencode($b64_2);
    }
    
    private function decodeData($encodedStr) {
        try {
            $decodedStep1Str = $this->base64ToStr($encodedStr);
            
            $xorResult = '';
            $keyLen = strlen($this->key);
            for ($i = 0; $i < strlen($decodedStep1Str); $i++) {
                $charCode = ord($decodedStep1Str[$i]) ^ ord($this->key[$i % $keyLen]);
                $xorResult .= chr($charCode);
            }
            
            $decodedStep2Str = $this->base64ToStr($xorResult);
            return json_decode($decodedStep2Str, true);
        } catch (Exception $e) {
            return [];
        }
    }
    
    private function getToken($path, $refPath = '') {
        $headers = array_merge($this->def_headers, [
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'priority: u=0, i',
            'sec-fetch-dest: document',
            'sec-fetch-mode: navigate',
            'sec-fetch-user: ?1',
            'upgrade-insecure-requests: 1'
        ]);
        
        if ($refPath) {
            $headers[] = 'Referer: ' . $this->host . $refPath;
        }
        
        try {
            $response = $this->fetch($this->host . $path, $headers);
            
            if (preg_match('/window\.pageid\s?=\s?\'(.*?)\';/i', $response, $matches)) {
                $pageId = $matches[1];
                return $this->encodeData($pageId);
            }
            return '';
        } catch (Exception $e) {
            return '';
        }
    }
    
    private function getHeaders2($refPath = '') {
        $headers = array_merge($this->def_headers, [
            'Accept: application/json, text/javascript, */*; q=0.01',
            'priority: u=1, i',
            'sec-fetch-dest: empty',
            'sec-fetch-mode: cors',
            'x-requested-with: XMLHttpRequest'
        ]);
        
        if ($refPath) {
            $headers[] = 'Referer: ' . $this->host . $refPath;
        }
        
        return $headers;
    }
    
    private function decryptUrl($encryptedStr, $viewportMetaId, $charsetMetaId) {
        try {
            $idTextList = [];
            $charsetLen = strlen($charsetMetaId);
            $viewportLen = strlen($viewportMetaId);
            
            for ($i = 0; $i < $charsetLen; $i++) {
                $idChar = $charsetMetaId[$i];
                $textChar = ($i < $viewportLen) ? $viewportMetaId[$i] : '';
                $idTextList[] = ['id' => $idChar, 'text' => $textChar];
            }
            
            usort($idTextList, function($a, $b) {
                return intval($a['id']) - intval($b['id']);
            });
            
            $seed = '';
            foreach ($idTextList as $item) {
                $seed .= $item['text'];
            }
            
            $md5Result = md5($seed . 'lemon');
            $iv = substr($md5Result, 0, 16);
            $keyStr = substr($md5Result, 16);
            
            $encryptedData = base64_decode($encryptedStr);
            $decrypted = openssl_decrypt(
                $encryptedData,
                'AES-128-CBC',
                $keyStr,
                OPENSSL_RAW_DATA,
                $iv
            );
            
            return trim($decrypted);
        } catch (Exception $e) {
            return '';
        }
    }
    
    // ========== 主要功能函数 ==========
    
    public function categoryContent($tid, $pg, $filter, $extend) {
        $typeKey = basename($tid);
        $token = $this->getToken($tid, '/');
        
        try {
            $url = $this->host . "/libs/VodList.api.php?type=" . $typeKey . "&rank=rankhot&cat=&year=&area=&page=" . $pg . "&token=" . $token;
            $response = $this->fetch($url, $this->getHeaders2($tid));
            $data = json_decode($response, true);
            
            return [
                'list' => $this->arr2vods($data['data'] ?? []),
                'pagecount' => 10,
                'page' => $pg,
                'total' => 200
            ];
        } catch (Exception $e) {
            return [
                'list' => [],
                'page' => $pg,
                'pagecount' => 0
            ];
        }
    }
    
    public function detailContent($ids) {
        if (empty($ids)) {
            return ['list' => []];
        }
        
        $id = $ids[0];
        $idParts = explode('/', $id);
        $realId = end($idParts);
        $token = $this->getToken($id, '/');
        
        try {
            // 判断类型
            $type = 'movie';
            $isMovie = true;
            if (strpos($id, '/type/tv') !== false || strpos($id, '/tv/') !== false) {
                $type = 'tv';
                $isMovie = false;
            } elseif (strpos($id, '/type/va') !== false || strpos($id, '/va/') !== false) {
                $type = 'va';
                $isMovie = false;
            } elseif (strpos($id, '/type/ct') !== false || strpos($id, '/ct/') !== false) {
                $type = 'ct';
                $isMovie = false;
            }
            
            $url = $this->host . "/libs/VodInfo.api.php?type=" . $type . "&id=" . $realId . "&token=" . $token;
            $response = $this->fetch($url, $this->getHeaders2($id));
            $data = json_decode($response, true);
            
            // 调试：记录API响应
            error_log("Detail API Response for movie: " . substr($response, 0, 500));
            
            $videoData = $data['data'] ?? [];
            
            $parsesArr = [];
            $playApi = $videoData['playapi'] ?? [];
            foreach ($playApi as $i) {
                if (isset($i['url']) && is_string($i['url'])) {
                    if (strpos($i['url'], '//') === 0) {
                        $parsesArr[] = 'https:' . $i['url'];
                    } else {
                        $parsesArr[] = $i['url'];
                    }
                }
            }
            $parses = implode(',', $parsesArr);
            
            // 如果没有解析地址，添加默认解析地址
            if (empty($parses)) {
                $parses = 'https://json.vipjx.cnow.eu.org/?url=,https://api.lhh.la/vip/?url=';
                $parsesArr = explode(',', $parses);
            }
            
            $shows = [];
            $playUrls = [];
            
            // 首先尝试获取播放地址
            $playUrl = '';
            
            // 方法1: 从playinfo中获取
            if (isset($videoData['playinfo']) && is_array($videoData['playinfo'])) {
                foreach ($videoData['playinfo'] as $playSource) {
                    $sourceName = $playSource['cnsite'] ?? '播放源';
                    
                    // 尝试从player中获取
                    if (isset($playSource['player']) && is_array($playSource['player'])) {
                        foreach ($playSource['player'] as $player) {
                            if (isset($player['url']) && !empty($player['url'])) {
                                $playUrl = $player['url'];
                                $shows[] = $sourceName;
                                break 2;
                            }
                        }
                    }
                    
                    // 尝试从其他字段获取
                    if (isset($playSource['url']) && !empty($playSource['url'])) {
                        $playUrl = $playSource['url'];
                        $shows[] = $sourceName;
                        break;
                    }
                }
            }
            
            // 方法2: 从其他字段获取
            if (empty($playUrl)) {
                if (isset($videoData['url']) && !empty($videoData['url'])) {
                    $playUrl = $videoData['url'];
                } elseif (isset($videoData['playurl']) && !empty($videoData['playurl'])) {
                    $playUrl = $videoData['playurl'];
                } elseif (isset($videoData['videourl']) && !empty($videoData['videourl'])) {
                    $playUrl = $videoData['videourl'];
                }
            }
            
            // 方法3: 如果还是没有，使用playapi的第一个地址
            if (empty($playUrl) && !empty($parsesArr)) {
                $playUrl = $parsesArr[0];
            }
            
            // 方法4: 构建默认播放地址
            if (empty($playUrl)) {
                $playUrl = '/play/' . $realId . '.html';
            }
            
            // 确保播放地址是完整URL
            if ($playUrl && strpos($playUrl, 'http') !== 0) {
                if (strpos($playUrl, '//') === 0) {
                    $playUrl = 'https:' . $playUrl;
                } elseif (strpos($playUrl, '/') === 0) {
                    $playUrl = $this->host . $playUrl;
                } else {
                    $playUrl = $this->host . '/' . $playUrl;
                }
            }
            
            // 构建播放列表
            if ($isMovie) {
                // 电影：只有一个播放项
                if (empty($shows)) {
                    $shows = ['播放源'];
                }
                $playUrls = ['1$' . $playUrl . '@' . $parses];
            } else {
                // 电视剧：可能有多个播放源
                if (isset($videoData['playinfo']) && is_array($videoData['playinfo'])) {
                    foreach ($videoData['playinfo'] as $playSource) {
                        $urls = [];
                        $sourceName = $playSource['cnsite'] ?? '播放源';
                        
                        if (isset($playSource['player']) && is_array($playSource['player'])) {
                            foreach ($playSource['player'] as $player) {
                                if (isset($player['no'], $player['url'])) {
                                    $urls[] = $player['no'] . '$' . $player['url'] . '@' . $parses;
                                }
                            }
                        }
                        
                        if (!empty($urls)) {
                            $playUrls[] = implode('#', $urls);
                            $shows[] = $sourceName;
                        }
                    }
                }
                
                // 如果还是没有播放列表，使用单集格式
                if (empty($shows)) {
                    $shows = ['播放源'];
                    $playUrls = ['1$' . $playUrl . '@' . $parses];
                }
            }
            
            // 确保至少有一个播放源
            if (empty($shows)) {
                $shows = ['播放源'];
                $playUrls = ['1$' . $playUrl . '@' . $parses];
            }
            
            $video = [
                'vod_id' => $id,
                'vod_name' => $videoData['title'] ?? '',
                'vod_pic' => $videoData['img'] ?? '',
                'vod_remarks' => $videoData['remark'] ?? '',
                'vod_year' => $videoData['year'] ?? '',
                'vod_area' => $videoData['area'] ?? '',
                'vod_actor' => $videoData['actor'] ?? '',
                'vod_director' => $videoData['director'] ?? '',
                'vod_content' => $videoData['desc'] ?? $videoData['content'] ?? '',
                'vod_play_from' => implode('$$$', $shows),
                'vod_play_url' => implode('$$$', $playUrls),
                'type_name' => ''
            ];
            
            return ['list' => [$video]];
        } catch (Exception $e) {
            error_log("Detail error: " . $e->getMessage());
            return ['list' => []];
        }
    }
    
    public function searchContent($key, $quick, $pg = '1') {
        if ($pg != '1') {
            return [
                'list' => [],
                'page' => $pg
            ];
        }
        
        try {
            $path = '/search/' . urlencode($key);
            $token = $this->getToken($path, '/');
            $url = $this->host . "/libs/VodList.api.php?search=" . urlencode($key) . "&token=" . $token;
            
            $response = $this->fetch($url, $this->getHeaders2($path));
            $data = json_decode($response, true);
            
            $decodedData = $this->decodeData($data['data'] ?? '');
            
            $videos = [];
            if (isset($decodedData['vod_all']) && is_array($decodedData['vod_all'])) {
                foreach ($decodedData['vod_all'] as $i) {
                    if (is_array($i) && isset($i['show'])) {
                        $videos = array_merge($videos, $this->arr2vods($i['show']));
                    }
                }
            }
            
            return [
                'list' => $videos,
                'page' => $pg
            ];
        } catch (Exception $e) {
            return [
                'list' => [],
                'page' => $pg
            ];
        }
    }
    
    public function playerContent($flag, $id, $vipFlags) {
        $parts = explode('@', $id);
        $rawUrl = $parts[0];
        $parsesStr = isset($parts[1]) ? $parts[1] : '';
        $parses = explode(',', $parsesStr);
        
        $jx = 0;
        $sniff = 0;
        $url = '';
        
        try {
            foreach ($parses as $parseUrl) {
                if (empty($parseUrl)) continue;
                
                try {
                    $apiUrl = $parseUrl . $rawUrl;
                    $response = $this->fetch($apiUrl, $this->def_headers);
                    
                    $charsetMatch = preg_match('/<meta\s+charset="UTF-8"\s+id\s*=\s*"now_(.*?)"\s*>/i', $response, $charsetMatches);
                    $viewportMatch = preg_match('/<meta\s+name="viewport".*?id\s*=\s*"now_(.*?)">/i', $response, $viewportMatches);
                    $urlMatch = preg_match('/"url"\s*:\s*"(.*?)",/i', $response, $urlMatches);
                    
                    if ($charsetMatch && $viewportMatch && $urlMatch) {
                        $playUrl = $this->decryptUrl($urlMatches[1], $viewportMatches[1], $charsetMatches[1]);
                        if (strpos($playUrl, 'http') === 0) {
                            $url = $playUrl;
                            break;
                        }
                    }
                } catch (Exception $e) {
                    // 继续尝试下一个
                }
            }
            
            if (!$url) {
                if (strpos($rawUrl, 'http') === 0 && preg_match('/(?:www\.iqiyi|v\.qq|v\.youku|www\.mgtv|www\.bilibili)\.com/', $rawUrl)) {
                    $url = $rawUrl;
                    $jx = 1;
                } else {
                    foreach ($parses as $j) {
                        if (strpos($j, 'http') === 0) {
                            $url = $j . $rawUrl;
                            $sniff = 1;
                            break;
                        }
                    }
                }
            }
        } catch (Exception $e) {
            // 忽略错误
        }
        
        return [
            'jx' => $jx,
            'parse' => $sniff,
            'url' => $url,
            'header' => [
                'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
                'referer' => $this->host . '/'
            ]
        ];
    }
    
    public function localProxy($param) {
        return null;
    }
    
    protected function fetch($url, $headers = [], $postData = null) {
        return parent::fetch($url, $headers, $postData);
    }
}
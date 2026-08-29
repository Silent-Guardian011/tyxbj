<?php

/**
 * 零度影视 - PHP 版本 (修复多分类问题)
 */

class Spider extends BaseSpider {
    
    private $host = 'http://ldys.sq1005.top';
    
    private $publicKey = <<<EOD
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoYt0BP77U+DM08BiI/QbSRIfx
ijXo85BTPqIM1Ow8BNwhLETzRIZ+dEwdWDbydG/PspgBAfRpGaYVdJYtvaC2JnoO
8+Ik6qMWojfEJxSFLa0Pb0A892tun4gsxoEMjcreZ+YGyaBxAfqX0BSMfdrOgIYa
ZQjYrw9TRLlUT31QoQIDAQAB
-----END PUBLIC KEY-----
EOD;
    
    private $privateKey = <<<EOD
-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCquQQ5r6+yJI8C
DFkXRp8vUsdD45ov8EP12ooLs56ca2DQXaSNGS9910bAPVA9chkp0mKIvKqjAsHz
5Tl9EeNPblarGEeJUIxpxZtiSqNTpvtiD/TjhpzuHYic7RAfQ/h7p/ypE8ymU42p
YjsB5t26Mv6XgkLV+jzrSf73HlCuS0iMyLmt6zz3Mw9izM13EpB8iFLtfbbYymyc
KTx4RAmPQLwhNGex/AlUIYxXP4R2yyaa4W6mEtc6aME2QuzJFxPgP3HJ9NBx/LWV
n4skxWjZ7zg+VRQRHnjyVaSLu3Z5gN5ITWCyE32qaHJa6WBahZj5jWhRyAG1bQ+x
KJa8lBL5AgMBAAECggEAUwv9SjJ0PSwbhNuM2w23kcWquROWhYtTA91zGY4esehq
B/IFgb2mpIh8Gje5OKqwIu/8jpd4SiOlRYdUF8sD0DfUYRZGdj2AkFNX6tBz8tVf
o6wvbB6naA1lzzBij1L5JO3qsjS3cJFkb+kg2yP66AC2Z+0tpfk8eRhdtshAZwfc
d1DEGt1uAvYL1eaUK9HRvpt9lPeGcHERDl2hBd4uyaF0K1O+zF9y59nYbTySWPxR
Zq3sFEE85xRMlstD7YZi7W2gKvMFRD4/FKmrZ3m7aKJRITtyKOyyPcYmepNv3Qv7
kk59Pg38n2WWQ0Ra/bCH3E48YNCnQvZMpitkTfJhoQKBgQDbnROOYTP8OTJ6f/qh
oGjxeO3x1VOaOp8l0x7b0SCfoqNGS0Cyiqj72BmJtPMPqSTjn6MmNzqbg1KOdhXy
zNozs+i5ccW1M56j96mr5I/Z0FpE3oyIHNfDDBlf9M8YQqEF9oYxniYYft9oapO7
cRQkHER6qpvnHTavwlv4m78CXwKBgQDHAjs2YlpKDdI1lcbZJCc7TwtH+Pd2bUki
8YXafWNcPhITQHbOZjr310eK1QJC6GJncjkOqbX7yv3ivvTO35FZTQhuA1xEG1P0
0FG8bE0tHYPIwQHi9y0eA5cieMdo8E6XYria1mw/3fqSQEsfZyJlR32JQIoGAipM
8iO1X2nZpwKBgDkMFIhnt5lNQk+P7wsNIDWZtDWdtJnboHuy29E+Abt2A/O+mI/I
dRz2hau/1WO8DFkUnszOi+rZshhPlGP90rCbi1igtTrcrdjp/KkqNjPea5R4Owkg
dOu1uOG0NheXNzzVTQaWjk7Opjn5dWa7eP/oV+GFb/oZHJuLYVizHGsBAoGADA7r
jZEKDYCm4w5PPSr+oY5ZjaPdQrS+gLqHtMRyN82fBMGcMUdqfUfzEstzVqCEDeaS
5HuOBlK3bXzKkppjUTjksN3NQmcxgBz7RuJ9DqXCLXDcb2cwuafYCYOt+YLOEEgw
DVm+t2P44dG5e46hO+fICH/7nP+WlpD5buz4GfMCgYB57r3g/6hi9WUDnfc7ZAzW
MqR0EhJVYKYy+KFEtdIPzhkkIHq5RASe88E9kzoGoZFdb3tIjvGZWcHerirrqWkM
suQtP/Qi0zjieid5tAPj+r4kbiCVTw0E0jnmPBzGInQi7lpeTTKnG1fbyS5lBS+W
mHfIuzpECgCkxhaT+LJJkg==
-----END PRIVATE KEY-----
EOD;
    
    private $deviceId = '';
    private $token = '';
    
    public function init($extend = '') {
        return '';
    }
    
    public function getName() {
        return '零度影视';
    }
    
    public function isVideoFormat($url) {
        return true;
    }
    
    public function manualVideoCheck() {
        return false;
    }
    
    public function destroy() {
    }
    
    // ========== 工具方法 ==========
    
    private function generateDeviceId() {
        if (empty($this->deviceId)) {
            $hex = '0123456789abcdef';
            $this->deviceId = '';
            for ($i = 0; $i < 16; $i++) {
                $this->deviceId .= $hex[mt_rand(0, 15)];
            }
        }
        return $this->deviceId;
    }
    
    private function getHeaders() {
        $deviceId = $this->generateDeviceId();
        
        if (empty($this->token)) {
            $this->getToken($deviceId);
        }
        
        return [
            'HOST: ldys.sq1005.top',
            'User-Agent: okhttp/4.12.0',
            'client: app',
            'deviceType: Android',
            'deviceId: ' . $deviceId,
            'token: ' . $this->token,
            'Referer: ',
            'Connection: keep-alive'
        ];
    }
    
    private function getToken($deviceId) {
        try {
            $ch = curl_init($this->host . '/api/v1/app/user/visitorInfo');
            curl_setopt_array($ch, [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_HTTPHEADER => [
                    'deviceId: ' . $deviceId,
                    'client: app',
                    'deviceType: Android',
                    'User-Agent: okhttp/4.12.0'
                ],
                CURLOPT_TIMEOUT => 10,
                CURLOPT_SSL_VERIFYPEER => false,
                CURLOPT_SSL_VERIFYHOST => false,
            ]);
            
            $response = curl_exec($ch);
            curl_close($ch);
            
            if ($response) {
                $data = json_decode($response, true);
                if ($data && isset($data['data']['token'])) {
                    $this->token = $data['data']['token'];
                }
            }
        } catch (Exception $e) {
        }
    }
    
    private function rsaEncode($data) {
        try {
            if (is_array($data)) {
                $data = json_encode($data, JSON_UNESCAPED_UNICODE);
            }
            
            $encrypted = '';
            $result = openssl_public_encrypt($data, $encrypted, $this->publicKey, OPENSSL_PKCS1_PADDING);
            
            if ($result) {
                return base64_encode($encrypted);
            }
        } catch (Exception $e) {
        }
        return "";
    }
    
    private function rsaDecode($data) {
        if (empty($data)) {
            return null;
        }
        
        try {
            $binary = base64_decode($data);
            if ($binary === false) {
                return null;
            }
            
            $blockSize = 256;
            $decryptedParts = [];
            $length = strlen($binary);
            
            for ($i = 0; $i < $length; $i += $blockSize) {
                $chunk = substr($binary, $i, $blockSize);
                if (strlen($chunk) === 0) continue;
                
                $decChunk = '';
                $result = openssl_private_decrypt($chunk, $decChunk, $this->privateKey, OPENSSL_NO_PADDING);
                
                if ($result && $decChunk) {
                    $zeroIndex = strpos($decChunk, "\x00", 2);
                    if ($zeroIndex !== false) {
                        $decryptedParts[] = substr($decChunk, $zeroIndex + 1);
                    } else {
                        $decryptedParts[] = $decChunk;
                    }
                }
            }
            
            if (empty($decryptedParts)) {
                return null;
            }
            
            $result = implode('', $decryptedParts);
            $result = preg_replace('/[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\xff]/', '', $result);
            return trim($result);
        } catch (Exception $e) {
            return null;
        }
    }
    
    private function makeRequest($url, $method = 'GET', $data = null, $headers = null) {
        try {
            $ch = curl_init($url);
            $options = [
                CURLOPT_RETURNTRANSFER => true,
                CURLOPT_TIMEOUT => 15,
                CURLOPT_SSL_VERIFYPEER => false,
                CURLOPT_SSL_VERIFYHOST => false,
                CURLOPT_FOLLOWLOCATION => true,
            ];
            
            if ($method === 'POST') {
                $options[CURLOPT_POST] = true;
                if ($data !== null) {
                    if (is_array($data)) {
                        $data = json_encode($data, JSON_UNESCAPED_UNICODE);
                        $options[CURLOPT_POSTFIELDS] = $data;
                        if ($headers === null) {
                            $headers = [];
                        }
                        $headers[] = 'Content-Type: application/json; charset=utf-8';
                    } else {
                        $options[CURLOPT_POSTFIELDS] = $data;
                    }
                }
            }
            
            if ($headers !== null) {
                $options[CURLOPT_HTTPHEADER] = $headers;
            }
            
            curl_setopt_array($ch, $options);
            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);
            
            if ($httpCode === 200 && $response) {
                return json_decode($response, true);
            }
        } catch (Exception $e) {
        }
        return null;
    }
    
    // ========== 业务方法 ==========
    
    public function homeContent($filter = false) {
        $headers = $this->getHeaders();
        
        $data = $this->makeRequest(
            $this->host . '/api/v1/app/screen/screenType',
            'POST',
            new stdClass(),
            $headers
        );
        
        if (!$data || !isset($data['data'])) {
            return ['class' => []];
        }
        
        $classes = [];
        foreach ($data['data'] as $item) {
            $classes[] = [
                'type_id' => strval($item['id']),
                'type_name' => $item['name'] ?? ''
            ];
        }
        
        return ['class' => $classes];
    }
    
    public function homeVideoContent() {
        return ['list' => []];
    }
    
    public function categoryContent($tid, $pg, $filter, $extend) {
        $page = intval($pg);
        $headers = $this->getHeaders();
        
        $payload = [
            'condition' => [
                'sreecnTypeEnum' => 'NEWEST',
                'typeId' => $tid
            ],
            'pageNum' => $page,
            'pageSize' => 40
        ];
        
        $data = $this->makeRequest(
            $this->host . '/api/v1/app/screen/screenMovie',
            'POST',
            $payload,
            $headers
        );
        
        if (!$data || !isset($data['data']['records'])) {
            return ['list' => [], 'page' => $page, 'pagecount' => 0];
        }
        
        $videos = [];
        foreach ($data['data']['records'] as $item) {
            $videos[] = [
                'vod_id' => $item['id'] . '*' . $item['typeId'],
                'vod_name' => $item['name'] ?? '',
                'vod_pic' => $item['cover'] ?? '',
                'vod_remarks' => $item['totalEpisode'] ?? '0'
            ];
        }
        
        $total = $data['data']['total'] ?? 0;
        $pagecount = ceil($total / 40);
        
        return [
            'list' => $videos,
            'page' => $page,
            'pagecount' => $pagecount
        ];
    }
    
    public function detailContent($ids) {
        $headers = $this->getHeaders();
        
        $idList = is_array($ids) ? $ids : [$ids];
        if (empty($idList)) {
            return ['list' => []];
        }
        
        $idStr = $idList[0];
        $parts = explode('*', $idStr);
        if (count($parts) < 2) {
            return ['list' => []];
        }
        
        $m_id = $parts[0];
        $typeId = $parts[1];
        
        try {
            // 1. 获取详情
            $detailPayload = [
                'id' => intval($m_id),
                'typeId' => $typeId
            ];
            
            $detailData = $this->makeRequest(
                $this->host . '/api/v1/app/play/movieDesc',
                'POST',
                $detailPayload,
                $headers
            );
            
            if (!$detailData || !isset($detailData['data'])) {
                return ['list' => []];
            }
            
            $detail = $detailData['data'];
            
            // 2. 根据分类类型处理播放源 - 关键修复
            $playFrom = [];
            $playUrl = [];
            
            // 获取总集数
            $totalEpisodes = intval($detail['totalEpisode'] ?? 0);
            
            // 处理不同类型的内容
            switch ($typeId) {
                case '3': // 综艺
                case '4': // 动漫
                    // 综艺和动漫：需要特殊处理播放源
                    $playSources = $this->getSpecialPlaySources($m_id, $typeId, $headers, $totalEpisodes);
                    break;
                    
                case '64': // 短剧
                case '少儿分类ID': // 需要根据实际分类ID调整
                    // 短剧和少儿：可能是单集或者不同结构
                    $playSources = $this->getShortPlaySources($m_id, $typeId, $headers, $totalEpisodes);
                    break;
                    
                default:
                    // 电影、电视剧等：标准处理
                    $playSources = $this->getStandardPlaySources($m_id, $typeId, $headers, $totalEpisodes);
                    break;
            }
            
            if (!empty($playSources)) {
                list($playFrom, $playUrl) = $playSources;
            } else {
                // 备用方案：根据总集数创建默认播放项
                $playFrom[] = '默认播放';
                if ($totalEpisodes > 1) {
                    $episodes = [];
                    for ($i = 1; $i <= min($totalEpisodes, 50); $i++) {
                        $episodes[] = $this->createPlayItem($m_id, $typeId, 1, $i, '第' . $i . '集');
                    }
                    $playUrl[] = implode('#', $episodes);
                } else {
                    $playUrl[] = $this->createPlayItem($m_id, $typeId, 1, 1, '正片');
                }
            }
            
            $video = [
                'vod_id' => $idStr,
                'vod_name' => $detail['name'] ?? '未知',
                'vod_pic' => $detail['cover'] ?? '',
                'vod_remarks' => $detail['totalEpisode'] ?? '0',
                'vod_year' => $detail['year'] ?? '',
                'vod_area' => $detail['area'] ?? '',
                'vod_actor' => $detail['star'] ?? '',
                'vod_content' => $detail['introduce'] ?? '',
                'vod_play_from' => implode('$$$', $playFrom),
                'vod_play_url' => implode('$$$', $playUrl)
            ];
            
            return ['list' => [$video]];
            
        } catch (Exception $e) {
            return ['list' => []];
        }
    }
    
    // 新增：标准播放源获取（电影、电视剧）
    private function getStandardPlaySources($m_id, $typeId, $headers, $totalEpisodes) {
        $playFrom = [];
        $playUrl = [];
        
        // 获取播放源列表
        $playKeyData = [
            'id' => intval($m_id),
            'source' => 0,
            'typeId' => $typeId
        ];
        
        $playKey = $this->rsaEncode($playKeyData);
        if (empty($playKey)) {
            return null;
        }
        
        $playPayload = ['key' => $playKey];
        $playData = $this->makeRequest(
            $this->host . '/api/v1/app/play/movieDetails',
            'POST',
            $playPayload,
            $headers
        );
        
        if (!$playData || !isset($playData['data'])) {
            return null;
        }
        
        $decryptedStr = $this->rsaDecode($playData['data']);
        if (!$decryptedStr) {
            return null;
        }
        
        $decryptedData = json_decode($decryptedStr, true);
        if (!$decryptedData) {
            return null;
        }
        
        // 处理标准播放源结构
        if (isset($decryptedData['moviePlayerList']) && is_array($decryptedData['moviePlayerList'])) {
            foreach ($decryptedData['moviePlayerList'] as $player) {
                $playerId = $player['id'] ?? 0;
                $playerName = $player['moviePlayerName'] ?? '播放源';
                
                $playFrom[] = $playerName;
                
                // 获取该播放源的剧集
                $episodes = $this->getEpisodes($m_id, $typeId, $playerId, $headers, $totalEpisodes);
                if (!empty($episodes)) {
                    $playUrl[] = implode('#', $episodes);
                } else {
                    // 创建默认剧集
                    if ($totalEpisodes > 1) {
                        $defaultEpisodes = [];
                        for ($i = 1; $i <= min($totalEpisodes, 20); $i++) {
                            $defaultEpisodes[] = $this->createPlayItem($m_id, $typeId, $playerId, $i, '第' . $i . '集');
                        }
                        $playUrl[] = implode('#', $defaultEpisodes);
                    } else {
                        $playUrl[] = $this->createPlayItem($m_id, $typeId, $playerId, 1, '正片');
                    }
                }
            }
        } else if (isset($decryptedData['url'])) {
            // 直接有播放URL的情况（电影）
            $playFrom[] = '播放';
            $playUrl[] = $this->createPlayItem($m_id, $typeId, 1, 1, '正片');
        }
        
        return [$playFrom, $playUrl];
    }
    
    // 新增：特殊分类播放源获取（综艺、动漫）
    private function getSpecialPlaySources($m_id, $typeId, $headers, $totalEpisodes) {
        $playFrom = [];
        $playUrl = [];
        
        // 尝试多种方式获取播放源
        $attempts = [
            ['source' => 0], // 默认源
            ['source' => 1], // 备用源1
            ['source' => 2], // 备用源2
        ];
        
        foreach ($attempts as $attempt) {
            $playKeyData = [
                'id' => intval($m_id),
                'source' => $attempt['source'],
                'typeId' => $typeId
            ];
            
            $playKey = $this->rsaEncode($playKeyData);
            if (empty($playKey)) continue;
            
            $playPayload = ['key' => $playKey];
            $playData = $this->makeRequest(
                $this->host . '/api/v1/app/play/movieDetails',
                'POST',
                $playPayload,
                $headers
            );
            
            if ($playData && isset($playData['data'])) {
                $decryptedStr = $this->rsaDecode($playData['data']);
                if ($decryptedStr) {
                    $decryptedData = json_decode($decryptedStr, true);
                    
                    // 检查不同的数据结构
                    if (isset($decryptedData['episodeList']) && is_array($decryptedData['episodeList'])) {
                        $playFrom[] = '播放源' . ($attempt['source'] + 1);
                        $episodes = [];
                        foreach ($decryptedData['episodeList'] as $index => $ep) {
                            $episodeName = $ep['episode'] ?? ('第' . ($index + 1) . '期');
                            $episodes[] = $this->createPlayItem($m_id, $typeId, $attempt['source'] + 1, $ep['id'] ?? ($index + 1), $episodeName);
                        }
                        $playUrl[] = implode('#', $episodes);
                        break; // 找到有效源就停止尝试
                    }
                }
            }
        }
        
        // 如果还是没找到，创建默认播放项
        if (empty($playFrom) && $totalEpisodes > 0) {
            $playFrom[] = '默认播放';
            $episodes = [];
            for ($i = 1; $i <= min($totalEpisodes, 30); $i++) {
                $episodes[] = $this->createPlayItem($m_id, $typeId, 1, $i, '第' . $i . '期');
            }
            $playUrl[] = implode('#', $episodes);
        }
        
        return [$playFrom, $playUrl];
    }
    
    // 新增：短剧和少儿播放源获取
    private function getShortPlaySources($m_id, $typeId, $headers, $totalEpisodes) {
        $playFrom = [];
        $playUrl = [];
        
        // 短剧和少儿可能没有标准的播放源结构，尝试直接获取
        $playKeyData = [
            'id' => intval($m_id),
            'source' => 0,
            'typeId' => $typeId
        ];
        
        $playKey = $this->rsaEncode($playKeyData);
        if (empty($playKey)) {
            return null;
        }
        
        $playPayload = ['key' => $playKey];
        $playData = $this->makeRequest(
            $this->host . '/api/v1/app/play/movieDetails',
            'POST',
            $playPayload,
            $headers
        );
        
        if ($playData && isset($playData['data'])) {
            $decryptedStr = $this->rsaDecode($playData['data']);
            if ($decryptedStr) {
                $decryptedData = json_decode($decryptedStr, true);
                
                // 短剧可能是数组格式
                if (is_array($decryptedData) && isset($decryptedData[0])) {
                    $playFrom[] = '短剧播放';
                    $episodes = [];
                    foreach ($decryptedData as $index => $item) {
                        if (is_array($item) && isset($item['url'])) {
                            $episodes[] = $this->createPlayItem($m_id, $typeId, 1, $index + 1, '第' . ($index + 1) . '集');
                        }
                    }
                    if (!empty($episodes)) {
                        $playUrl[] = implode('#', $episodes);
                    }
                }
            }
        }
        
        // 备用方案
        if (empty($playFrom) && $totalEpisodes > 0) {
            $playFrom[] = '默认播放';
            $episodes = [];
            for ($i = 1; $i <= min($totalEpisodes, 100); $i++) {
                $episodes[] = $this->createPlayItem($m_id, $typeId, 1, $i, '第' . $i . '集');
            }
            $playUrl[] = implode('#', $episodes);
        }
        
        return [$playFrom, $playUrl];
    }
    
    // 获取剧集列表
    private function getEpisodes($m_id, $typeId, $playerId, $headers, $totalEpisodes) {
        $episodes = [];
        
        $epKeyData = [
            'id' => intval($m_id),
            'source' => 0,
            'typeId' => $typeId,
            'playerId' => $playerId
        ];
        
        $epKey = $this->rsaEncode($epKeyData);
        if (empty($epKey)) {
            return $episodes;
        }
        
        $epPayload = ['key' => $epKey];
        $epData = $this->makeRequest(
            $this->host . '/api/v1/app/play/movieDetails',
            'POST',
            $epPayload,
            $headers
        );
        
        if ($epData && isset($epData['data'])) {
            $epDecryptedStr = $this->rsaDecode($epData['data']);
            if ($epDecryptedStr) {
                $decryptedEp = json_decode($epDecryptedStr, true);
                
                // 处理各种剧集格式
                if (isset($decryptedEp['episodeList']) && is_array($decryptedEp['episodeList'])) {
                    foreach ($decryptedEp['episodeList'] as $ep) {
                        $episodeName = $ep['episode'] ?? '未知';
                        $episodeId = $ep['id'] ?? 0;
                        $episodes[] = $this->createPlayItem($m_id, $typeId, $playerId, $episodeId, $episodeName);
                    }
                } else if (isset($decryptedEp['url'])) {
                    // 单集直接播放
                    $episodes[] = $this->createPlayItem($m_id, $typeId, $playerId, 1, '正片');
                }
            }
        }
        
        // 如果没获取到剧集但知道总集数，创建默认剧集
        if (empty($episodes) && $totalEpisodes > 0) {
            for ($i = 1; $i <= min($totalEpisodes, 20); $i++) {
                $episodes[] = $this->createPlayItem($m_id, $typeId, $playerId, $i, '第' . $i . '集');
            }
        }
        
        return $episodes;
    }
    
    // 创建播放项
    private function createPlayItem($m_id, $typeId, $playerId, $episodeId, $episodeName) {
        $param = [
            'id' => $m_id,
            'typeId' => $typeId,
            'playerId' => $playerId,
            'episodeId' => $episodeId
        ];
        $paramStr = json_encode($param, JSON_UNESCAPED_UNICODE);
        return $episodeName . '$' . base64_encode($paramStr);
    }
    
    public function searchContent($key, $quick, $pg = '1') {
        $page = intval($pg);
        
        if ($page !== 1 || empty($key)) {
            return ['list' => [], 'page' => $page];
        }
        
        $headers = $this->getHeaders();
        
        $payload = [
            'condition' => ['value' => $key],
            'pageNum' => 1,
            'pageSize' => 40
        ];
        
        $data = $this->makeRequest(
            $this->host . '/api/v1/app/search/searchMovie',
            'POST',
            $payload,
            $headers
        );
        
        if (!$data || !isset($data['data']['records'])) {
            return ['list' => [], 'page' => $page];
        }
        
        $videos = [];
        foreach ($data['data']['records'] as $item) {
            $videos[] = [
                'vod_id' => $item['id'] . '*' . $item['typeId'],
                'vod_name' => $item['name'] ?? '',
                'vod_pic' => $item['cover'] ?? '',
                'vod_remarks' => $item['totalEpisode'] ?? '0'
            ];
        }
        
        return [
            'list' => $videos,
            'page' => $page
        ];
    }
    
    public function playerContent($flag, $id, $vipFlags) {
        $headers = $this->getHeaders();
        
        try {
            $decoded = base64_decode($id);
            if ($decoded === false) {
                return ['parse' => 0, 'url' => ''];
            }
            
            $param = json_decode($decoded, true);
            if (!$param) {
                return ['parse' => 0, 'url' => ''];
            }
            
            // 关键修复：尝试多种source值获取播放地址
            $sources = [0, 1, 2, 3];
            $playUrl = '';
            
            foreach ($sources as $source) {
                $urlKeyData = [
                    'id' => intval($param['id']),
                    'source' => $source,
                    'typeId' => $param['typeId'],
                    'playerId' => $param['playerId'],
                    'episodeId' => $param['episodeId']
                ];
                
                $urlKey = $this->rsaEncode($urlKeyData);
                if (empty($urlKey)) continue;
                
                $urlPayload = ['key' => $urlKey];
                $postData = $this->makeRequest(
                    $this->host . '/api/v1/app/play/movieDetails',
                    'POST',
                    $urlPayload,
                    $headers
                );
                
                if ($postData && isset($postData['data'])) {
                    $decryptedStr = $this->rsaDecode($postData['data']);
                    if ($decryptedStr) {
                        $decryptedUrlData = json_decode($decryptedStr, true);
                        if ($decryptedUrlData && isset($decryptedUrlData['url']) && !empty($decryptedUrlData['url'])) {
                            $playerUrl = $decryptedUrlData['url'];
                            
                            // 解析播放地址
                            $params = [
                                'playerUrl' => $playerUrl,
                                'playerId' => $param['playerId']
                            ];
                            
                            $queryString = http_build_query($params);
                            $url = $this->host . '/api/v1/app/play/analysisMovieUrl?' . $queryString;
                            
                            $ch = curl_init($url);
                            curl_setopt_array($ch, [
                                CURLOPT_RETURNTRANSFER => true,
                                CURLOPT_HTTPHEADER => $headers,
                                CURLOPT_TIMEOUT => 10,
                                CURLOPT_SSL_VERIFYPEER => false,
                                CURLOPT_SSL_VERIFYHOST => false,
                            ]);
                            
                            $response = curl_exec($ch);
                            curl_close($ch);
                            
                            if ($response) {
                                $data = json_decode($response, true);
                                $playUrl = $data['data'] ?? '';
                                if (!empty($playUrl)) {
                                    break; // 找到有效播放地址就停止
                                }
                            }
                        }
                    }
                }
            }
            
            if (!empty($playUrl)) {
                return ['parse' => 0, 'url' => $playUrl];
            }
            
        } catch (Exception $e) {
        }
        
        return ['parse' => 0, 'url' => ''];
    }
    
    public function localProxy($param) {
        return null;
    }
}
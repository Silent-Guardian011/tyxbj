<?php
class LspCmSpider {
    private $siteUrl = "https://xn--oq2a.lspcm48.lat";
    
    public function getName() {
        return "lsp传媒（优）";
    }
    
    public function init($extend) {
        // 初始化配置
    }
    
    public function homeContent($filter) {
        $result = array();
        $classes = array();
        
        try {
            $rsp = $this->fetch($this->siteUrl . "/index.php");
            if ($rsp) {
                // 使用正则表达式提取分类
                preg_match_all('/<li\s+class="[^"]*">\s*<a\s+href="\/(\d+)\.html">([^<]+)<\/a>\s*<\/li>/', $rsp, $matches, PREG_SET_ORDER);
                
                foreach ($matches as $match) {
                    $classes[] = array(
                        'type_name' => $match[2],
                        'type_id' => $match[1]
                    );
                }
            }
        } catch (Exception $e) {
            // 错误处理
        }
        
        $result['class'] = $classes;
        return $result;
    }
    
    public function homeVideoContent() {
        return array();
    }
    
    public function categoryContent($tid, $pg, $filter, $extend) {
        $result = array();
        $videos = array();
        
        try {
            $url = $this->siteUrl . "/index.php/vod/type/id/{$tid}/page/{$pg}.html";
            $rsp = $this->fetch($url);
            
            if ($rsp) {
                // 提取视频列表
                preg_match_all('/<div\s+class="grid__item[^"]*">(.*?)<\/div>\s*<\/div>/s', $rsp, $items, PREG_SET_ORDER);
                
                foreach ($items as $item) {
                    $itemHtml = $item[1];
                    
                    // 提取链接
                    preg_match('/<a\s+href="([^"]+)"/', $itemHtml, $hrefMatch);
                    // 提取标题
                    preg_match('/<h3[^>]*>(.*?)<\/h3>/', $itemHtml, $titleMatch);
                    // 提取图片
                    preg_match('/<img[^>]+(?:data-original|src)="([^"]+)"/', $itemHtml, $imgMatch);
                    // 提取描述/时长
                    preg_match('/<span\s+class="duration-video[^>]*>(.*?)<\/span>/', $itemHtml, $descMatch);
                    
                    if ($hrefMatch && $titleMatch) {
                        $href = $hrefMatch[1];
                        $title = $titleMatch[1];
                        $img = $imgMatch ? $imgMatch[1] : '';
                        $desc = $descMatch ? $descMatch[1] : '';
                        
                        // 直接获取播放地址，实现点击即播
                        $playUrl = $this->getDirectPlayUrl($href);
                        
                        $videos[] = array(
                            'vod_id' => $href,
                            'vod_name' => $title,
                            'vod_pic' => $img,
                            'vod_remarks' => $desc,
                            // 添加直接播放信息
                            'vod_play_url' => $playUrl ? '正片$' . $playUrl : '',
                            'vod_play_from' => $playUrl ? '默认线路' : ''
                        );
                    }
                }
            }
        } catch (Exception $e) {
            // 错误处理
        }
        
        $result['list'] = $videos;
        $result['page'] = intval($pg);
        $result['pagecount'] = 9999;
        $result['limit'] = 90;
        $result['total'] = 999999;
        
        return $result;
    }
    
    public function detailContent($ids) {
        $result = array();
        if (empty($ids)) return $result;
        
        try {
            $aid = $ids[0];
            $url = $this->siteUrl . (strpos($aid, '/') === 0 ? $aid : '/' . $aid);
            $rsp = $this->fetch($url);
            
            if ($rsp) {
                // 提取视频标题
                preg_match('/<h1[^>]*class="[^"]*section-header__title[^"]*"[^>]*>(.*?)<\/h1>/', $rsp, $titleMatch);
                // 提取封面图片
                preg_match('/<div[^>]*class="[^"]*xgplayer-poster[^"]*"[^>]*style="[^"]*background-image:\s*url\(\'?([^\'\)]+)/', $rsp, $picMatch);
                // 提取描述
                preg_match('/<div[^>]*class="[^"]*video-footer__description[^"]*"[^>]*>(.*?)<\/div>/s', $rsp, $descMatch);
                
                $title = $titleMatch ? trim($titleMatch[1]) : '';
                $pic = $picMatch ? $picMatch[1] : '';
                $desc = $descMatch ? trim(strip_tags($descMatch[1])) : '';
                
                // 获取播放地址
                $playUrl = $this->extractPlayUrl($rsp);
                
                $vod = array(
                    'vod_id' => $aid,
                    'vod_name' => $title,
                    'vod_pic' => $pic,
                    'vod_remarks' => $desc,
                    'vod_content' => $desc,
                    'vod_play_from' => $playUrl ? '默认线路' : '',
                    'vod_play_url' => $playUrl ? '正片$' . $playUrl : ''
                );
                
                $result['list'] = array($vod);
            }
        } catch (Exception $e) {
            // 错误处理
        }
        
        return $result;
    }
    
    public function searchContent($key, $quick, $page = 1) {
        $result = array();
        $videos = array();
        
        try {
            if (empty($key)) return $result;
            
            $encodedKey = urlencode($key);
            $url = $this->siteUrl . "/index.php/vod/search/wd/{$encodedKey}/page/{$page}.html";
            $rsp = $this->fetch($url);
            
            if ($rsp) {
                preg_match_all('/<div\s+class="grid__item[^"]*">(.*?)<\/div>\s*<\/div>/s', $rsp, $items, PREG_SET_ORDER);
                
                foreach ($items as $item) {
                    $itemHtml = $item[1];
                    
                    preg_match('/<a\s+href="([^"]+)"/', $itemHtml, $hrefMatch);
                    preg_match('/<h3[^>]*>(.*?)<\/h3>/', $itemHtml, $titleMatch);
                    preg_match('/<img[^>]+(?:data-original|src)="([^"]+)"/', $itemHtml, $imgMatch);
                    preg_match('/<span\s+class="duration-video[^>]*>(.*?)<\/span>/', $itemHtml, $descMatch);
                    
                    if ($hrefMatch && $titleMatch) {
                        $videos[] = array(
                            'vod_id' => $hrefMatch[1],
                            'vod_name' => $titleMatch[1],
                            'vod_pic' => $imgMatch ? $imgMatch[1] : '',
                            'vod_remarks' => $descMatch ? $descMatch[1] : ''
                        );
                    }
                }
            }
        } catch (Exception $e) {
            // 错误处理
        }
        
        $result['list'] = $videos;
        return $result;
    }
    
    public function playerContent($flag, $id, $vipFlags) {
        $result = array();
        
        try {
            if (empty($id)) return $result;
            
            // 如果已经是m3u8链接，直接使用
            if (strpos($id, 'http') === 0 && strpos($id, '.m3u8') !== false) {
                $result["parse"] = 0;
                $result["playUrl"] = '';
                $result["url"] = $id;
                $result["header"] = array(
                    'User-Agent' => 'Mozilla/5.0 (iPhone; CPU iPhone OS like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                    'Referer' => $this->siteUrl . '/'
                );
            } else {
                // 否则从详情页提取
                $url = $this->siteUrl . (strpos($id, '/') === 0 ? $id : '/' . $id);
                $rsp = $this->fetch($url);
                
                if ($rsp) {
                    $playUrl = $this->extractPlayUrl($rsp);
                    
                    if ($playUrl) {
                        $result["parse"] = 0;
                        $result["playUrl"] = '';
                        $result["url"] = $playUrl;
                        $result["header"] = array(
                            'User-Agent' => 'Mozilla/5.0 (iPhone; CPU iPhone OS like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
                            'Referer' => $url
                        );
                    }
                }
            }
        } catch (Exception $e) {
            // 错误处理
        }
        
        return $result;
    }
    
    /**
     * 直接从分类页面获取播放地址（核心功能）
     */
    private function getDirectPlayUrl($videoPath) {
        try {
            $url = $this->siteUrl . (strpos($videoPath, '/') === 0 ? $videoPath : '/' . $videoPath);
            $rsp = $this->fetch($url);
            
            if ($rsp) {
                return $this->extractPlayUrl($rsp);
            }
        } catch (Exception $e) {
            // 静默失败，不影响主流程
        }
        
        return '';
    }
    
    /**
     * 从HTML内容中提取播放地址
     */
    private function extractPlayUrl($html) {
        $playUrl = '';
        
        // 方法1: 从HlsJsPlayer配置中提取
        if (preg_match('/let\s+player\s*=\s*new\s+HlsJsPlayer\s*\(\s*(\{.*?\})\s*\)/s', $html, $playerMatch)) {
            $playerConfig = $playerMatch[1];
            if (preg_match('/"url"\s*:\s*"([^"]+)"/', $playerConfig, $urlMatch)) {
                $playUrl = $urlMatch[1];
            }
        }
        
        // 方法2: 直接搜索m3u8链接
        if (empty($playUrl)) {
            if (preg_match('/https?:\/\/[^\s"\']+\.m3u8[^\s"\']*/', $html, $m3u8Match)) {
                $playUrl = $m3u8Match[0];
            }
        }
        
        // 方法3: 从iframe中提取
        if (empty($playUrl)) {
            if (preg_match('/<iframe[^>]+src="([^"]+)"/', $html, $iframeMatch)) {
                $playUrl = $iframeMatch[1];
            }
        }
        
        return $playUrl;
    }
    
    /**
     * 网络请求方法
     */
    private function fetch($url, $timeout = 10) {
        $ch = curl_init();
        curl_setopt_array($ch, array(
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => $timeout,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_USERAGENT => 'Mozilla/5.0 (iPhone; CPU iPhone OS like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ));
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode == 200 && !empty($response)) {
            return $response;
        }
        
        return false;
    }
    
    public function isVideoFormat($url) {
        return false;
    }
    
    public function manualVideoCheck() {
        return false;
    }
    
    public function localProxy($param) {
        return array();
    }
}

// 返回蜘蛛实例
return new LspCmSpider();
?>
<?php
/**
 * 月光影视 - PHP 版本
 * 基于甜圈短剧模板修改
 * 参考甜圈短剧的API调用方式
 */

class Spider extends BaseSpider {
    
    private $ahost = 'https://www.dzwhs.com';
    private $timeout = 5;
    private $headers = [];
    
    public function init($extend = '') {
        // 解析扩展配置
        if (!empty($extend)) {
            if (is_string($extend)) {
                $ext = json_decode($extend, true);
                if ($ext && is_array($ext)) {
                    // 设置主机
                    if (isset($ext['host']) && !empty($ext['host'])) {
                        $host = trim($ext['host']);
                        $this->ahost = rtrim($host, '/');
                    }
                    // 设置超时时间
                    if (isset($ext['timeout']) && is_numeric($ext['timeout']) && $ext['timeout'] > 0) {
                        $this->timeout = intval($ext['timeout']);
                    }
                }
            }
        }
        
        // 设置默认请求头
        $this->headers = [
            'User-Agent: Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language: zh-CN',
            'Referer: ' . $this->ahost,
        ];
        
        return '';
    }
    
    public function getName() {
        return '月光影视';
    }
    
    public function isVideoFormat($url) {
        return true;
    }
    
    public function manualVideoCheck() {
        return false;
    }
    
    public function destroy() {
    }
    
    // 辅助函数：清理字符串
    private function cleanStr($str) {
        if ($str === null || $str === '') {
            return '';
        }
        
        $str = strval($str);
        $str = str_replace(['&nbsp;', ' '], ' ', $str);
        $str = trim($str);
        $str = preg_replace('/\s+/', ' ', $str);
        return $str;
    }
    
    // 辅助函数：正则提取
    private function pregMatch($pattern, $content, $default = '') {
        if (preg_match($pattern, $content, $matches)) {
            return isset($matches[1]) ? $this->cleanStr($matches[1]) : $default;
        }
        return $default;
    }
    
    // 辅助函数：获取HTML内容（使用简单curl）
    private function getHtml($url) {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $this->headers);
        
        $response = curl_exec($ch);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            error_log("获取页面失败 {$url}: {$error}");
            return '';
        }
        
        return $response ?: '';
    }
    
    // 获取视频列表 - 优化版本
    private function getVodList($html) {
        if (empty($html)) {
            return [];
        }
        
        $vods = [];
        
        // 主要匹配模式：匹配视频卡片
        $patterns = [
            // 模式1：完整的视频卡片匹配
            '/<div[^>]*class="[^"]*stui-vodlist__box[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>.*?<img[^>]*(?:data-original|src)="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*(?:pic-text|text-right)[^"]*"[^>]*>([^<]*)<\/span>/is',
            
            // 模式2：简化的视频卡片匹配
            '/<a[^>]*class="[^"]*lazyload[^"]*"[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*(?:data-original|src)="([^"]*)"[^>]*>.*?<span[^>]*class="[^"]*(?:pic-text|text-right)[^"]*"[^>]*>([^<]*)<\/span>/is',
        ];
        
        $allVideos = [];
        
        foreach ($patterns as $pattern) {
            if (preg_match_all($pattern, $html, $matches, PREG_SET_ORDER)) {
                foreach ($matches as $match) {
                    $href = $match[1] ?? '';
                    $title = $match[2] ?? '';
                    $pic = $match[3] ?? '';
                    $remarks = $match[4] ?? '';
                    
                    $href = $this->cleanStr($href);
                    $title = $this->cleanStr($title);
                    $pic = $this->cleanStr($pic);
                    $remarks = $this->cleanStr($remarks);
                    
                    // 过滤掉预告片
                    if (strpos($title, '预告片') !== false || strpos($remarks, '预告') !== false) {
                        continue;
                    }
                    
                    if ($href && $title) {
                        // 清理备注信息
                        if (empty($remarks)) {
                            $remarks = '已完结';
                        } else {
                            // 统一备注格式
                            $remarks = $this->cleanRemarks($remarks);
                        }
                        
                        $allVideos[] = [
                            'href' => $href,
                            'title' => $title,
                            'pic' => $pic,
                            'remarks' => $remarks
                        ];
                    }
                }
                
                if (!empty($allVideos)) {
                    break;
                }
            }
        }
        
        // 转换为最终格式
        foreach ($allVideos as $video) {
            $vods[] = [
                'vod_id' => "{$video['href']}@{$video['title']}@{$video['pic']}@{$video['remarks']}",
                'vod_name' => $video['title'],
                'vod_pic' => $video['pic'],
                'vod_remarks' => $video['remarks'],
                'vod_year' => null
            ];
        }
        
        return $vods;
    }
    
    // 清理备注信息
    private function cleanRemarks($remarks) {
        if (empty($remarks)) {
            return '已完结';
        }
        
        $remarks = $this->cleanStr($remarks);
        
        // 常见的备注格式处理
        $patterns = [
            '/更新至高清/' => '已完结',
            '/HD国语/' => '已完结',
            '/HD中字/' => '已完结',
            '/TC国语/' => '已完结',
            '/DVD国语/' => '已完结',
            '/更新至第(\d+)集/' => '更新中',
            '/已完结/' => '已完结',
            '/全(\d+)集/' => '已完结',
            '/预告片/' => '预告片',
            '/预告/' => '预告片',
        ];
        
        foreach ($patterns as $pattern => $replacement) {
            if (preg_match($pattern, $remarks)) {
                return $replacement;
            }
        }
        
        // 默认返回原备注
        return $remarks;
    }
    
    public function homeContent($filter = false) {
        try {
            // 获取首页内容
            $html = $this->getHtml($this->ahost);
            
            if (empty($html)) {
                return ['class' => [], 'filters' => []];
            }
            
            // 尝试提取分类 - 多种模式
            $classes = [];
            
            // 模式1：type-slide 元素
            if (preg_match_all('/<a[^>]*href="[^"]*\/(\d+)[^"]*"[^>]*class="[^"]*type-slide[^"]*"[^>]*>([^<]*)<\/a>/i', $html, $matches, PREG_SET_ORDER)) {
                foreach ($matches as $match) {
                    $classId = $this->cleanStr($match[1]);
                    $className = $this->cleanStr($match[2]);
                    
                    if ($classId && $className && $classId != '1') {
                        $classes[] = [
                            'type_id' => $classId,
                            'type_name' => $className
                        ];
                    }
                }
            }
            
            // 模式2：查找导航菜单
            if (empty($classes)) {
                if (preg_match_all('/<li[^>]*>.*?<a[^>]*href="[^"]*\/(\d+)[^"]*"[^>]*>([^<]*)<\/a>.*?<\/li>/i', $html, $matches, PREG_SET_ORDER)) {
                    foreach ($matches as $match) {
                        $classId = $this->cleanStr($match[1]);
                        $className = $this->cleanStr($match[2]);
                        
                        if ($classId && $className && $classId != '1' && !in_array($className, ['首页', '最新', '推荐'])) {
                            $classes[] = [
                                'type_id' => $classId,
                                'type_name' => $className
                            ];
                        }
                    }
                }
            }
            
            // 如果没有找到分类，使用默认分类
            if (empty($classes)) {
                $classes = [
                    ['type_id' => '6', 'type_name' => '动作片'],
                    ['type_id' => '7', 'type_name' => '喜剧片'],
                    ['type_id' => '8', 'type_name' => '爱情片'],
                    ['type_id' => '9', 'type_name' => '科幻片'],
                    ['type_id' => '10', 'type_name' => '恐怖片'],
                    ['type_id' => '11', 'type_name' => '剧情片'],
                    ['type_id' => '12', 'type_name' => '战争片'],
                    ['type_id' => '13', 'type_name' => '纪录片'],
                    ['type_id' => '14', 'type_name' => '悬疑片'],
                    ['type_id' => '15', 'type_name' => '犯罪片'],
                    ['type_id' => '16', 'type_name' => '奇幻片'],
                    ['type_id' => '17', 'type_name' => '国产剧'],
                    ['type_id' => '18', 'type_name' => '港台剧'],
                    ['type_id' => '20', 'type_name' => '日韩剧'],
                    ['type_id' => '21', 'type_name' => '欧美剧'],
                    ['type_id' => '22', 'type_name' => '海外剧'],
                    ['type_id' => '23', 'type_name' => '大陆综艺'],
                    ['type_id' => '24', 'type_name' => '日韩综艺'],
                    ['type_id' => '25', 'type_name' => '欧美综艺'],
                    ['type_id' => '26', 'type_name' => '港台综艺'],
                    ['type_id' => '27', 'type_name' => '国产动漫'],
                    ['type_id' => '28', 'type_name' => '日韩动漫'],
                    ['type_id' => '29', 'type_name' => '欧美动漫'],
                    ['type_id' => '30', 'type_name' => '其他动漫'],
                    ['type_id' => '31', 'type_name' => '动画片'],
                    //['type_id' => '32', 'type_name' => '预告片'],
                ];
            }
            
            // 定义筛选器（保持与Node.js版本一致）
            $filters = [
                "1" => [
                    ["key" => "cateId", "name" => "类型", "value" => [
                        ["n" => "全部", "v" => "全部"],
                        ["n" => "动作片", "v" => "6"],
                        ["n" => "喜剧片", "v" => "7"],
                        ["n" => "爱情片", "v" => "8"],
                        ["n" => "科幻片", "v" => "9"],
                        ["n" => "恐怖片", "v" => "10"],
                        ["n" => "剧情片", "v" => "11"],
                        ["n" => "战争片", "v" => "12"],
                        ["n" => "纪录片", "v" => "13"],
                        ["n" => "悬疑片", "v" => "14"],
                        ["n" => "犯罪片", "v" => "15"],
                        ["n" => "奇幻片", "v" => "16"],
                        ["n" => "动画片", "v" => "31"],
                        ["n" => "预告片", "v" => "32"]
                    ]]
                ],
                "2" => [
                    ["key" => "cateId", "name" => "类型", "value" => [
                        ["n" => "全部", "v" => "全部"],
                        ["n" => "国产剧", "v" => "17"],
                        ["n" => "港台剧", "v" => "18"],
                        ["n" => "日韩剧", "v" => "20"],
                        ["n" => "欧美剧", "v" => "21"],
                        ["n" => "海外剧", "v" => "22"]
                    ]]
                ],
                "3" => [
                    ["key" => "cateId", "name" => "类型", "value" => [
                        ["n" => "全部", "v" => "全部"],
                        ["n" => "大陆综艺", "v" => "23"],
                        ["n" => "日韩综艺", "v" => "24"],
                        ["n" => "欧美综艺", "v" => "25"],
                        ["n" => "港台综艺", "v" => "26"]
                    ]]
                ],
                "4" => [
                    ["key" => "cateId", "name" => "类型", "value" => [
                        ["n" => "全部", "v" => "全部"],
                        ["n" => "国产动漫", "v" => "27"],
                        ["n" => "日韩动漫", "v" => "28"],
                        ["n" => "欧美动漫", "v" => "29"],
                        ["n" => "其他动漫", "v" => "30"]
                    ]]
                ]
            ];
            
            return [
                'class' => $classes,
                'filters' => $filters
            ];
            
        } catch (Exception $e) {
            error_log('获取分类失败: ' . $e->getMessage());
            return ['class' => [], 'filters' => []];
        }
    }
    
    public function homeVideoContent() {
        try {
            $html = $this->getHtml($this->ahost);
            $vods = $this->getVodList($html);
            
            return ['list' => $vods];
        } catch (Exception $e) {
            error_log('推荐页获取失败: ' . $e->getMessage());
            return ['list' => []];
        }
    }
    
    public function categoryContent($tid, $pg, $filter, $extend) {
        try {
            $page = intval($pg) ?: 1;
            $cateId = $tid;
            
            // 解析extend参数
            if (!empty($extend)) {
                if (is_string($extend)) {
                    $ext = json_decode($extend, true);
                    if ($ext && is_array($ext) && isset($ext['cateId']) && $ext['cateId'] !== '全部') {
                        $cateId = $ext['cateId'];
                    }
                }
            }
            
            $url = $this->ahost . "/zwhstp/{$cateId}-{$page}.html";
            $html = $this->getHtml($url);
            
            $vods = $this->getVodList($html);
            
            return [
                'list' => $vods,
                'page' => $page,
                'pagecount' => 999,
                'limit' => 30,
                'total' => 30 * 999
            ];
        } catch (Exception $e) {
            error_log('类别页获取失败: ' . $e->getMessage());
            return [
                'list' => [],
                'page' => 1,
                'pagecount' => 0,
                'limit' => 30,
                'total' => 0
            ];
        }
    }
    
    public function detailContent($ids) {
        try {
            $id = $ids[0];
            if (empty($id)) {
                return ['list' => []];
            }
            
            // 解析ID
            $parts = explode('@', $id);
            $href = $parts[0] ?? '';
            $kname = $parts[1] ?? '未知';
            $kpic = $parts[2] ?? '';
            $kremarks = $parts[3] ?? '';
            
            // 构建详情页URL
            if (!preg_match('/^https?:\/\//', $href)) {
                $detailUrl = $this->ahost . $href;
            } else {
                $detailUrl = $href;
            }
            
            $html = $this->getHtml($detailUrl);
            if (empty($html)) {
                return ['list' => []];
            }
            
            // 使用正则提取信息
            $intro = $this->pregMatch('/<div[^>]*class="[^"]*stui-content[^"]*"[^>]*>(.*?)<\/div>/is', $html, '');
            
            // 提取播放线路和集数 - 专门修复国产剧问题
            $tabs = [];
            $playUrls = [];
            
            // 首先，确定这是电影还是电视剧
            $isSeries = $this->isSeriesVideo($kname, $html, $detailUrl);
            
            error_log("视频名称: {$kname}, 是否电视剧: " . ($isSeries ? '是' : '否'));
            
            // 国产剧的特殊处理
            if ($isSeries && strpos($kname, '剧') !== false) {
                $episodes = $this->extractChineseSeriesEpisodes($html, $detailUrl);
                if (!empty($episodes)) {
                    $tabs[] = '高清线路';
                    $playUrls[] = implode('#', $episodes);
                    error_log("国产剧提取到集数: " . count($episodes));
                }
            } else {
                // 普通视频的提取逻辑
                $this->extractNormalVideoEpisodes($html, $detailUrl, $tabs, $playUrls, $isSeries);
            }
            
            // 如果没有找到播放列表，尝试通用方法
            if (empty($tabs)) {
                error_log("使用通用方法提取播放列表");
                $this->extractGenericEpisodes($html, $detailUrl, $tabs, $playUrls, $isSeries);
            }
            
            // 如果没有找到线路，使用默认
            if (empty($tabs)) {
                $tabs = ['播放线路1'];
                if ($isSeries) {
                    // 国产剧生成模拟集数
                    $playUrls = [$this->generateChineseSeriesEpisodes($detailUrl, $kname)];
                } else {
                    $playUrls = ["HD国语\${$detailUrl}"];
                }
            }
            
            // 提取详细信息
            $type_name = $this->pregMatch('/类型[：:]\s*([^<]+)/', $intro, '电影');
            $vod_year = $this->pregMatch('/年份[：:]\s*([^<]+)/', $intro, '2023');
            $vod_area = $this->pregMatch('/地区[：:]\s*([^<]+)/', $intro, '中国大陆');
            $vod_director = $this->pregMatch('/导演[：:]\s*([^<]+)/', $intro, '未知');
            $vod_actor = $this->pregMatch('/主演[：:]\s*([^<]+)/', $intro, '未知');
            $vod_content = $this->pregMatch('/简介[：:]\s*([^<]+)/', $intro, $kname);
            
            // 调试日志
            error_log("视频类型: " . ($isSeries ? '电视剧' : '电影'));
            error_log("提取到线路: " . implode(', ', $tabs));
            error_log("提取到播放URL数量: " . count($playUrls));
            foreach ($playUrls as $index => $url) {
                error_log("线路 {$tabs[$index]}: " . substr($url, 0, 100));
            }
            
            // 构建VOD信息
            $vod = [
                'vod_id' => $detailUrl,
                'vod_name' => $kname,
                'vod_pic' => $kpic,
                'type_name' => $type_name,
                'vod_remarks' => $kremarks,
                'vod_year' => $vod_year,
                'vod_area' => $vod_area,
                'vod_lang' => '国语',
                'vod_director' => $vod_director,
                'vod_actor' => $vod_actor,
                'vod_content' => $vod_content,
                'vod_play_from' => implode('$$$', $tabs),
                'vod_play_url' => implode('$$$', $playUrls)
            ];
            
            return ['list' => [$vod]];
        } catch (Exception $e) {
            error_log('详情页获取失败: ' . $e->getMessage());
            return ['list' => []];
        }
    }
    
    // 判断是否是电视剧
    private function isSeriesVideo($title, $html, $url) {
        // 根据标题判断
        if (preg_match('/(剧|连续剧|电视剧|系列剧|剧集)$/i', $title)) {
            return true;
        }
        
        // 根据页面内容判断
        if (preg_match('/第[一二三四五六七八九十\d]+集|集数|全集|更新至第\d+集/i', $html)) {
            return true;
        }
        
        // 根据URL判断
        if (preg_match('/\/tv\/|\/series\/|\/drama\//i', $url)) {
            return true;
        }
        
        // 根据备注判断
        if (preg_match('/更新至第\d+集|全\d+集/', $html)) {
            return true;
        }
        
        return false;
    }
    
    // 专门提取国产剧集数
    private function extractChineseSeriesEpisodes($html, $detailUrl) {
        $episodes = [];
        
        error_log("开始提取国产剧集数...");
        
        // 方法1：查找国产剧特有的播放列表
        if (preg_match_all('/<div[^>]*class="[^"]*stui-pannel__head[^"]*"[^>]*>.*?<h3[^>]*class="[^"]*title[^"]*"[^>]*>([^<]*)<\/h3>.*?<\/div>.*?<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)<\/ul>/is', $html, $sectionMatches)) {
            for ($i = 0; $i < count($sectionMatches[0]); $i++) {
                $tabName = $this->cleanStr($sectionMatches[1][$i]);
                $ulContent = $sectionMatches[2][$i];
                
                error_log("找到播放区域: {$tabName}");
                
                if (preg_match_all('/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/i', $ulContent, $episodeMatches)) {
                    for ($j = 0; $j < count($episodeMatches[0]); $j++) {
                        $episodeUrl = $this->cleanStr($episodeMatches[1][$j]);
                        $episodeName = $this->cleanStr($episodeMatches[2][$j]);
                        
                        // 清理集数名称
                        $episodeName = str_replace(['<span class="text-muted">', '</span>', '预告', '片花'], '', $episodeName);
                        $episodeName = trim($episodeName);
                        
                        // 如果名称为空或者是数字，转换为"第X集"
                        if (empty($episodeName) || is_numeric($episodeName)) {
                            $episodeName = '第' . ($j + 1) . '集';
                        }
                        
                        // 跳过预告片
                        if (strpos($episodeName, '预告') !== false || strpos($episodeName, '片花') !== false) {
                            continue;
                        }
                        
                        if ($episodeUrl && $episodeName) {
                            // 处理相对URL
                            if (!preg_match('/^https?:\/\//', $episodeUrl)) {
                                $episodeUrl = $this->ahost . $episodeUrl;
                            }
                            $episodes[] = "{$episodeName}\${$episodeUrl}";
                            error_log("提取到剧集: {$episodeName} -> {$episodeUrl}");
                        }
                    }
                }
            }
        }
        
        // 方法2：直接查找所有播放列表
        if (empty($episodes)) {
            if (preg_match_all('/<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)<\/ul>/is', $html, $playlistMatches)) {
                foreach ($playlistMatches[1] as $index => $playlistHtml) {
                    if (preg_match_all('/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/i', $playlistHtml, $episodeMatches)) {
                        for ($j = 0; $j < count($episodeMatches[0]); $j++) {
                            $episodeUrl = $this->cleanStr($episodeMatches[1][$j]);
                            $episodeName = $this->cleanStr($episodeMatches[2][$j]);
                            
                            $episodeName = str_replace(['<span class="text-muted">', '</span>'], '', $episodeName);
                            $episodeName = trim($episodeName);
                            
                            // 如果是数字，转换为"第X集"
                            if (is_numeric($episodeName)) {
                                $episodeName = '第' . $episodeName . '集';
                            } elseif (empty($episodeName)) {
                                $episodeName = '第' . ($j + 1) . '集';
                            }
                            
                            // 跳过预告片
                            if (strpos($episodeName, '预告') !== false) {
                                continue;
                            }
                            
                            if ($episodeUrl && $episodeName) {
                                if (!preg_match('/^https?:\/\//', $episodeUrl)) {
                                    $episodeUrl = $this->ahost . $episodeUrl;
                                }
                                $episodes[] = "{$episodeName}\${$episodeUrl}";
                            }
                        }
                    }
                }
            }
        }
        
        // 方法3：查找国产剧详情页特有的集数信息
        if (empty($episodes) && preg_match('/<div[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>.*?第(\d+)[集季].*?<\/a>/is', $html, $epMatches)) {
            for ($i = 1; $i <= 40; $i++) { // 假设最多40集
                $episodeName = '第' . $i . '集';
                $episodeUrl = str_replace('-1-1', '-' . $i . '-1', $detailUrl);
                $episodes[] = "{$episodeName}\${$episodeUrl}";
            }
        }
        
        // 去重
        $episodes = array_unique($episodes);
        
        error_log("国产剧提取结果: 共" . count($episodes) . "集");
        
        return $episodes;
    }
    
    // 提取普通视频的选集
    private function extractNormalVideoEpisodes($html, $detailUrl, &$tabs, &$playUrls, $isSeries) {
        // 查找所有的播放线路div
        if (preg_match_all('/<div[^>]*class="[^"]*stui-pannel-box b playlist mb[^"]*"[^>]*>(.*?)<\/div>\s*<\/div>/is', $html, $playlistDivs)) {
            error_log("找到播放线路div数量: " . count($playlistDivs[0]));
            
            foreach ($playlistDivs[0] as $playlistDiv) {
                // 提取线路名称
                $tabName = '';
                if (preg_match('/<h3[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)<\/h3>/i', $playlistDiv, $tabMatches)) {
                    $tabName = $this->cleanStr($tabMatches[1]);
                    // 去掉可能的图标文字
                    $tabName = preg_replace('/<img[^>]*>/', '', $tabName);
                    $tabName = trim($tabName);
                }
                
                if (empty($tabName)) {
                    $tabName = '播放线路' . (count($tabs) + 1);
                }
                
                // 提取该线路的播放集数
                $episodes = [];
                if (preg_match('/<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)<\/ul>/is', $playlistDiv, $ulMatches)) {
                    $ulContent = $ulMatches[1];
                    if (preg_match_all('/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/i', $ulContent, $episodeMatches)) {
                        for ($i = 0; $i < count($episodeMatches[0]); $i++) {
                            $episodeUrl = $this->cleanStr($episodeMatches[1][$i]);
                            $episodeName = $this->cleanStr($episodeMatches[2][$i]);
                            
                            // 清理集数名称
                            $episodeName = str_replace(['<span class="text-muted">', '</span>'], '', $episodeName);
                            $episodeName = trim($episodeName);
                            
                            // 如果是电视剧且名称是数字，转换为"第X集"
                            if ($isSeries && is_numeric($episodeName)) {
                                $episodeName = '第' . $episodeName . '集';
                            }
                            
                            // 如果名称为空且是电影，使用"HD国语"等默认名称
                            if (empty($episodeName) && !$isSeries) {
                                if (preg_match('/HD/i', $tabName)) {
                                    $episodeName = 'HD国语';
                                } elseif (preg_match('/高清/i', $tabName)) {
                                    $episodeName = '高清';
                                } else {
                                    $episodeName = 'HD';
                                }
                            }
                            
                            // 跳过预告片
                            if (strpos($episodeName, '预告') !== false) {
                                continue;
                            }
                            
                            if ($episodeUrl && $episodeName) {
                                // 处理相对URL
                                if (!preg_match('/^https?:\/\//', $episodeUrl)) {
                                    $episodeUrl = $this->ahost . $episodeUrl;
                                }
                                $episodes[] = "{$episodeName}\${$episodeUrl}";
                            }
                        }
                    }
                }
                
                if (!empty($episodes)) {
                    $tabs[] = $tabName;
                    $playUrls[] = implode('#', $episodes);
                    error_log("线路 {$tabName} 找到集数: " . count($episodes));
                }
            }
        }
    }
    
    // 通用提取方法
    private function extractGenericEpisodes($html, $detailUrl, &$tabs, &$playUrls, $isSeries) {
        // 直接查找所有的播放列表
        if (preg_match_all('/<ul[^>]*class="[^"]*stui-content__playlist[^"]*"[^>]*>(.*?)<\/ul>/is', $html, $playlistMatches)) {
            foreach ($playlistMatches[1] as $index => $playlistHtml) {
                $episodes = [];
                if (preg_match_all('/<a[^>]*href="([^"]*)"[^>]*>(.*?)<\/a>/i', $playlistHtml, $episodeMatches)) {
                    for ($i = 0; $i < count($episodeMatches[0]); $i++) {
                        $episodeUrl = $this->cleanStr($episodeMatches[1][$i]);
                        $episodeName = $this->cleanStr($episodeMatches[2][$i]);
                        
                        $episodeName = str_replace(['<span class="text-muted">', '</span>'], '', $episodeName);
                        $episodeName = trim($episodeName);
                        
                        // 如果是电视剧且名称是数字，转换为"第X集"
                        if ($isSeries && is_numeric($episodeName)) {
                            $episodeName = '第' . $episodeName . '集';
                        }
                        
                        // 如果名称为空且是电影，使用默认名称
                        if (empty($episodeName) && !$isSeries) {
                            $episodeName = 'HD国语';
                        }
                        
                        // 跳过预告片
                        if (strpos($episodeName, '预告') !== false) {
                            continue;
                        }
                        
                        if ($episodeUrl && $episodeName) {
                            if (!preg_match('/^https?:\/\//', $episodeUrl)) {
                                $episodeUrl = $this->ahost . $episodeUrl;
                            }
                            $episodes[] = "{$episodeName}\${$episodeUrl}";
                        }
                    }
                }
                
                if (!empty($episodes)) {
                    $tabs[] = '播放线路' . ($index + 1);
                    $playUrls[] = implode('#', $episodes);
                }
            }
        }
    }
    
    // 生成国产剧模拟集数
    private function generateChineseSeriesEpisodes($baseUrl, $seriesName) {
        $episodes = [];
        
        // 国产剧通常有较多集数，假设30-40集
        $totalEpisodes = 40;
        
        for ($i = 1; $i <= $totalEpisodes; $i++) {
            $episodeName = '第' . $i . '集';
            // 生成模拟的剧集URL（基于基础URL）
            $episodeUrl = preg_replace('/(-1-1\.html|\.html)$/', '-' . $i . '-1.html', $baseUrl);
            if ($episodeUrl === $baseUrl) {
                $episodeUrl = $baseUrl . '-' . $i;
            }
            $episodes[] = "{$episodeName}\${$episodeUrl}";
        }
        
        return implode('#', $episodes);
    }
    
    public function searchContent($key, $quick, $pg = '1') {
        try {
            $page = intval($pg) ?: 1;
            $encodedWd = urlencode($key);
            $url = $this->ahost . "/zwhstp/id.html?wd={$encodedWd}&page={$page}";
            
            $html = $this->getHtml($url);
            $vods = $this->getVodList($html);
            
            return [
                'list' => $vods,
                'page' => $page,
                'pagecount' => 10,
                'limit' => 30,
                'total' => 300
            ];
        } catch (Exception $e) {
            error_log('搜索页获取失败: ' . $e->getMessage());
            return [
                'list' => [],
                'page' => 1,
                'pagecount' => 0,
                'limit' => 30,
                'total' => 0
            ];
        }
    }
    
    public function playerContent($flag, $id, $vipFlags) {
        try {
            // 构建播放URL
            if (!preg_match('/^https?:\/\//', $id)) {
                $playUrl = $this->ahost . $id;
            } else {
                $playUrl = $id;
            }
            
            error_log("月光影视获取播放URL: {$playUrl}");
            
            $parse = 1; // 默认需要解析
            $finalUrl = '';
            
            // 尝试获取播放页内容
            $html = $this->getHtml($playUrl);
            
            if (empty($html)) {
                error_log("获取播放页失败: {$playUrl}");
                return [
                    'parse' => 0,
                    'url' => $playUrl,
                    'header' => [
                        'User-Agent' => 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
                        'Referer' => $this->ahost,
                    ]
                ];
            }
            
            // 模式1：直接匹配 var player_aaaa = {...}
            if (preg_match('/var\s+player_[a-zA-Z0-9_]+\s*=\s*(\{.*?\})\s*;/s', $html, $matches)) {
                $jsonStr = $matches[1];
                error_log("找到JSON字符串: " . substr($jsonStr, 0, 200));
                
                $data = json_decode($jsonStr, true);
                if ($data && isset($data['url']) && !empty($data['url'])) {
                    $extractedUrl = $data['url'];
                    
                    // 解码可能的URL编码和转义字符
                    $extractedUrl = stripslashes($extractedUrl);
                    $extractedUrl = urldecode($extractedUrl);
                    
                    error_log("提取到URL: {$extractedUrl}");
                    
                    // 检查是否是有效的视频链接
                    if (preg_match('/\.(m3u8|mp4|mkv|flv|avi|mov|wmv|ts)/i', $extractedUrl)) {
                        $parse = 0; // 直接播放
                        $finalUrl = $extractedUrl;
                        error_log("直接播放URL: {$finalUrl}");
                    } else {
                        $parse = 1; // 需要解析
                        $finalUrl = $extractedUrl;
                        error_log("需要解析URL: {$finalUrl}");
                    }
                } else {
                    error_log("JSON解析失败或没有URL字段");
                }
            }
            
            // 模式2：匹配 player_aaaa = {...}（没有var）
            if (empty($finalUrl) && preg_match('/player_[a-zA-Z0-9_]+\s*=\s*(\{.*?\})\s*;/s', $html, $matches)) {
                $jsonStr = $matches[1];
                error_log("找到JSON字符串(无var): " . substr($jsonStr, 0, 200));
                
                $data = json_decode($jsonStr, true);
                if ($data && isset($data['url']) && !empty($data['url'])) {
                    $extractedUrl = $data['url'];
                    $extractedUrl = stripslashes($extractedUrl);
                    $extractedUrl = urldecode($extractedUrl);
                    
                    if (preg_match('/\.(m3u8|mp4|mkv|flv|avi|mov|wmv|ts)/i', $extractedUrl)) {
                        $parse = 0;
                        $finalUrl = $extractedUrl;
                    } else {
                        $parse = 1;
                        $finalUrl = $extractedUrl;
                    }
                }
            }
            
            // 模式3：从script标签中提取m3u8链接
            if (empty($finalUrl)) {
                if (preg_match_all('/<script[^>]*>(.*?)<\/script>/is', $html, $scriptMatches)) {
                    foreach ($scriptMatches[1] as $scriptContent) {
                        if (preg_match('/"url"\s*:\s*"([^"]+\.(m3u8|mp4))"/i', $scriptContent, $urlMatches)) {
                            $extractedUrl = $urlMatches[1];
                            $extractedUrl = stripslashes($extractedUrl);
                            $extractedUrl = urldecode($extractedUrl);
                            
                            if (preg_match('/\.(m3u8|mp4|mkv|flv|avi|mov|wmv|ts)/i', $extractedUrl)) {
                                $parse = 0;
                                $finalUrl = $extractedUrl;
                                break;
                            }
                        }
                    }
                }
            }
            
            // 如果还是没有找到视频URL，返回原始页面URL并设置parse=1让播放器解析
            if (empty($finalUrl)) {
                error_log("未找到视频URL，返回原始页面URL: {$playUrl}");
                $parse = 1;
                $finalUrl = $playUrl;
            }
            
            // 调试日志
            error_log("月光影视播放URL解析结果: parse={$parse}, url={$finalUrl}");
            
            return [
                'parse' => $parse,
                'url' => $finalUrl,
                'header' => [
                    'User-Agent' => 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
                    'Referer' => $this->ahost,
                ]
            ];
        } catch (Exception $e) {
            error_log('播放失败: ' . $e->getMessage());
            return [
                'parse' => 0,
                'url' => '',
                'header' => []
            ];
        }
    }
    
    public function localProxy($param) {
        return null;
    }
}
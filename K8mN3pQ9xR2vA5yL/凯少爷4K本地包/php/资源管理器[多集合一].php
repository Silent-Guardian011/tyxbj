<?php
/**
 * 本地浏览 + 列表文件虚拟目录 + 本地看图增强版
 * - m3u/txt/json/magnets/db 在分类页显示为“目录”
 * - 进入后展示链接项，点击链接项才播放
 * - 支持本地图片单张查看
 * - 支持“本目录看图”（pics:// 多图聚合）
 * - 支持磁力链接(magnet)和数据库文件(db)
 * - vdir/vitem/ialbum 与播放URL使用 b64u 编码，避免特殊字符壳解析错误
 * - 兼容旧版 base64 的 vdir/vitem/ialbum
 * - 完全独立运行，内置 HtmlParser 和 BaseSpider
 */

// ==================== HtmlParser 类 ====================
class HtmlParser {
    
    /**
     * Parse HTML and return array of OuterHTML strings
     */
    public function pdfa($html, $rule) {
        if (empty($html) || empty($rule)) return [];
        $doc = $this->getDom($html);
        $xpath = new DOMXPath($doc);
        
        $xpathQuery = $this->parseRuleToXpath($rule);
        $nodes = $xpath->query($xpathQuery);
        
        $res = [];
        if ($nodes) {
            foreach ($nodes as $node) {
                // saveHTML($node) returns OuterHTML
                $res[] = $doc->saveHTML($node);
            }
        }
        return $res;
    }

    /**
     * Parse HTML and return single value (Text, Html, or Attribute)
     */
    public function pdfh($html, $rule, $baseUrl = '') {
        if (empty($html) || empty($rule)) return '';
        $doc = $this->getDom($html);
        $xpath = new DOMXPath($doc);

        // Separate Option
        $option = '';
        if (strpos($rule, '&&') !== false) {
            $parts = explode('&&', $rule);
            $option = array_pop($parts);
            $rule = implode('&&', $parts);
        }

        $xpathQuery = $this->parseRuleToXpath($rule);
        $nodes = $xpath->query($xpathQuery);
        
        if ($nodes && $nodes->length > 0) {
            // Special handling for Text option: concatenate all nodes
            if ($option === 'Text') {
                $text = '';
                foreach ($nodes as $node) {
                    $text .= $node->textContent;
                }
                return $this->parseText($text);
            }
            
            // For other options, use the first node
            $node = $nodes->item(0);
            return $this->formatOutput($doc, $node, $option, $baseUrl);
        }
        return '';
    }
    
    /**
     * Parse HTML and return URL (auto joined)
     */
    public function pd($html, $rule, $baseUrl = '') {
        $res = $this->pdfh($html, $rule, $baseUrl);
        return $this->urlJoin($baseUrl, $res);
    }

    // --- Helper Methods ---

    private function parseText($text) {
        // Match JS behavior: 
        // text = text.replace(/[\s]+/gm, '\n');
        // text = text.replace(/\n+/g, '\n').replace(/^\s+/, '');
        // text = text.replace(/\n/g, ' ');
        
        $text = preg_replace('/[\s]+/u', "\n", $text);
        $text = preg_replace('/\n+/', "\n", $text);
        $text = trim($text);
        $text = str_replace("\n", ' ', $text);
        return $text;
    }

    private function parseRuleToXpath($rule) {
        // Replace && with space to unify as descendant separator
        $rule = str_replace('&&', ' ', $rule);
        $parts = explode(' ', $rule);
        $xpathParts = [];
        
        foreach ($parts as $part) {
            if (empty($part)) continue;
            $xpathParts[] = $this->transSingleSelector($part);
        }
        
        // Join with descendant axis
        return '//' . implode('//', $xpathParts);
    }

    private function transSingleSelector($selector) {
        // Handle :eq
        $position = null;
        if (preg_match('/:eq\((-?\d+)\)/', $selector, $matches)) {
            $idx = intval($matches[1]);
            $selector = str_replace($matches[0], '', $selector);
            if ($idx >= 0) {
                $position = $idx + 1; // XPath is 1-based
            } else {
                // -1 is last()
                // -2 is last()-1
                $offset = abs($idx) - 1;
                $position = "last()" . ($offset > 0 ? "-$offset" : ""); 
            }
        }
        
        // Handle tag.class#id
        $tag = '*';
        $conditions = [];
        
        // Extract id
        if (preg_match('/#([\w-]+)/', $selector, $m)) {
            $conditions[] = '@id="' . $m[1] . '"';
            $selector = str_replace($m[0], '', $selector);
        }
        
        // Extract classes
        if (preg_match_all('/\.([\w-]+)/', $selector, $m)) {
            foreach ($m[1] as $cls) {
                $conditions[] = 'contains(concat(" ", normalize-space(@class), " "), " ' . $cls . ' ")';
            }
            $selector = preg_replace('/\.[\w-]+/', '', $selector);
        }
        
        // Remaining is tag
        if (!empty($selector)) {
            $tag = $selector;
        }
        
        $xpath = $tag;
        if (!empty($conditions)) {
            $xpath .= '[' . implode(' and ', $conditions) . ']';
        }
        if ($position !== null) {
            $xpath .= '[' . $position . ']';
        }
        
        return $xpath;
    }

    private function formatOutput($doc, $node, $option, $baseUrl) {
        if ($option === 'Text') {
            return $this->parseText($node->textContent);
        } elseif ($option === 'Html') {
            return $doc->saveHTML($node);
        } elseif ($option) {
            // Attribute
            $val = $node->getAttribute($option);
            // Handle style url() extraction if needed? JS does it.
            // JS: if (contains(opt, 'style') && contains(ret, 'url(')) ...
            return $val;
        }
        // Default to outer HTML if no option provided
        return $doc->saveHTML($node);
    }

    private function getDom($html) {
        $doc = new DOMDocument();
        // Suppress warnings for malformed HTML
        libxml_use_internal_errors(true);
        // Force UTF-8 encoding
        if (!empty($html) && mb_detect_encoding($html, 'UTF-8', true) === false) {
             $html = mb_convert_encoding($html, 'UTF-8', 'GBK, BIG5'); 
        }
        // Add meta charset to ensure DOMDocument treats it as UTF-8
        $html = '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">' . $html;
        
        $doc->loadHTML($html);
        libxml_clear_errors();
        return $doc;
    }

    private function urlJoin($baseUrl, $relativeUrl) {
        if (empty($relativeUrl)) return '';
        if (preg_match('#^https?://#', $relativeUrl)) return $relativeUrl;
        
        if (empty($baseUrl)) return $relativeUrl;

        $parts = parse_url($baseUrl);
        $scheme = isset($parts['scheme']) ? $parts['scheme'] . '://' : 'http://';
        $host = isset($parts['host']) ? $parts['host'] : '';
        
        if (substr($relativeUrl, 0, 1) == '/') {
            return $scheme . $host . $relativeUrl;
        }
        
        // Relative path
        $path = isset($parts['path']) ? $parts['path'] : '/';
        $dir = rtrim(dirname($path), '/\\');
        if ($dir === '/' || $dir === '\\') $dir = ''; // handle root
        
        return $scheme . $host . $dir . '/' . $relativeUrl;
    }
}

// ==================== BaseSpider 抽象类 ====================
abstract class BaseSpider {
    
    // 默认请求头
    protected $headers = [
        'User-Agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept' => 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language' => 'zh-CN,zh;q=0.9',
    ];

    /**
     * @var HtmlParser
     */
    protected $htmlParser;

    public function __construct() {
        $this->htmlParser = new HtmlParser();
    }

    /**
     * 初始化方法
     * @param string $extend 扩展参数
     */
    public function init($extend = '') {
        // 子类实现
    }

    /**
     * 获取首页分类
     * @param array $filter 筛选条件
     * @return array
     */
    public function homeContent($filter) {
        return ['class' => []];
    }

    /**
     * 获取首页推荐视频
     * @return array
     */
    public function homeVideoContent() {
        return ['list' => []];
    }

    /**
     * 获取分类详情
     * @param string $tid 分类ID
     * @param int $pg 页码
     * @param array $filter 筛选条件
     * @param array $extend 扩展参数
     * @return array
     */
    public function categoryContent($tid, $pg = 1, $filter = [], $extend = []) {
        return ['list' => [], 'page' => $pg, 'pagecount' => 1, 'limit' => 20, 'total' => 0];
    }

    /**
     * 获取视频详情
     * @param array $ids 视频ID列表
     * @return array
     */
    public function detailContent($ids) {
        return ['list' => []];
    }

    /**
     * 搜索视频
     * @param string $key 关键词
     * @param bool $quick 快速搜索
     * @param int $pg 页码
     * @return array
     */
    public function searchContent($key, $quick = false, $pg = 1) {
        return ['list' => []];
    }

    /**
     * 获取播放地址
     * @param string $flag 播放线路
     * @param string $id 视频播放ID
     * @param array $vipFlags VIP标识
     * @return array
     */
    public function playerContent($flag, $id, $vipFlags = []) {
        return ['parse' => 0, 'url' => '', 'header' => []];
    }

    /**
     * 代理请求 (可选)
     * @param array $params
     * @return mixed
     */
    public function localProxy($params) {
        return null;
    }

    /**
     * 执行 Action (可选)
     * @param string $action 动作名称
     * @param string $value 参数值
     * @return mixed
     */
    public function action($action, $value) {
        return '';
    }

    // ================== 辅助方法 ==================

    protected function pdfa($html, $rule) {
        return $this->htmlParser->pdfa($html, $rule);
    }
    
    protected function pdfh($html, $rule, $baseUrl = '') {
        return $this->htmlParser->pdfh($html, $rule, $baseUrl);
    }
    
    protected function pd($html, $rule, $baseUrl = '') {
        if (empty($baseUrl)) {
            $baseUrl = $this->tryGetHost();
        }
        return $this->htmlParser->pd($html, $rule, $baseUrl);
    }

    /**
     * 尝试获取子类定义的 HOST 常量或属性
     */
    private function tryGetHost() {
        try {
            $ref = new ReflectionClass($this);

            // 1. 尝试获取 HOST 属性 (优先)
            if ($ref->hasProperty('HOST')) {
                $prop = $ref->getProperty('HOST');
                // PHP 8.1+ 默认可访问私有属性，只有旧版本需要手动开启
                if (PHP_VERSION_ID < 80100) {
                    $prop->setAccessible(true);
                }
                $val = $prop->getValue($this);
                if (!empty($val)) {
                    return $val;
                }
            }

            // 2. 尝试获取 const HOST 常量
            if ($ref->hasConstant('HOST')) {
                return $ref->getConstant('HOST');
            }
        } catch (Exception $e) {
            // ignore
        }
        return '';
    }

    /**
     * 快速构建分页返回结果
     * @param array $list 视频列表
     * @param int $pg 当前页码
     * @param int $total 总记录数 (可选)
     * @param int $limit 每页条数 (默认 20)
     * @return array
     */
    protected function pageResult($list, $pg, $total = 0, $limit = 20) {
        $pg = max(1, intval($pg));
        $count = count($list);
        
        if ($total > 0) {
            $pagecount = ceil($total / $limit);
        } else {
            // 如果没有提供 total，尝试根据当前列表数量估算
            if ($count < $limit) {
                // 当前页数据少于限制，说明是最后一页
                $pagecount = $pg;
                $total = ($pg - 1) * $limit + $count;
            } else {
                // 还有下一页，设置一个较大的页数
                $pagecount = 9999;
                $total = 99999;
            }
        }
        
        return [
            'list' => $list,
            'page' => $pg,
            'pagecount' => intval($pagecount),
            'limit' => intval($limit),
            'total' => intval($total)
        ];
    }

    /**
     * 封装 HTTP 请求
     * @param string $url 请求地址
     * @param array $options CURL 选项
     * @param array $headers 请求头
     * @return string|bool
     */
    protected function fetch($url, $options = [], $headers = []) {
        // 支持从 options 中传递 headers
        if (isset($options['headers'])) {
            $headers = array_merge($headers, $options['headers']);
            unset($options['headers']);
        }

        $ch = curl_init();
        
        // 1. 解析自定义 header 为关联数组
        $customHeaders = [];
        foreach ($headers as $k => $v) {
            if (is_numeric($k)) {
                // 处理 "Key: Value" 格式
                $parts = explode(':', $v, 2);
                if (count($parts) === 2) {
                    $key = trim($parts[0]);
                    $value = trim($parts[1]);
                    $customHeaders[$key] = $value;
                }
            } else {
                $customHeaders[$k] = $v;
            }
        }

        // 2. 合并请求头 (自定义覆盖默认)
        $finalHeadersMap = array_merge($this->headers, $customHeaders);

        // 3. 转换回 CURL 所需的索引数组
        $mergedHeaders = [];
        foreach ($finalHeadersMap as $k => $v) {
            if ($v === "") {
                // To send empty header in CURL, use "Header;" (no colon)
                $mergedHeaders[] = $k . ";";
            } else {
                $mergedHeaders[] = "$k: $v";
            }
        }

        $defaultOptions = [
            CURLOPT_URL => $url,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_SSL_VERIFYPEER => false,
            CURLOPT_SSL_VERIFYHOST => false,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_TIMEOUT => 15,
            CURLOPT_ENCODING => '', // 支持 GZIP 自动解压
            CURLOPT_HTTPHEADER => $mergedHeaders,
        ];

        // 处理 POST 数据
        if (isset($options['body'])) {
            $defaultOptions[CURLOPT_POST] = true;
            $defaultOptions[CURLOPT_POSTFIELDS] = $options['body'];
            unset($options['body']);
        }
        
        // 处理 Cookie
        if (isset($options['cookie'])) {
            $defaultOptions[CURLOPT_COOKIE] = $options['cookie'];
            unset($options['cookie']);
        }

        // 合并用户自定义选项
        foreach ($options as $k => $v) {
            $defaultOptions[$k] = $v;
        }

        curl_setopt_array($ch, $defaultOptions);
        $result = curl_exec($ch);
        
        if (is_resource($ch)) {
            curl_close($ch);
        }
        
        return $result;
    }

    protected function fetchJson($url, $options = []) {
        $resp = $this->fetch($url, $options);
        return json_decode($resp, true) ?: [];
    }

    /**
     * 自动运行，处理路由
     */
    public function run() {
        $ac = $_GET['ac'] ?? '';
        $t = $_GET['t'] ?? '';
        $pg = $_GET['pg'] ?? '1';
        $wd = $_GET['wd'] ?? '';
        $ids = $_GET['ids'] ?? '';
        $play = $_GET['play'] ?? ''; // 某些源使用 play 参数传递播放ID
        $flag = $_GET['flag'] ?? ''; // 播放线路
        $filter = isset($_GET['filter']) && $_GET['filter'] === 'true'; // 是否过滤
        $extend = $_GET['ext'] ?? ''; // 扩展参数
        if (!empty($extend) && is_string($extend)) {
            $decoded = json_decode(base64_decode($extend), true);
            if (is_array($decoded)) {
                $extend = $decoded;
            }
        }
        $action = $_GET['action'] ?? ''; // Action 动作
        $value = $_GET['value'] ?? ''; // Action 参数

        $this->init($extend);

        try {
            // 0. Action (优先处理)
            if ($ac === 'action') {
                echo json_encode($this->action($action, $value), JSON_UNESCAPED_UNICODE);
                return;
            }

            // 1. 播放 (Play)
            // 优先检测 play 参数或 ac=play
            if ($ac === 'play' || !empty($play)) {
                $playId = !empty($play) ? $play : ($_GET['id'] ?? '');
                echo json_encode($this->playerContent($flag, $playId), JSON_UNESCAPED_UNICODE);
                return;
            }

            // 2. 搜索 (Search)
            // 有 wd 则是搜索
            if (!empty($wd)) {
                echo json_encode($this->searchContent($wd, false, $pg), JSON_UNESCAPED_UNICODE);
                return;
            }

            // 3. 详情 (Detail)
            // 有 ids 且 ac 不为空
            if (!empty($ids) && !empty($ac)) {
                // ids 可能是逗号分隔的字符串
                $idList = explode(',', $ids);
                echo json_encode($this->detailContent($idList), JSON_UNESCAPED_UNICODE);
                return;
            }

            // 4. 分类 (Category)
            // 有 t 且 ac 不为空
            if ($t !== '' && !empty($ac)) {
                // 处理 filter
                $filterData = []; // 暂未实现复杂 filter 解析，可根据需要扩展
                echo json_encode($this->categoryContent($t, $pg, $filterData, $extend), JSON_UNESCAPED_UNICODE);
                return;
            }

            // 5. 首页 (默认)
            // 通常返回 {class: [...], list: [...]}
            // 可以分别调用 homeContent 和 homeVideoContent 合并
            $homeData = $this->homeContent($filter);
            $videoData = $this->homeVideoContent();
            
            $result = [
                'class' => $homeData['class'] ?? [],
            ];
            
            // 如果 homeContent 只有 class，合并 homeVideoContent 的 list
            if (isset($videoData['list'])) {
                $result['list'] = $videoData['list'];
            }
            // 如果 homeContent 也有 list，优先使用 homeContent 的 list (视具体逻辑而定，这里简单的合并)
            if (isset($homeData['list']) && !empty($homeData['list'])) {
                $result['list'] = $homeData['list'];
            }
            // 兼容：如果 homeContent 返回了 filters
            if (isset($homeData['filters'])) {
                $result['filters'] = $homeData['filters'];
            }

            echo json_encode($result, JSON_UNESCAPED_UNICODE);

        } catch (Exception $e) {
            echo json_encode(['code' => 500, 'msg' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
        } catch (Throwable $e) {
            echo json_encode(['code' => 500, 'msg' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
        }
    }
}

// ==================== 数据库读取类 ====================
class DatabaseReader {
    
    private $dbCache = [];
    
    /**
     * 读取SQLite数据库，根据实际数据库结构智能解析
     * @param string $dbPath 数据库文件路径
     * @param int $limit 限制返回条数
     * @return array
     */
    public function readSQLite($dbPath, $limit = 1000) {
        // 检查缓存
        $cacheKey = $dbPath . '_' . $limit;
        if (isset($this->dbCache[$cacheKey])) {
            return $this->dbCache[$cacheKey];
        }
        
        $result = [];
        
        if (!file_exists($dbPath) || !is_readable($dbPath)) {
            return $result;
        }
        
        try {
            $pdo = new PDO('sqlite:' . $dbPath);
            $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
            
            // 获取所有表名
            $tables = $pdo->query("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name NOT LIKE 'android_%'")->fetchAll(PDO::FETCH_COLUMN);
            
            foreach ($tables as $table) {
                // 跳过元数据表
                if (in_array($table, ['android_metadata', 'db_config', 'meta', 'crawl_state', 'sqlite_sequence'])) {
                    continue;
                }
                
                // 获取表结构
                $columns = $pdo->query("PRAGMA table_info(" . $pdo->quote($table) . ")")->fetchAll();
                $columnNames = array_column($columns, 'name');
                
                // 根据表名和字段智能解析
                $items = $this->parseTableByStructure($pdo, $table, $columnNames, $limit);
                $result = array_merge($result, $items);
                
                if (count($result) >= $limit) {
                    $result = array_slice($result, 0, $limit);
                    break;
                }
            }
            
        } catch (Exception $e) {
            // 忽略错误
        }
        
        // 存入缓存
        $this->dbCache[$cacheKey] = $result;
        
        return $result;
    }
    
    /**
     * 根据表结构智能解析
     */
private function parseTableByStructure($pdo, $table, $columnNames, $limit) {
    $result = [];
    
    // 1. 标准VOD格式 (vod_play_url)
    if (in_array('vod_play_url', $columnNames)) {
        $titleField   = $this->findBestMatch($columnNames, ['vod_name', 'name', 'title']);
        $urlField     = 'vod_play_url';
        $picField     = $this->findBestMatch($columnNames, ['vod_pic', 'pic', 'image']);
        $remarksField = $this->findBestMatch($columnNames, ['vod_remarks', 'remarks']);
        $fromField    = $this->findBestMatch($columnNames, ['vod_play_from', 'play_from']);

        if ($titleField && $urlField) {
            $query = "SELECT * FROM {$table} WHERE {$urlField} IS NOT NULL AND {$urlField} != '' LIMIT {$limit}";
            $rows = $pdo->query($query)->fetchAll();

            foreach ($rows as $row) {
                $playUrlRaw = trim($row[$urlField] ?? '');
                if ($playUrlRaw === '') continue;

                $name = trim($row[$titleField] ?? '未命名');
                $from = trim($row[$fromField] ?? ($row['type_name'] ?? '默认线路'));
                $remarks = trim($row[$remarksField] ?? '');

                // 给电视剧自动加个“共X集”提示（可选）
                $epCount = $this->countVodEpisodes($playUrlRaw);
                if ($remarks === '' && $epCount > 1) {
                    $remarks = '共' . $epCount . '集';
                }

                // 关键：不拆分，整条交给上层 detail 再拆
                $result[] = [
                    'name' => $name,
                    'url' => '',
                    'play_url' => $playUrlRaw,
                    'from' => $from,
                    'pic' => $row[$picField] ?? '',
                    'remarks' => $remarks
                ];
            }
        }
    }
    // 2. 简单格式 (name, url)
    elseif (in_array('name', $columnNames) && in_array('url', $columnNames)) {
        $query = "SELECT name, url FROM {$table} WHERE url IS NOT NULL AND url != '' LIMIT {$limit}";
        $rows = $pdo->query($query)->fetchAll();

        foreach ($rows as $row) {
            $result[] = [
                'name' => $row['name'] ?? '未命名',
                'url' => $row['url'],
                'pic' => '',
                'remarks' => ''
            ];
        }
    }
    // 3. 歌曲格式 (song_name, url)
    elseif (in_array('song_name', $columnNames) && in_array('url', $columnNames)) {
        $query = "SELECT song_name as name, url FROM {$table} WHERE url IS NOT NULL AND url != '' LIMIT {$limit}";
        $rows = $pdo->query($query)->fetchAll();

        foreach ($rows as $row) {
            $result[] = [
                'name' => $row['name'] ?? '未命名',
                'url' => $row['url'],
                'pic' => '',
                'remarks' => ''
            ];
        }
    }
    // 4. 标题+URL格式 (title, play_url)
    elseif (in_array('title', $columnNames) && in_array('play_url', $columnNames)) {
        $query = "SELECT title as name, play_url as url FROM {$table} WHERE play_url IS NOT NULL AND play_url != '' LIMIT {$limit}";
        $rows = $pdo->query($query)->fetchAll();

        foreach ($rows as $row) {
            $result[] = [
                'name' => $row['name'] ?? '未命名',
                'url' => $row['url'],
                'pic' => '',
                'remarks' => ''
            ];
        }
    }
    // 5. 通用尝试
    else {
        $titleField = $this->findBestMatch($columnNames, ['name', 'title', 'vod_name', 'song_name', 'video_name', 'movie_name', 'nickname', 'label']);
        $urlField   = $this->findBestMatch($columnNames, ['url', 'link', 'play_url', 'vod_url', 'video_url', 'magnet', 'path', 'file_path', 'src']);
        $picField   = $this->findBestMatch($columnNames, ['pic', 'image', 'vod_pic', 'cover', 'thumbnail', 'poster']);

        if ($titleField && $urlField) {
            $query = "SELECT * FROM {$table} WHERE {$urlField} IS NOT NULL AND {$urlField} != '' LIMIT {$limit}";
            $rows = $pdo->query($query)->fetchAll();

            foreach ($rows as $row) {
                $url = trim($row[$urlField] ?? '');
                if ($url === '') continue;

                // 像VOD多集格式的字符串：不拆分，交给上层
                if (strpos($url, '$') !== false && (strpos($url, '#') !== false || strpos($url, '$$$') !== false)) {
                    $epCount = $this->countVodEpisodes($url);
                    $result[] = [
                        'name' => $row[$titleField] ?? '未命名',
                        'url' => '',
                        'play_url' => $url,
                        'from' => '默认线路',
                        'pic' => $row[$picField] ?? '',
                        'remarks' => $epCount > 1 ? ('共' . $epCount . '集') : ''
                    ];
                } else {
                    $result[] = [
                        'name' => $row[$titleField] ?? '未命名',
                        'url' => $url,
                        'pic' => $row[$picField] ?? '',
                        'remarks' => ''
                    ];
                }
            }
        }
    }

    return $result;
}

private function countVodEpisodes($playUrlRaw) {
    $playUrlRaw = trim((string)$playUrlRaw);
    if ($playUrlRaw === '') return 0;

    $groups = array_values(array_filter(array_map('trim', explode('$$$', $playUrlRaw))));
    if (empty($groups)) $groups = [$playUrlRaw];

    $total = 0;
    foreach ($groups as $g) {
        $eps = array_values(array_filter(array_map('trim', explode('#', $g))));
        if (empty($eps)) continue;
        $total += count($eps);
    }

    return max(1, $total);
}
    /**
     * 解析VOD播放URL格式
     * 格式: 名称1$url1#名称2$url2#名称3$url3
     */
    public function parseVodPlayUrl($playUrl) {
        $result = [];
        
        if (empty($playUrl)) return $result;
        
        // 按#分割多线路
        $lines = explode('#', $playUrl);
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            // 按$分割名称和URL
            $parts = explode('$', $line, 2);
            if (count($parts) == 2) {
                $name = trim($parts[0]);
                $url = trim($parts[1]);
                
                // 进一步处理多集格式（有些源会用$$$分隔）
                if (strpos($url, '$$$') !== false) {
                    $episodes = explode('$$$', $url);
                    foreach ($episodes as $index => $epUrl) {
                        $result[] = [
                            'name' => $name . ' 第' . ($index + 1) . '集',
                            'url' => trim($epUrl)
                        ];
                    }
                } else {
                    $result[] = [
                        'name' => $name,
                        'url' => $url
                    ];
                }
            } else {
                // 没有名称，只有URL
                $result[] = [
                    'name' => '线路' . (count($result) + 1),
                    'url' => $line
                ];
            }
        }
        
        return $result;
    }
    
    /**
     * 从列名中找出最佳匹配
     */
    private function findBestMatch($columnNames, $candidates) {
        $candidates = is_array($candidates) ? $candidates : [$candidates];
        
        foreach ($candidates as $candidate) {
            foreach ($columnNames as $col) {
                if (stripos($col, $candidate) !== false) {
                    return $col;
                }
            }
        }
        
        return null;
    }
    
    /**
     * 判断是否为可播放URL
     */
    public function isPlayableUrl($url) {
        $url = strtolower(trim($url));
        return (
            strpos($url, 'http://') === 0 ||
            strpos($url, 'https://') === 0 ||
            strpos($url, 'magnet:?') === 0 ||
            strpos($url, 'rtmp://') === 0 ||
            strpos($url, 'rtsp://') === 0 ||
            strpos($url, 'udp://') === 0 ||
            strpos($url, 'rtp://') === 0 ||
            strpos($url, 'file://') === 0 ||
            strpos($url, 'pics://') === 0 ||
            strpos($url, 'thunder://') === 0 ||
            strpos($url, 'ed2k://') === 0
        );
    }
}

// ==================== Spider 主类 ====================
class Spider extends BaseSpider
{
    /* ▲◆★定义管理器的初始目录★◆▲ */
    private $ROOT = [
        '/storage/emulated/0/江湖/wj/',
        '/storage/emulated/0/mt2/apks/vid/',
        '/storage/emulated/0/mt2/apks/pic/',
        '/storage/emulated/0/peekpili/我的收藏/'
    ];

    private $V_DIR_PREFIX = 'vdir://';
    private $V_ITEM_PREFIX = 'vitem://';
    private $I_ALBUM_PREFIX = 'ialbum://';
    private $URL_B64U_PREFIX = 'b64u://';

    private $MEDIA_EXTS = ['mp4', 'mkv', 'mp3', 'flv', 'avi', 'rmvb', 'mov', 'wmv', 'm4v', 'ts', 'm3u8'];
    private $IMAGE_EXTS = ['jpg', 'jpeg', 'png', 'webp', 'gif', 'bmp', 'ico', 'svg'];
    private $MAGNET_EXTS = ['magnets', 'magnet', 'torrent']; // 磁力链接列表文件
    private $DB_EXTS = ['db', 'sqlite', 'sqlite3']; // 数据库文件

    private $dbReader;

    public function init($extend = '')
    {
        if (!empty($extend)) {
            if (is_array($extend)) {
                $this->ROOT = $extend;
            } else {
                $this->ROOT = [rtrim($extend, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR];
            }
        }
        $this->dbReader = new DatabaseReader();
    }

    public function homeContent($filter = [])
    {
        $class = [];
        foreach ($this->ROOT as $index => $root) {
            $name = basename(rtrim($root, DIRECTORY_SEPARATOR));
            $class[] = [
                'type_id' => 'root_' . $index,
                'type_name' => $name
            ];
        }
        return ['class' => $class];
    }

    public function homeVideoContent()
    {
        $list = [];
        foreach ($this->ROOT as $index => $root) {
            $content = $this->categoryContent('root_' . $index, 1);
            if (isset($content['list'])) {
                // 只取前10个作为推荐
                $list = array_merge($list, array_slice($content['list'], 0, 10));
            }
        }
        return ['list' => $list];
    }

    public function categoryContent($tid, $pg = 1, $filter = [], $extend = [])
    {
        // 0) 虚拟目录（m3u/txt/json/magnets/db）
        if ($this->isVirtualDir($tid)) {
            return $this->buildVirtualDirCategory($tid, $pg);
        }

        // 1) 图片聚合目录（本目录看图）
        if ($this->isImageAlbum($tid)) {
            return $this->buildImageAlbumCategory($tid, $pg);
        }

        // 2) 根目录选择
        if (preg_match('/^root_(\d+)$/', $tid, $matches)) {
            $index = intval($matches[1]);
            if (isset($this->ROOT[$index])) {
                $path = $this->ROOT[$index];
            } else {
                return ['list' => []];
            }
        } else {
            // 3) 实体目录
            $path = $tid;
        }
        $path = rtrim($path, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR;

        if (strpos($path, 'back_dir_') === 0) {
            $path = substr($path, 9);
        }

        if (!is_dir($path)) return ['list' => []];
        
        // 分页处理
        $itemsPerPage = 50;
        $offset = ($pg - 1) * $itemsPerPage;

        $list = [];

        $realPath = realpath($path);
        $rootIndex = $this->getRootIndex($path);
        $realRoot = ($rootIndex !== null) ? realpath($this->ROOT[$rootIndex]) : null;

        // 返回上一级（只在第一页显示）
        if ($pg == 1 && $rootIndex !== null && $realPath !== $realRoot && $realPath !== '/') {
            $parentPath = dirname($realPath);
            $targetId = (strlen($parentPath) < strlen($realRoot)) ? 'root_' . $rootIndex : $parentPath;

            $list[] = [
                'vod_id' => 'back_dir_' . $targetId,
                'type_id' => $targetId,
                'vod_tag' => 'folder',
                'vod_name' => '⬅️ 返回上一级',
                'vod_pic' => $this->getIcon('back', ''),
                'style' => ['type' => 'grid', 'spancount' => 4, 'ratio' => 2, 'titletextsize' => 13],
                'vod_remarks' => '点击回到上层'
            ];
        }

        // 当前目录图片集合（用于“本目录看图”入口）- 只在第一页显示
        if ($pg == 1) {
            $imageFiles = $this->collectImagesInDir($path);
            if (!empty($imageFiles)) {
                $cover = $imageFiles[0]; // file://...
                $albumId = $this->encodeImageAlbum($realPath ?: $path);
                $list[] = [
                    'vod_id' => $albumId,
                    'type_id' => $albumId,
                    'vod_tag' => 'folder',
                    'vod_name' => '🖼️ 本目录看图',
                    'vod_pic' => $cover,
                    'style' => ['type' => 'list'],
                    'vod_remarks' => count($imageFiles) . ' 张图片'
                ];
            }
        }

        // 遍历（自然排序）
        $files = $this->scanDirNatural($path);
        
        // 计算总数用于分页
        $totalFiles = count($files);
        $files = array_slice($files, $offset, $itemsPerPage);
        
        foreach ($files as $file) {
            if ($file === '.' || $file === '..') continue;

            $fullPath = $path . $file;
            $realFullPath = realpath($fullPath) ?: $fullPath;
            $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));

            if (is_dir($realFullPath)) {
                $list[] = [
                    'vod_id' => $realFullPath,
                    'type_id' => $realFullPath,
                    'vod_tag' => 'folder',
                    'vod_name' => '📁 ' . $file,
                    'vod_pic' => $this->getIcon('dir', $realFullPath),
                    'style' => ['type' => 'list'],
                    'vod_remarks' => '进入目录'
                ];
            } elseif (in_array($ext, array_merge(['m3u', 'txt', 'json'], $this->MAGNET_EXTS, $this->DB_EXTS))) {
                // 列表文件 -> 模拟目录
                $vdir = $this->encodeVirtualDir($realFullPath);
                $iconType = $ext;
                $remarks = '进入列表';
                
                if (in_array($ext, $this->MAGNET_EXTS)) {
                    $remarks = '磁力链接列表';
                    $iconType = 'magnet';
                } elseif ($ext === 'db' || $ext === 'sqlite' || $ext === 'sqlite3') {
                    $remarks = '数据库文件';
                    $iconType = 'database';
                } elseif ($ext === 'json') {
                    $remarks = 'JSON数据';
                    $iconType = 'json';
                }
                
                $list[] = [
                    'vod_id' => $vdir,
                    'type_id' => $vdir,
                    'vod_tag' => 'folder',
                    'vod_name' => '📂 ' . $file,
                    'vod_pic' => $this->getIcon($iconType, $realFullPath),
                    'style' => ['type' => 'list'],
                    'vod_remarks' => $remarks
                ];
            } elseif (in_array($ext, $this->MEDIA_EXTS)) {
                // 普通媒体文件
                $list[] = [
                    'vod_id' => $realFullPath,
                    'vod_name' => '📄 ' . $file,
                    'vod_pic' => $this->getIcon($ext, $realFullPath),
                    'style' => ['type' => 'list'],
                    'vod_remarks' => strtoupper($ext)
                ];
            } elseif (in_array($ext, $this->IMAGE_EXTS)) {
                // 本地图片文件（显示缩略图）
                $list[] = [
                    'vod_id' => $realFullPath,
                    'vod_name' => '🖼️ ' . $file,
                    'vod_pic' => 'file://' . $realFullPath,
                    'style' => ['type' => 'list'],
                    'vod_remarks' => strtoupper($ext)
                ];
            }
        }

        return [
            'page' => intval($pg),
            'pagecount' => ceil($totalFiles / $itemsPerPage),
            'limit' => $itemsPerPage,
            'total' => $totalFiles,
            'list' => $list
        ];
    }

public function detailContent($ids)
{
    $id = $ids[0] ?? '';

    // 0) 直接可播放的 b64u 链接
    if (strpos($id, $this->URL_B64U_PREFIX) === 0) {
        $decoded = $this->b64uDecode(substr($id, strlen($this->URL_B64U_PREFIX)));
        $from = $this->detectUrlType($decoded);

        return [
            'list' => [[
                'vod_id' => $id,
                'vod_name' => '播放',
                'vod_play_from' => $from,
                'vod_play_url' => '立即播放$' . $id
            ]]
        ];
    }

    // 1) 虚拟目录
    if ($this->isVirtualDir($id)) {
        return $this->categoryContent($id, 1);
    }

    // 2) 图片聚合目录
    if ($this->isImageAlbum($id)) {
        return $this->buildImageAlbumDetail($id);
    }

    // 3) 虚拟条目（这里新增支持 play_url 多集）
    if ($this->isVirtualItem($id)) {
        $item = $this->decodeVirtualItem($id);
        if (!$item) return ['list' => []];

        $title = trim($item['name'] ?? '未命名');
        $pic = $item['pic'] ?? '';
        $playUrlRaw = trim($item['play_url'] ?? '');
        $url = trim($item['url'] ?? '');

        // 优先处理多集/多线路
        if ($playUrlRaw !== '') {
            $playData = $this->buildSafeVodPlay(
                $item['from'] ?? '默认线路',
                $playUrlRaw,
                $title
            );

            return [
                'list' => [[
                    'vod_id' => $id,
                    'vod_name' => $title,
                    'vod_pic' => $pic,
                    'vod_play_from' => $playData['vod_play_from'],
                    'vod_play_url' => $playData['vod_play_url']
                ]]
            ];
        }

        // 单链接
        if ($url !== '') {
            $safeUrl = $this->URL_B64U_PREFIX . $this->b64uEncode($url);
            $from = $this->detectUrlType($url);

            return [
                'list' => [[
                    'vod_id' => $id,
                    'vod_name' => $title,
                    'vod_pic' => $pic,
                    'vod_play_from' => $from,
                    'vod_play_url' => $title . '$' . $safeUrl
                ]]
            ];
        }

        return ['list' => []];
    }

    // 4) 返回上一级
    if (strpos($id, 'back_dir_') === 0) {
        $targetPath = substr($id, 9);
        if (preg_match('/^root_(\d+)$/', $targetPath, $matches)) {
            return $this->categoryContent($targetPath, 1);
        }
        return $this->categoryContent($targetPath, 1);
    }

    // 5) 根目录选择
    if (preg_match('/^root_(\d+)$/', $id, $matches)) {
        return $this->categoryContent($id, 1);
    }

    // 6) 本地目录
    if ($this->isLocalPath($id) && is_dir($id)) {
        return $this->categoryContent($id, 1);
    }

    // 7) 磁力链接直接播放
    if (strpos($id, 'magnet:?') === 0) {
        $safeUrl = $this->URL_B64U_PREFIX . $this->b64uEncode($id);
        return [
            'list' => [[
                'vod_id' => $id,
                'vod_name' => $this->extractMagnetName($id),
                'vod_play_from' => '磁力链接',
                'vod_play_url' => '立即播放$' . $safeUrl
            ]]
        ];
    }

    // 8) YouTube播放列表
    if (strpos($id, 'PL') === 0 && strlen($id) > 20) {
        $safeUrl = $this->URL_B64U_PREFIX . $this->b64uEncode('https://www.youtube.com/playlist?list=' . $id);
        return [
            'list' => [[
                'vod_id' => $id,
                'vod_name' => 'YouTube播放列表',
                'vod_play_from' => 'YouTube',
                'vod_play_url' => '播放列表$' . $safeUrl
            ]]
        ];
    }

    // 9) 本地媒体/图片文件
    $name = basename($id);
    $ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));

    if (in_array($ext, $this->IMAGE_EXTS)) {
        $picsPayload = 'pics://' . 'file://' . $id;
        $safePayload = $this->URL_B64U_PREFIX . $this->b64uEncode($picsPayload);

        return [
            'list' => [[
                'vod_id' => $id,
                'vod_name' => $name,
                'vod_pic' => 'file://' . $id,
                'vod_play_from' => '本地看图',
                'vod_play_url' => '查看图片$' . $safePayload
            ]]
        ];
    }

    // 10) 普通文件
    $from = $this->detectUrlType($id);
    return [
        'list' => [[
            'vod_id' => $id,
            'vod_name' => $name,
            'vod_play_from' => $from,
            'vod_play_url' => '本地播放$file://' . $id
        ]]
    ];
}

    public function playerContent($flag, $id, $vipFlags = [])
    {
        $u = trim($id);

        // 容错：历史错误链路可能传入 file://b64u://...
        if (strpos($u, 'file://' . $this->URL_B64U_PREFIX) === 0) {
            $u = substr($u, 7); // 去掉 file://
        }

        // 还原 b64u://
        if (strpos($u, $this->URL_B64U_PREFIX) === 0) {
            $raw = substr($u, strlen($this->URL_B64U_PREFIX));
            $decoded = $this->b64uDecode($raw);
            if ($decoded !== false && $decoded !== null && $decoded !== '') {
                $u = $decoded;
            }
        }

        // 磁力链接直接返回
        if (strpos($u, 'magnet:?') === 0) {
            return [
                'parse' => 0,
                'url' => $u,
                'header' => [
                    'User-Agent' => 'Mozilla/5.0'
                ]
            ];
        }

        // YouTube播放列表
        if (strpos($u, 'youtube.com/playlist?list=') !== false) {
            return [
                'parse' => 0,
                'url' => $u,
                'header' => [
                    'User-Agent' => 'Mozilla/5.0'
                ]
            ];
        }

        // 本地绝对路径补 file://
        if ($this->isLocalPath($u) && strpos($u, 'file://') !== 0) {
            $u = 'file://' . $u;
        }

        return [
            'parse' => 0,
            'url' => $u,
            'header' => [
                'User-Agent' => 'Mozilla/5.0'
            ]
        ];
    }

    // =========================
    // 工具方法
    // =========================
    
    /**
     * 检测URL类型
     */
    private function detectUrlType($url) {
        if (strpos($url, 'magnet:?') === 0) return '磁力链接';
        if (strpos($url, 'thunder://') === 0) return '迅雷链接';
        if (strpos($url, 'ed2k://') === 0) return '电驴链接';
        if (strpos($url, 'youtube.com') !== false) return 'YouTube';
        if (strpos($url, 'bilibili.com') !== false) return 'B站';
        if (strpos($url, 'pics://') === 0) return '本地看图';
        if (strpos($url, 'file://') === 0) return '本地文件';
        if (strpos($url, 'http://') === 0 || strpos($url, 'https://') === 0) return '在线视频';
        return '默认线路';
    }

    /**
     * 从磁力链接提取名称
     */
    private function extractMagnetName($magnet) {
        if (preg_match('/dn=([^&]+)/', $magnet, $matches)) {
            return urldecode($matches[1]);
        }
        if (preg_match('/btih:([a-fA-F0-9]+)/i', $magnet, $matches)) {
            return '磁力链接 ' . substr($matches[1], 0, 8) . '...';
        }
        return '磁力链接';
    }

    // =========================
    // 图片聚合目录
    // =========================
    private function buildImageAlbumCategory($tid, $pg = 1)
    {
        if ($pg > 1) return ['page' => $pg, 'pagecount' => 0, 'list' => []];

        $dir = $this->decodeImageAlbum($tid);
        if ($dir === '' || !is_dir($dir)) return ['list' => []];

        $images = $this->collectImagesInDir($dir); // file://...
        $list = [];

        // 返回实体目录
        $parent = realpath($dir) ?: $dir;
        $list[] = [
            'vod_id' => 'back_dir_' . $parent,
            'type_id' => $parent,
            'vod_tag' => 'folder',
            'vod_name' => '⬅️ 返回文件目录',
            'vod_pic' => $this->getIcon('back', ''),
            'style' => ['type' => 'grid', 'cols' => 4, 'ratio' => 1.5],
            'vod_remarks' => '返回目录'
        ];

        // 一键播放全部
        if (!empty($images)) {
            $payload = 'pics://' . implode('&&', $images);
            $safePayload = $this->URL_B64U_PREFIX . $this->b64uEncode($payload);

            $list[] = [
                'vod_id' => $safePayload,
                'vod_name' => '🎞️ 幻灯播放（全部）',
                'vod_pic' => $images[0],
                'style' => ['type' => 'grid', 'ratio' => 1.1],
                'vod_remarks' => count($images) . ' 张'
            ];

            // 单张条目
            foreach ($images as $img) {
                $basename = basename(parse_url($img, PHP_URL_PATH) ?? $img);
                $singlePayload = 'pics://' . $img;
                $singleSafe = $this->URL_B64U_PREFIX . $this->b64uEncode($singlePayload);

                $list[] = [
                    'vod_id' => $singleSafe,
                    'vod_name' => '🖼️ ' . $basename,
                    'vod_pic' => $img,
                    'style' => ['type' => 'grid', 'cols' => 4, 'ratio' => 1.5],
                    'vod_remarks' => '单图查看'
                ];
            }
        }

        return [
            'page' => 1,
            'pagecount' => 0,
            'limit' => count($list),
            'total' => count($list),
            'list' => $list
        ];
    }

    private function buildImageAlbumDetail($id)
    {
        $dir = $this->decodeImageAlbum($id);
        if ($dir === '' || !is_dir($dir)) return ['list' => []];

        $images = $this->collectImagesInDir($dir); // file://...
        if (empty($images)) return ['list' => []];

        $payload = 'pics://' . implode('&&', $images);
        $safePayload = $this->URL_B64U_PREFIX . $this->b64uEncode($payload);

        $title = '本目录看图 - ' . basename(rtrim($dir, DIRECTORY_SEPARATOR));
        $vod = [
            'vod_id' => $id,
            'vod_name' => $title,
            'vod_pic' => $images[0],
            'vod_play_from' => '本地看图',
            'vod_play_url' => '幻灯播放（' . count($images) . '张）$' . $safePayload
        ];

        return ['list' => [$vod]];
    }

    private function encodeImageAlbum($dirPath)
    {
        return $this->I_ALBUM_PREFIX . $this->b64uEncode($dirPath);
    }

    private function decodeImageAlbum($tid)
    {
        $raw = substr($tid, strlen($this->I_ALBUM_PREFIX));

        $path = $this->b64uDecode($raw);
        if ($path === false || $path === null || $path === '') {
            $path = base64_decode($raw, true); // 兼容旧 base64
        }

        return $path ?: '';
    }

    private function isImageAlbum($tid)
    {
        return strpos($tid, $this->I_ALBUM_PREFIX) === 0;
    }

    // =========================
    // 虚拟目录构建
    // =========================
private function buildVirtualDirCategory($tid, $pg = 1)
{
    if ($pg > 1) return ['page' => $pg, 'pagecount' => 0, 'list' => []];

    $listFile = $this->decodeVirtualDir($tid);
    if ($listFile === '' || !is_file($listFile)) return ['list' => []];

    $ext = strtolower(pathinfo($listFile, PATHINFO_EXTENSION));
    $items = [];

    if ($ext === 'm3u') {
        $items = $this->parseM3uToItems($listFile);
    } elseif ($ext === 'txt') {
        $items = $this->parseTxtToItems($listFile);
    } elseif ($ext === 'json') {
        $items = $this->parseJsonToItems($listFile);
    } elseif (in_array($ext, $this->MAGNET_EXTS)) {
        $items = $this->parseMagnetsToItems($listFile);
    } elseif (in_array($ext, $this->DB_EXTS)) {
        $items = $this->parseDbToItems($listFile);
    }

    $list = [];

    // 返回到实体目录
    $parent = dirname(realpath($listFile) ?: $listFile);
    $list[] = [
        'vod_id' => 'back_dir_' . $parent,
        'type_id' => $parent,
        'vod_tag' => 'folder',
        'vod_name' => '⬅️ 返回上一级',
        'vod_pic' => $this->getIcon('back', ''),
        'style' => ['type' => 'grid', 'cols' => 4, 'ratio' => 1.5],
        'vod_remarks' => '返回文件目录'
    ];

    foreach ($items as $it) {
        $title = trim($it['name'] ?? '');
        $url = trim($it['url'] ?? '');
        $playUrlRaw = trim($it['play_url'] ?? '');
        $pic = $it['pic'] ?? '';
        $remarks = $it['remarks'] ?? '';

        // 允许“只有 play_url 没有 url”的多集条目
        if ($url === '' && $playUrlRaw === '') continue;

        $iconType = $url !== '' ? $this->getIconTypeFromUrl($url) : 'link';
        $remarksText = $remarks ?: ($url !== '' ? $this->getRemarksFromUrl($url) : '剧集/多线路');

        $list[] = [
            'vod_id' => $this->encodeVirtualItem(
                $title !== '' ? $title : '未命名',
                $url,
                $pic,
                [
                    'play_url' => $playUrlRaw,
                    'from' => $it['from'] ?? '',
                    'remarks' => $remarksText
                ]
            ),
            'vod_name' => '🎬 ' . ($title !== '' ? $title : '未命名'),
            'vod_pic' => $pic ?: $this->getIcon($iconType, ''),
            'style' => ['type' => 'grid', 'cols' => 4, 'ratio' => 1.5],
            'vod_remarks' => $remarksText
        ];
    }

    return [
        'page' => 1,
        'pagecount' => 0,
        'limit' => count($list),
        'total' => count($list),
        'list' => $list
    ];
}

    /**
     * 根据URL获取图标类型
     */
    private function getIconTypeFromUrl($url) {
        if (strpos($url, 'magnet:?') === 0) return 'magnet';
        if (strpos($url, 'thunder://') === 0) return 'thunder';
        if (strpos($url, 'youtube.com') !== false) return 'youtube';
        if (strpos($url, 'bilibili.com') !== false) return 'bilibili';
        if (strpos($url, '.m3u8') !== false) return 'm3u8';
        if (strpos($url, '.mp4') !== false) return 'mp4';
        return 'link';
    }

    /**
     * 根据URL获取备注
     */
    private function getRemarksFromUrl($url) {
        if (strpos($url, 'magnet:?') === 0) return '磁力链接';
        if (strpos($url, 'thunder://') === 0) return '迅雷链接';
        if (strpos($url, 'youtube.com') !== false) return 'YouTube';
        if (strpos($url, 'bilibili.com') !== false) return 'B站';
        if (strpos($url, '.m3u8') !== false) return 'M3U8';
        if (strpos($url, '.mp4') !== false) return 'MP4';
        return '链接项';
    }

    // =========================
    // 解析器
    // =========================
    private function parseM3uToItems($path)
    {
        $out = [];
        $fp = @fopen($path, 'r');
        if (!$fp) return $out;

        $currentTitle = '';
        $idx = 1;

        while (($line = fgets($fp)) !== false) {
            $line = trim($line);
            if ($line === '') continue;

            if (stripos($line, '#EXTINF:') === 0) {
                if (preg_match('/,\s*(.+)$/', $line, $m)) {
                    $currentTitle = trim($m[1]);
                } elseif (preg_match('/tvg-name="([^"]+)"/i', $line, $m2)) {
                    $currentTitle = trim($m2[1]);
                } else {
                    $currentTitle = '线路' . $idx;
                }
                continue;
            }

            if ($line[0] === '#') continue;

            $url = $line;
            if ($this->isPlayableUrl($url)) {
                $name = ($currentTitle !== '') ? $currentTitle : ('线路' . $idx);
                $out[] = ['name' => $name, 'url' => $url];
                $currentTitle = '';
                $idx++;
            }
        }

        fclose($fp);
        return $out;
    }

    private function parseTxtToItems($path)
    {
        $out = [];
        $fp = @fopen($path, 'r');
        if (!$fp) return $out;

        $idx = 1;
        while (($line = fgets($fp)) !== false) {
            $line = trim($line);
            if ($line === '') continue;
            if ($line[0] === '#') continue;
            if (strpos($line, '#genre#') !== false) continue;

            $name = '';
            $url = '';

            if (strpos($line, ',') !== false) {
                list($n, $u) = explode(',', $line, 2);
                $name = trim($n);
                $url = trim($u);
            } else {
                $name = '线路' . $idx;
                $url = $line;
            }

            if ($this->isPlayableUrl($url)) {
                $out[] = ['name' => ($name !== '' ? $name : ('线路' . $idx)), 'url' => $url];
                $idx++;
            }
        }

        fclose($fp);
        return $out;
    }

    /**
     * 解析JSON文件为播放项
     * 修复：正确解析vod_play_url字段并传递给播放器
     */
private function parseJsonToItems($path)
{
    $out = [];
    $content = @file_get_contents($path);
    if ($content === false || $content === '') return $out;

    $data = json_decode($content, true);
    if (!is_array($data)) return $out;

    // 支持 {list:[...]} 和直接数组
    $items = (isset($data['list']) && is_array($data['list'])) ? $data['list'] : $data;

    $idx = 1;
    foreach ($items as $item) {
        // 标准VOD：保留 vod_play_url 原样，不拆分
        if (is_array($item) && isset($item['vod_name']) && isset($item['vod_play_url'])) {
            $name = trim($item['vod_name'] ?? ('视频' . $idx));
            $playUrlRaw = trim($item['vod_play_url'] ?? '');
            if ($playUrlRaw === '') { $idx++; continue; }

            $out[] = [
                'name' => $name,
                'url' => '', // 电视剧多集走 play_url
                'play_url' => $playUrlRaw,
                'from' => $item['vod_play_from'] ?? '默认线路',
                'pic' => $item['vod_pic'] ?? '',
                'remarks' => $item['vod_remarks'] ?? ''
            ];
        }
        // 简单格式 {name,url}
        elseif (is_array($item) && isset($item['name']) && isset($item['url'])) {
            $out[] = [
                'name' => $item['name'],
                'url' => $item['url'],
                'pic' => $item['pic'] ?? $item['image'] ?? '',
                'remarks' => $item['remarks'] ?? ''
            ];
        }
        // 索引数组 [name,url,pic,remarks]
        elseif (is_array($item) && count($item) >= 2) {
            $out[] = [
                'name' => $item[0] ?? ('线路' . $idx),
                'url' => $item[1] ?? '',
                'pic' => $item[2] ?? '',
                'remarks' => $item[3] ?? ''
            ];
        }

        $idx++;
    }

    return $out;
}
    /**
     * 解析VOD播放URL格式
     * 格式: 名称1$url1#名称2$url2#名称3$url3
     */
    private function parseVodPlayUrl($playUrl) {
        $result = [];
        
        if (empty($playUrl)) return $result;
        
        // 按#分割多线路
        $lines = explode('#', $playUrl);
        
        foreach ($lines as $line) {
            $line = trim($line);
            if (empty($line)) continue;
            
            // 按$分割名称和URL
            $parts = explode('$', $line, 2);
            if (count($parts) == 2) {
                $name = trim($parts[0]);
                $url = trim($parts[1]);
                
                // 进一步处理多集格式（有些源会用$$$分隔）
                if (strpos($url, '$$$') !== false) {
                    $episodes = explode('$$$', $url);
                    foreach ($episodes as $index => $epUrl) {
                        $result[] = [
                            'name' => $name . ' 第' . ($index + 1) . '集',
                            'url' => trim($epUrl)
                        ];
                    }
                } else {
                    $result[] = [
                        'name' => $name,
                        'url' => $url
                    ];
                }
            } else {
                // 没有名称，只有URL
                $result[] = [
                    'name' => '线路' . (count($result) + 1),
                    'url' => $line
                ];
            }
        }
        
        return $result;
    }

    /**
     * 解析磁力链接列表文件
     */
    private function parseMagnetsToItems($path)
    {
        $out = [];
        $fp = @fopen($path, 'r');
        if (!$fp) return $out;

        $idx = 1;
        while (($line = fgets($fp)) !== false) {
            $line = trim($line);
            if ($line === '') continue;
            if ($line[0] === '#') continue;

            $name = '';
            $url = '';

            // 格式1: 标题, magnet:?xt=...
            if (strpos($line, ',magnet:') !== false) {
                list($name, $url) = explode(',', $line, 2);
                $name = trim($name);
                $url = trim($url);
            }
            // 格式2: 标题 - magnet:?xt=...
            elseif (strpos($line, ' - magnet:') !== false) {
                list($name, $url) = explode(' - ', $line, 2);
                $name = trim($name);
                $url = trim($url);
            }
            // 格式3: 标题 magnet:?xt=...
            elseif (strpos($line, ' magnet:') !== false) {
                $parts = explode(' ', $line, 2);
                if (count($parts) == 2 && strpos($parts[1], 'magnet:') === 0) {
                    $name = trim($parts[0]);
                    $url = trim($parts[1]);
                } else {
                    $url = $line;
                }
            }
            // 格式4: 纯磁力链接
            else {
                $url = $line;
            }

            // 提取磁力链接
            if (strpos($url, 'magnet:?') !== 0) {
                if (preg_match('/(magnet:\?xt=urn:btih:[a-zA-Z0-9]+[^\s]*)/i', $line, $matches)) {
                    $url = $matches[1];
                    if (empty($name)) {
                        $titlePart = str_replace($url, '', $line);
                        $titlePart = trim($titlePart, " ,-\t\n\r\0\x0B");
                        if (!empty($titlePart)) {
                            $name = $titlePart;
                        }
                    }
                } else {
                    continue;
                }
            }

            if (empty($name)) {
                if (preg_match('/dn=([^&]+)/', $url, $matches)) {
                    $name = urldecode($matches[1]);
                } elseif (preg_match('/btih:([a-fA-F0-9]+)/i', $url, $matches)) {
                    $name = '磁力链接 ' . substr($matches[1], 0, 8) . '...';
                } else {
                    $name = '磁力链接 ' . $idx;
                }
            }

            $out[] = ['name' => $name, 'url' => $url];
            $idx++;
        }

        fclose($fp);
        return $out;
    }

    /**
     * 解析数据库文件
     */
    private function parseDbToItems($path)
    {
        return $this->dbReader->readSQLite($path, 500); // 限制500条避免卡顿
    }

    // =========================
    // 编码/解码
    // =========================
    private function b64uEncode($str)
    {
        return rtrim(strtr(base64_encode($str), '+/', '-_'), '=');
    }

    private function b64uDecode($str)
    {
        $str = strtr($str, '-_', '+/');
        $pad = strlen($str) % 4;
        if ($pad > 0) $str .= str_repeat('=', 4 - $pad);
        return base64_decode($str, true);
    }

    private function isVirtualDir($tid)
    {
        return strpos($tid, $this->V_DIR_PREFIX) === 0;
    }

    private function isVirtualItem($id)
    {
        return strpos($id, $this->V_ITEM_PREFIX) === 0;
    }

    private function encodeVirtualDir($listFilePath)
    {
        return $this->V_DIR_PREFIX . $this->b64uEncode($listFilePath);
    }

    private function decodeVirtualDir($tid)
    {
        $raw = substr($tid, strlen($this->V_DIR_PREFIX));

        $path = $this->b64uDecode($raw);
        if ($path === false || $path === null || $path === '') {
            $path = base64_decode($raw, true); // 兼容旧 base64
        }

        return $path ?: '';
    }

private function encodeVirtualItem($name, $url = '', $pic = '', $extra = [])
{
    $payload = array_merge([
        'name' => $name,
        'url' => $url,
        'pic' => $pic
    ], is_array($extra) ? $extra : []);

    return $this->V_ITEM_PREFIX . $this->b64uEncode(
        json_encode($payload, JSON_UNESCAPED_UNICODE)
    );
}

private function decodeVirtualItem($id)
{
    $raw = substr($id, strlen($this->V_ITEM_PREFIX));

    $json = $this->b64uDecode($raw);
    if ($json === false || $json === null || $json === '') {
        $json = base64_decode($raw, true); // 兼容旧 base64
    }
    if (!$json) return null;

    $arr = json_decode($json, true);
    if (!is_array($arr)) return null;

    $url = trim($arr['url'] ?? '');
    $playUrl = trim($arr['play_url'] ?? '');

    if ($url === '' && $playUrl === '') return null;

    return $arr;
}

private function buildSafeVodPlay($fromRaw, $playUrlRaw, $fallbackTitle = '播放')
{
    $fromArr = array_values(array_filter(array_map('trim', explode('$$$', (string)$fromRaw))));
    $groupArr = array_values(array_filter(array_map('trim', explode('$$$', (string)$playUrlRaw))));

    if (empty($groupArr) && trim($playUrlRaw) !== '') {
        $groupArr = [trim($playUrlRaw)];
    }

    $safeFrom = [];
    $safeGroups = [];

    foreach ($groupArr as $i => $group) {
        $lineName = $fromArr[$i] ?? ('线路' . ($i + 1));
        $episodes = array_values(array_filter(array_map('trim', explode('#', $group))));
        $safeEp = [];

        foreach ($episodes as $j => $ep) {
            $parts = explode('$', $ep, 2);
            if (count($parts) === 2) {
                $epName = trim($parts[0]) !== '' ? trim($parts[0]) : ('第' . ($j + 1) . '集');
                $epUrl = trim($parts[1]);
            } else {
                $epName = '第' . ($j + 1) . '集';
                $epUrl = trim($ep);
            }

            if ($epUrl === '') continue;

            $safe = $this->URL_B64U_PREFIX . $this->b64uEncode($epUrl);
            $safeEp[] = $epName . '$' . $safe;
        }

        if (!empty($safeEp)) {
            $safeFrom[] = $lineName;
            $safeGroups[] = implode('#', $safeEp);
        }
    }

    // 兜底：单链接直接包起来
    if (empty($safeGroups)) {
        $safe = $this->URL_B64U_PREFIX . $this->b64uEncode($playUrlRaw);
        return [
            'vod_play_from' => '默认线路',
            'vod_play_url' => $fallbackTitle . '$' . $safe
        ];
    }

    return [
        'vod_play_from' => implode('$$$', $safeFrom),
        'vod_play_url' => implode('$$$', $safeGroups)
    ];
}

    // =========================
    // 工具
    // =========================
    private function getRootIndex($path)
    {
        $realPath = realpath($path);
        if ($realPath === false) return null;
        
        foreach ($this->ROOT as $index => $root) {
            $realRoot = realpath($root);
            if ($realRoot !== false && strpos($realPath, $realRoot) === 0) {
                return $index;
            }
        }
        return null;
    }

    private function isPlayableUrl($url)
    {
        return $this->dbReader->isPlayableUrl($url) || $this->isLocalPath($url);
    }

    private function isLocalPath($p)
    {
        $p = trim((string)$p);
        if ($p === '') return false;
        return (strpos($p, '://') === false) && (strpos($p, '/') === 0);
    }

    private function scanDirNatural($path)
    {
        $arr = @scandir($path);
        if (!$arr) return [];

        $arr = array_values(array_filter($arr, function ($x) {
            return $x !== '.' && $x !== '..';
        }));

        usort($arr, function ($a, $b) {
            return strnatcasecmp($a, $b);
        });

        return $arr;
    }

    /**
     * 收集目录下图片
     */
    private function collectImagesInDir($dir)
    {
        $out = [];
        $files = $this->scanDirNatural($dir);

        foreach ($files as $file) {
            $full = rtrim($dir, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR . $file;
            $real = realpath($full) ?: $full;
            if (!is_file($real)) continue;

            $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
            if (in_array($ext, $this->IMAGE_EXTS)) {
                $out[] = 'file://' . $real;
            }
        }

        return $out;
    }

    public function getIcon($ext, $path)
    {
        $port = $_SERVER['SERVER_PORT'] ?? '8901';
        $iconBase = 'http://0.0.0.0:' . $port . '/icon/';
        $iconName = 'video-file';

        if ($ext === 'dir' || is_dir($path)) $iconName = 'folder-invoices';
        elseif ($ext === 'json') $iconName = 'json';
        elseif ($ext === 'txt') $iconName = 'txt';
        elseif ($ext === 'm3u') $iconName = 'm3u';
        elseif ($ext === 'm3u8') $iconName = 'm3u8';
        elseif ($ext === 'magnet') $iconName = 'magnet';
        elseif ($ext === 'thunder') $iconName = 'thunder';
        elseif ($ext === 'database' || $ext === 'db') $iconName = 'database';
        elseif ($ext === 'youtube') $iconName = 'youtube';
        elseif ($ext === 'bilibili') $iconName = 'bilibili';
        elseif ($ext === 'back') $iconName = 'back';
        elseif ($ext === 'link') $iconName = 'video-file';
        elseif ($ext === 'album') $iconName = 'image-file';
        elseif (in_array($ext, $this->MEDIA_EXTS)) $iconName = 'video-file';
        elseif (in_array($ext, $this->IMAGE_EXTS)) $iconName = 'image-file';

        return $iconBase . $iconName . '.png';
    }
}

// 运行
if (!headers_sent()) {
    header('Content-Type: application/json; charset=utf-8');
}
error_reporting(E_ALL);
ini_set('display_errors', '1');

(new Spider())->run();
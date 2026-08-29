/**
 * 哔哩哔哩 - 猫影视/TVBox JS爬虫格式
 * 支持全部分类的自定义中文筛选搜索
 * 包含B站分享链接和Cookie功能
 */

class Spider extends BaseSpider {
    
    constructor() {
        super();
        this.host = 'https://www.bilibili.com';
        
        // 基础请求头
        this.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cookie': 'buvid3=; bili_jct=; DedeUserID=; DedeUserID__ckMd5=; SESSDATA=; sid='  // 留空，用户可自行配置
        };
        
        // ============ 分类配置 ============
        this.classes = [
            { type_id: '全部', type_name: '全部' },
            { type_id: '1', type_name: '番剧' },
            { type_id: '4', type_name: '国创' },
            { type_id: '2', type_name: '电影' },
            { type_id: '5', type_name: '电视剧' },
            { type_id: '3', type_name: '纪录片' },
            { type_id: '7', type_name: '综艺' },
            { type_id: '时间表', type_name: '时间表' },
            { type_id: 'search_仙逆', type_name: '🔍仙逆' },
            { type_id: 'search_沙雕动画', type_name: '🔍沙雕动画' },
            { type_id: 'search_搞笑动漫', type_name: '🔍搞笑动漫' }
        ];
        
        // ============ 筛选配置 - 支持自定义中文搜索 ============
        this.filters = {
            '全部': [
                {
                    key: 'search_keyword',
                    name: '🔍搜索关键词',
                    value: [
                        { n: '不搜索(显示推荐)', v: '' },
                        { n: '仙逆', v: '仙逆' },
                        { n: '沙雕动画', v: '沙雕动画' },
                        { n: '搞笑动漫', v: '搞笑动漫' },
                        { n: '修真', v: '修真' },
                        { n: '王林', v: '王林' },
                        { n: '国漫', v: '国漫' },
                        { n: '动漫搞笑', v: '动漫搞笑' },
                        { n: '搞笑', v: '搞笑' },
                        { n: '沙雕', v: '沙雕' },
                        { n: '幽默', v: '幽默' },
                        { n: '喜剧', v: '喜剧' }
                    ]
                },
                {
                    key: 'search_type',
                    name: '搜索类型',
                    value: [
                        { n: '智能搜索', v: '' },
                        { n: '视频', v: 'video' },
                        { n: '番剧', v: 'media_bangumi' },
                        { n: '影视', v: 'media_ft' }
                    ]
                },
                {
                    key: 'search_sort',
                    name: '排序方式',
                    value: [
                        { n: '综合排序', v: '' },
                        { n: '最新发布', v: 'pubdate' },
                        { n: '最多播放', v: 'click' },
                        { n: '最多弹幕', v: 'dm' },
                        { n: '最多收藏', v: 'stow' }
                    ]
                },
                {
                    key: 'tid',
                    name: '内容分类',
                    value: [
                        { n: '全部', v: '' },
                        { n: '番剧', v: '1' },
                        { n: '国创', v: '4' },
                        { n: '电影', v: '2' },
                        { n: '电视剧', v: '5' },
                        { n: '纪录片', v: '3' },
                        { n: '综艺', v: '7' }
                    ]
                },
                {
                    key: 'order',
                    name: '排序规则',
                    value: [
                        { n: '默认', v: '' },
                        { n: '播放数量', v: '2' },
                        { n: '更新时间', v: '0' },
                        { n: '最高评分', v: '4' },
                        { n: '弹幕数量', v: '1' },
                        { n: '追看人数', v: '3' }
                    ]
                }
            ],
            '番剧': [
                {
                    key: 'order',
                    name: '排序',
                    value: [
                        { n: '播放数量', v: '2' },
                        { n: '更新时间', v: '0' },
                        { n: '最高评分', v: '4' },
                        { n: '弹幕数量', v: '1' },
                        { n: '追看人数', v: '3' }
                    ]
                }
            ],
            '国创': [
                {
                    key: 'order',
                    name: '排序',
                    value: [
                        { n: '播放数量', v: '2' },
                        { n: '更新时间', v: '0' },
                        { n: '最高评分', v: '4' },
                        { n: '弹幕数量', v: '1' },
                        { n: '追看人数', v: '3' }
                    ]
                }
            ],
            '时间表': [
                {
                    key: 'tid',
                    name: '分类',
                    value: [
                        { n: '番剧', v: '1' },
                        { n: '国创', v: '4' }
                    ]
                }
            ],
            // 自定义搜索分类的筛选配置
            'search_仙逆': [
                {
                    key: 'subtype',
                    name: '子类型',
                    value: [
                        { n: '全部', v: '' },
                        { n: '搞笑版', v: '搞笑' },
                        { n: '剪辑版', v: '剪辑' },
                        { n: '解说版', v: '解说' },
                        { n: '燃向', v: '燃' },
                        { n: '沙雕版', v: '沙雕' },
                        { n: '完整版', v: '完整' }
                    ]
                },
                {
                    key: 'sort',
                    name: '排序',
                    value: [
                        { n: '综合排序', v: '' },
                        { n: '最新发布', v: 'pubdate' },
                        { n: '最多播放', v: 'click' },
                        { n: '最多弹幕', v: 'dm' }
                    ]
                }
            ],
            'search_沙雕动画': [
                {
                    key: 'style',
                    name: '风格',
                    value: [
                        { n: '全部', v: '' },
                        { n: '搞笑', v: '搞笑' },
                        { n: '治愈', v: '治愈' },
                        { n: '脑洞', v: '脑洞' },
                        { n: '日常', v: '日常' },
                        { n: '鬼畜', v: '鬼畜' }
                    ]
                },
                {
                    key: 'sort',
                    name: '排序',
                    value: [
                        { n: '综合排序', v: '' },
                        { n: '最新发布', v: 'pubdate' },
                        { n: '最多播放', v: 'click' }
                    ]
                }
            ],
            'search_搞笑动漫': [
                {
                    key: 'type',
                    name: '类型',
                    value: [
                        { n: '全部', v: '' },
                        { n: '番剧', v: '番剧' },
                        { n: '国创', v: '国创' },
                        { n: '剪辑', v: '剪辑' },
                        { n: 'MAD', v: 'MAD' }
                    ]
                },
                {
                    key: 'sort',
                    name: '排序',
                    value: [
                        { n: '综合排序', v: '' },
                        { n: '最新发布', v: 'pubdate' },
                        { n: '最多播放', v: 'click' }
                    ]
                }
            ]
        };
        
        // ============ 线路配置 ============
        this.playLines = [
            { name: '壳子超级解析', id: 'super_parse', type: 'parse', priority: 10 },
            { name: '官方直连(需Cookie)', id: 'official', type: 'direct', priority: 5 },
            { name: 'B站分享链接', id: 'share', type: 'share', priority: 3 }
        ];
        
        // 线路状态管理
        this.lineStats = {};
        this.initLineStats();
        
        // 检查是否登录
        this.isLoggedIn = this.checkLoginStatus();
        
        // 缓存系统
        this.searchCache = {};
        this.cacheTimeout = 5 * 60 * 1000; // 5分钟缓存
    }
    
    init(extend = '') {
        // 检查Cookie状态
        this.isLoggedIn = this.checkLoginStatus();
        
        // 尝试从extend中恢复配置
        if (extend) {
            try {
                const config = JSON.parse(extend);
                if (config.lineStats) {
                    this.lineStats = config.lineStats;
                }
            } catch (e) {
                // 解析失败，使用默认配置
            }
        }
        
        return '';
    }
    
    getName() {
        return '哔哩哔哩(全功能版)';
    }
    
    isVideoFormat(url) {
        return true;
    }
    
    manualVideoCheck() {
        return false;
    }
    
    destroy() {
        // 清理资源
    }
    
    // ============ 主页配置 ============
    homeContent(filter) {
        const result = {
            class: this.classes,
            filters: this.filters
        };
        
        return result;
    }
    
    async homeVideoContent() {
        try {
            // 获取热门番剧
            const videos = await this.getRankList(1, 1);
            return { list: videos.slice(0, 10) };
            
        } catch (error) {
            console.error(`homeVideoContent error: ${error.message}`);
            return { list: [] };
        }
    }
    
    // ============ 分类页面 - 支持全部分类的自定义搜索 ============
    async categoryContent(tid, pg, filter, extend) {
        try {
            const page = parseInt(pg) || 1;
            
            // 解析筛选参数
            const filterObj = this.parseFilterParams(extend);
            
            // ============ 处理全部分类的自定义搜索 ============
            if (tid === '全部') {
                return await this.handleAllCategorySearch(page, filterObj);
            }
            
            // ============ 处理自定义搜索分类 ============
            if (tid.startsWith('search_')) {
                return await this.handleCustomSearchCategory(tid, page, filterObj);
            }
            
            // ============ 处理标准分类 ============
            return await this.handleStandardCategory(tid, page, filterObj);
            
        } catch (error) {
            console.error(`categoryContent error: ${error.message}`);
            return {
                list: [],
                page: pg,
                pagecount: 0,
                limit: 20,
                total: 0
            };
        }
    }
    
    // ============ 处理全部分类的搜索 ============
    async handleAllCategorySearch(page, filterObj) {
        let videos = [];
        
        // 检查是否有搜索关键词
        const searchKeyword = filterObj.search_keyword || '';
        
        if (searchKeyword) {
            // 有搜索关键词，执行搜索
            const searchType = filterObj.search_type || '';
            const searchSort = filterObj.search_sort || '';
            
            videos = await this.performSearch(searchKeyword, page, searchType, searchSort);
        } else {
            // 没有搜索关键词，显示推荐内容
            videos = await this.getRecommendedContent(page, filterObj);
        }
        
        return {
            list: videos,
            page: page,
            pagecount: 9999,
            limit: 20,
            total: 999999
        };
    }
    
    // ============ 详情页面 ============
    async detailContent(ids) {
        try {
            const id = ids[0];
            
            if (id.startsWith('BV') || id.startsWith('av')) {
                return await this.getVideoDetail(id);
            } else {
                return await this.getSeasonDetail(id);
            }
            
        } catch (error) {
            console.error(`detailContent error: ${error.message}`);
            return { list: [] };
        }
    }
    
    // ============ 搜索页面 ============
    async searchContent(key, quick, pg = '1') {
        try {
            const page = parseInt(pg) || 1;
            
            // 检查缓存
            const cacheKey = `search_${key}_${page}`;
            if (this.searchCache[cacheKey] && 
                Date.now() - this.searchCache[cacheKey].timestamp < this.cacheTimeout) {
                return this.searchCache[cacheKey].data;
            }
            
            const videos = await this.smartSearch(key, page);
            
            const result = {
                list: videos,
                page: page,
                pagecount: page + 1,
                limit: 20,
                total: videos.length * 10
            };
            
            // 缓存结果
            this.searchCache[cacheKey] = {
                data: result,
                timestamp: Date.now()
            };
            
            return result;
            
        } catch (error) {
            console.error(`searchContent error: ${error.message}`);
            return {
                list: [],
                page: pg,
                pagecount: 0,
                limit: 20,
                total: 0
            };
        }
    }
    
    // ============ 播放页面 - 完整线路功能 ============
    async playerContent(flag, id, vipFlags) {
        try {
            // 根据线路类型返回不同的播放参数
            if (flag === '壳子超级解析') {
                // 调用壳子超级解析
                return {
                    parse: 1,           // 必须为1，表示需要解析
                    jx: 1,              // 必须为1，启用解析
                    play_parse: true,   // 启用播放解析
                    parse_type: '壳子超级解析',
                    parse_source: '哔哩哔哩',
                    url: id,            // B站分享链接
                    header: JSON.stringify({
                        'User-Agent': this.headers['User-Agent'],
                        'Referer': 'https://www.bilibili.com',
                        'Origin': 'https://www.bilibili.com'
                    })
                };
                
            } else if (flag === '官方直连(需Cookie)') {
                // 记录使用
                this.markLineSuccess('official');
                
                // 解析官方ID格式
                if (id.includes('_')) {
                    const parts = id.split('_');
                    if (parts.length >= 3) {
                        const season_id = parts[0];
                        const epId = parts[1];
                        const cid = parts[2];
                        
                        // 返回官方播放地址（需要壳子支持Cookie）
                        return {
                            parse: 0,
                            url: `https://api.bilibili.com/pgc/player/web/playurl?cid=${cid}&ep_id=${epId}&qn=80&fnval=1&fnver=0&fourk=0`,
                            header: JSON.stringify(this.headers)
                        };
                    }
                }
                
                // 如果不是官方ID格式，回退到壳子解析
                return {
                    parse: 1,
                    jx: 1,
                    play_parse: true,
                    parse_type: '壳子超级解析',
                    parse_source: '哔哩哔哩',
                    url: id,
                    header: JSON.stringify(this.headers)
                };
                
            } else if (flag === 'B站分享链接') {
                // 记录使用
                this.markLineSuccess('share');
                
                // 直接返回分享链接，让壳子处理
                return {
                    parse: 1,
                    jx: 1,
                    play_parse: true,
                    parse_type: '壳子自动解析',
                    parse_source: '哔哩哔哩',
                    url: id,
                    header: JSON.stringify({
                        'User-Agent': this.headers['User-Agent'],
                        'Referer': 'https://www.bilibili.com',
                        'Origin': 'https://www.bilibili.com'
                    })
                };
            }
            
            // 默认使用壳子超级解析
            return {
                parse: 1,
                jx: 1,
                play_parse: true,
                parse_type: '壳子超级解析',
                parse_source: '哔哩哔哩',
                url: id,
                header: JSON.stringify(this.headers)
            };
            
        } catch (error) {
            console.error(`playerContent error: ${error.message}`);
            // 即使出错也返回超级解析参数，让壳子处理
            return {
                parse: 1,
                jx: 1,
                play_parse: true,
                parse_type: '壳子超级解析',
                parse_source: '哔哩哔哩',
                url: id,
                header: JSON.stringify(this.headers)
            };
        }
    }
    
    localProxy(param) {
        return null;
    }
    
    // ============ 详情页面 - 完整线路功能 ============
    async getVideoDetail(videoId) {
        try {
            let url = '';
            if (videoId.startsWith('BV')) {
                url = `https://api.bilibili.com/x/web-interface/view?bvid=${videoId}`;
            } else if (videoId.startsWith('av')) {
                const aid = videoId.replace('av', '');
                url = `https://api.bilibili.com/x/web-interface/view?aid=${aid}`;
            } else {
                return { list: [] };
            }
            
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code !== 0 || !data.data) {
                console.log('视频详情接口返回错误:', data.message);
                return { list: [] };
            }
            
            const videoData = data.data;
            
            const vod = {
                vod_id: videoId,
                vod_name: videoData.title || '',
                vod_pic: this.fixCoverUrl(videoData.pic || ''),
                type_name: '视频',
                vod_year: new Date(videoData.pubdate * 1000).getFullYear() || '',
                vod_area: '中国',
                vod_remarks: `${this.formatCount(videoData.stat?.view)}播放`,
                vod_actor: `UP主: ${videoData.owner?.name || ''}`,
                vod_director: `点赞:${this.formatCount(videoData.stat?.like)} 投币:${this.formatCount(videoData.stat?.coin)}`,
                vod_content: this.cleanHtml(videoData.desc || ''),
                vod_play_from: '',
                vod_play_url: ''
            };

            // ============ 构建完整的播放线路 ============
            const shareUrl = `https://www.bilibili.com/video/${videoId}`;
            const playFrom = [];
            const playUrl = [];
            
            // 1. 壳子超级解析线路
            playFrom.push('壳子超级解析');
            playUrl.push(`正片$${shareUrl}`);
            
            // 2. B站分享链接线路
            playFrom.push('B站分享链接');
            playUrl.push(`正片$${shareUrl}`);
            
            // 3. 官方直连线路（需要Cookie）
            if (this.isLoggedIn) {
                playFrom.push('官方直连(需Cookie)');
                playUrl.push(`正片$${videoId}`);
            }

            vod.vod_play_from = playFrom.join('$$$');
            vod.vod_play_url = playUrl.join('$$$');

            return { list: [vod] };
            
        } catch (error) {
            console.error(`getVideoDetail error: ${error.message}`);
            return { list: [] };
        }
    }
    
    async getSeasonDetail(seasonId) {
        try {
            const url = 'https://api.bilibili.com/pgc/view/web/season';
            
            const response = await fetch(`${url}?season_id=${seasonId}`, { 
                headers: this.headers 
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code !== 0 || !data.result) {
                console.log('详情接口返回错误:', data.message);
                return { list: [] };
            }
            
            const jo = data.result;
            const stat = jo.stat || {};
            const rating = jo.rating || {};
            
            const vod = {
                vod_id: seasonId,
                vod_name: jo.title || '',
                vod_pic: this.fixCoverUrl(jo.cover || ''),
                type_name: jo.share_sub_title || '',
                vod_year: jo.publish?.pub_time?.substr(0, 4) || '',
                vod_area: jo.areas?.[0]?.name || '',
                vod_remarks: jo.new_ep?.desc || '',
                vod_actor: `弹幕: ${this.formatCount(stat.danmakus)}　点赞: ${this.formatCount(stat.likes)}　投币: ${this.formatCount(stat.coins)}`,
                vod_director: rating.score ? `评分: ${rating.score}　${jo.subtitle || ''}` : `暂无评分　${jo.subtitle || ''}`,
                vod_content: this.cleanHtml(jo.evaluate || ''),
                vod_play_from: '',
                vod_play_url: ''
            };

            // 处理剧集
            const episodes = jo.episodes || [];
            const filteredEpisodes = episodes.filter(ep => 
                !ep.title?.includes('预告') && 
                !(ep.badge && ep.badge.includes('预告'))
            );

            if (filteredEpisodes.length > 0) {
                const playFrom = [];
                const playUrl = [];

                // 壳子超级解析线路
                const superParseItems = [];
                
                // B站分享链接线路
                const shareItems = [];
                
                // 官方直连线路（需要Cookie）
                const officialItems = [];

                filteredEpisodes.forEach(ep => {
                    // B站分享链接
                    const shareUrl = ep.share_url || `https://www.bilibili.com/bangumi/play/ep${ep.id}`;
                    let part = `${ep.title || ''} ${ep.long_title || ''}`.trim();
                    
                    // 清理标题
                    part = part
                        .replace(/#/g, '-')
                        .replace(/\[预告\]/g, '')
                        .replace(/预告/g, '')
                        .replace(/\s+/g, ' ')
                        .trim();
                    
                    if (!part) {
                        part = `第${ep.order || '?'}集`;
                    }
                    
                    // 壳子超级解析使用分享链接
                    superParseItems.push(`${part}$${shareUrl}`);
                    
                    // B站分享链接
                    shareItems.push(`${part}$${shareUrl}`);
                    
                    // 官方线路使用ID格式（需要Cookie）
                    const officialId = `${seasonId}_${ep.id}_${ep.cid}`;
                    officialItems.push(`${part}$${officialId}`);
                });

                // 添加壳子超级解析线路
                playFrom.push('壳子超级解析');
                playUrl.push(superParseItems.join('#'));
                
                // 添加B站分享链接线路
                playFrom.push('B站分享链接');
                playUrl.push(shareItems.join('#'));
                
                // 添加官方直连线路（如果已登录）
                if (this.isLoggedIn) {
                    playFrom.push('官方直连(需Cookie)');
                    playUrl.push(officialItems.join('#'));
                }

                vod.vod_play_from = playFrom.join('$$$');
                vod.vod_play_url = playUrl.join('$$$');
            }

            return { list: [vod] };
            
        } catch (error) {
            console.error(`getSeasonDetail error: ${error.message}`);
            return { list: [] };
        }
    }
    
    // ============ 线路管理功能 ============
    
    // 检查登录状态
    checkLoginStatus() {
        const cookie = this.headers.Cookie || '';
        return cookie.includes('SESSDATA=') && cookie.includes('bili_jct=');
    }
    
    // 初始化线路统计
    initLineStats() {
        this.playLines.forEach(line => {
            if (!this.lineStats[line.id]) {
                this.lineStats[line.id] = {
                    success: 0,
                    fail: 0,
                    score: line.priority || 0,
                    lastUsed: 0
                };
            }
        });
    }
    
    // 记录线路成功
    markLineSuccess(lineId) {
        if (this.lineStats[lineId]) {
            this.lineStats[lineId].success++;
            this.lineStats[lineId].score += 2;
            this.lineStats[lineId].lastUsed = Date.now();
        }
    }
    
    // 记录线路失败
    markLineFail(lineId) {
        if (this.lineStats[lineId]) {
            this.lineStats[lineId].fail++;
            this.lineStats[lineId].score -= 1;
            this.lineStats[lineId].lastUsed = Date.now();
        }
    }
    
    // 获取最佳线路
    getBestLine() {
        let bestLine = this.playLines[0];
        let bestScore = -Infinity;
        
        this.playLines.forEach(line => {
            const stats = this.lineStats[line.id] || { score: 0 };
            if (stats.score > bestScore) {
                bestScore = stats.score;
                bestLine = line;
            }
        });
        
        return bestLine;
    }
    
    // ============ 辅助方法 ============
    
    // 解析筛选参数
    parseFilterParams(extend) {
        let filterObj = {};
        if (extend) {
            if (typeof extend === 'string') {
                try {
                    filterObj = JSON.parse(extend);
                } catch (e) {
                    extend.split('&').forEach(item => {
                        const [key, value] = item.split('=');
                        if (key && value) {
                            filterObj[key] = decodeURIComponent(value);
                        }
                    });
                }
            } else if (typeof extend === 'object') {
                filterObj = extend;
            }
        }
        return filterObj;
    }
    
    // 执行搜索
    async performSearch(keyword, page, searchType = '', searchSort = '') {
        try {
            const encodedKeyword = encodeURIComponent(keyword);
            let url = '';
            
            // 构建搜索URL
            if (searchType) {
                // 指定搜索类型
                url = `https://api.bilibili.com/x/web-interface/search/type?search_type=${searchType}&keyword=${encodedKeyword}&page=${page}`;
                if (searchSort) {
                    url += `&order=${searchSort}`;
                }
            } else {
                // 智能搜索：同时搜索多种类型
                return await this.smartSearch(keyword, page, searchSort);
            }
            
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code === 0 && data.data?.result) {
                return data.data.result.map(item => ({
                    vod_id: this.extractVideoId(item),
                    vod_name: this.cleanHtml(item.title || ''),
                    vod_pic: this.fixCoverUrl(item.pic || item.cover || ''),
                    vod_remarks: this.generateRemarks(item)
                })).filter(v => v.vod_id);
            }
            
            return [];
            
        } catch (error) {
            console.error(`performSearch error: ${error.message}`);
            return [];
        }
    }
    
    // 智能搜索
    async smartSearch(keyword, page, searchSort = '') {
        try {
            const videos = [];
            const searchTypes = ['video', 'media_bangumi', 'media_ft'];
            
            // 并行搜索多种类型
            const promises = searchTypes.map(type => 
                this.searchByType(keyword, page, type, searchSort)
            );
            
            const results = await Promise.all(promises);
            
            // 合并结果
            results.forEach(result => {
                videos.push(...result);
            });
            
            // 去重和排序
            return this.deduplicateAndSort(videos, keyword);
            
        } catch (error) {
            console.error(`smartSearch error: ${error.message}`);
            return [];
        }
    }
    
    async searchByType(keyword, page, searchType, searchSort = '') {
        try {
            const encodedKeyword = encodeURIComponent(keyword);
            let url = `https://api.bilibili.com/x/web-interface/search/type?search_type=${searchType}&keyword=${encodedKeyword}&page=${page}`;
            
            if (searchSort) {
                url += `&order=${searchSort}`;
            }
            
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                return [];
            }
            
            const data = await response.json();
            
            if (data.code === 0 && data.data?.result) {
                return data.data.result.map(item => ({
                    vod_id: this.extractVideoId(item),
                    vod_name: this.cleanHtml(item.title || ''),
                    vod_pic: this.fixCoverUrl(item.pic || item.cover || ''),
                    vod_remarks: this.generateRemarks(item),
                    search_score: this.calculateRelevanceScore(item, keyword)
                }));
            }
            
            return [];
            
        } catch (error) {
            console.error(`searchByType error: ${error.message}`);
            return [];
        }
    }
    
    // 提取视频ID
    extractVideoId(item) {
        if (item.bvid) {
            return item.bvid;
        } else if (item.aid) {
            return 'av' + item.aid;
        } else if (item.season_id) {
            return String(item.season_id);
        }
        return '';
    }
    
    // 生成备注信息
    generateRemarks(item) {
        let remarks = [];
        
        if (item.duration) {
            const minutes = Math.floor(item.duration / 60);
            const seconds = item.duration % 60;
            remarks.push(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        }
        
        if (item.play) {
            remarks.push(`${this.formatCount(item.play)}播放`);
        } else if (item.index_show) {
            remarks.push(item.index_show);
        }
        
        if (item.pubdate) {
            const date = new Date(item.pubdate * 1000);
            const now = new Date();
            const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
            
            if (diffDays === 0) remarks.push('今天');
            else if (diffDays === 1) remarks.push('昨天');
            else if (diffDays < 7) remarks.push(`${diffDays}天前`);
            else remarks.push(date.getMonth() + 1 + '月' + date.getDate() + '日');
        }
        
        return remarks.join(' · ') || '视频';
    }
    
    // 格式化数字
    formatCount(num) {
        if (!num) return '0';
        if (num > 1e8) return (num / 1e8).toFixed(1) + '亿';
        if (num > 1e4) return (num / 1e4).toFixed(1) + '万';
        return num.toString();
    }
    
    // 计算相关性分数
    calculateRelevanceScore(item, keyword) {
        let score = 0;
        const title = (item.title || '').toLowerCase();
        const keywordLower = keyword.toLowerCase();
        
        if (title.includes(keywordLower)) {
            score += 10;
            if (title === keywordLower) score += 20;
            if (title.startsWith(keywordLower)) score += 15;
        }
        
        if (item.play > 10000) score += 5;
        if (item.play > 100000) score += 10;
        if (item.play > 1000000) score += 15;
        
        if (item.pubdate) {
            const daysOld = (Date.now() - item.pubdate * 1000) / (1000 * 60 * 60 * 24);
            if (daysOld < 7) score += 10;
            else if (daysOld < 30) score += 5;
        }
        
        return score;
    }
    
    // 去重和排序
    deduplicateAndSort(videos, keyword) {
        const seen = new Set();
        const uniqueVideos = [];
        
        videos.sort((a, b) => (b.search_score || 0) - (a.search_score || 0));
        
        for (const video of videos) {
            if (!seen.has(video.vod_id) && video.vod_id) {
                seen.add(video.vod_id);
                delete video.search_score;
                uniqueVideos.push(video);
            }
        }
        
        return uniqueVideos.slice(0, 20);
    }
    
    // 处理自定义搜索分类
    async handleCustomSearchCategory(categoryId, page, filterObj) {
        let videos = [];
        let keyword = '';
        
        switch(categoryId) {
            case 'search_仙逆':
                keyword = '仙逆';
                break;
            case 'search_沙雕动画':
                keyword = '沙雕动画';
                break;
            case 'search_搞笑动漫':
                keyword = '搞笑动漫';
                break;
            default:
                keyword = categoryId.replace('search_', '');
        }
        
        const subtype = filterObj.subtype || filterObj.style || filterObj.type || '';
        const sort = filterObj.sort || '';
        
        let enhancedKeyword = keyword;
        if (subtype) {
            enhancedKeyword = `${keyword} ${subtype}`;
        }
        
        videos = await this.performSearch(enhancedKeyword, page, 'video', sort);
        
        if (videos.length < 5) {
            const baseVideos = await this.performSearch(keyword, page, 'video', sort);
            videos = [...videos, ...baseVideos];
        }
        
        videos = this.deduplicateVideos(videos);
        
        return {
            list: videos,
            page: page,
            pagecount: 9999,
            limit: 20,
            total: 999999
        };
    }
    
    // 处理标准分类
    async handleStandardCategory(tid, page, filterObj) {
        let videos = [];
        
        if (tid === '1') {
            videos = await this.getRankList(1, page);
        } else if (['2', '3', '4', '5', '7'].includes(tid)) {
            videos = await this.getRankList(parseInt(tid), page);
        } else if (tid === '时间表') {
            const seasonType = filterObj.tid || '1';
            videos = await this.getTimeline(seasonType);
        }
        
        return {
            list: videos,
            page: page,
            pagecount: 9999,
            limit: 20,
            total: 999999
        };
    }
    
    // 获取推荐内容
    async getRecommendedContent(page, filterObj) {
        let videos = [];
        const category = filterObj.tid || '';
        
        if (category) {
            videos = await this.getRankList(parseInt(category), page);
        } else {
            const mixVideos = await this.getMixedRecommendation(page);
            videos = mixVideos;
        }
        
        return videos;
    }
    
    async getMixedRecommendation(page) {
        const videos = [];
        const categories = [1, 4, 2, 5];
        
        for (const cat of categories) {
            try {
                const list = await this.getRankList(cat, page);
                videos.push(...list.slice(0, 5));
            } catch (error) {
                console.error(`获取分类 ${cat} 推荐失败:`, error.message);
            }
        }
        
        return videos.slice(0, 20);
    }
    
    // 简单去重
    deduplicateVideos(videos) {
        const seen = new Set();
        return videos.filter(video => {
            if (!video.vod_id || seen.has(video.vod_id)) {
                return false;
            }
            seen.add(video.vod_id);
            return true;
        });
    }
    
    // 修复封面URL
    fixCoverUrl(url) {
        if (!url) {
            return 'https://i0.hdslb.com/bfs/archive/9e5ff5a6e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5.jpg';
        }
        
        if (url.startsWith('//')) {
            return 'https:' + url;
        }
        
        if (!url.startsWith('http')) {
            if (url.includes('hdslb.com') || url.includes('bilivideo.com')) {
                return 'https:' + url;
            }
            return 'https://' + url;
        }
        
        return url;
    }
    
    // 清理HTML
    cleanHtml(text) {
        if (!text) return '';
        return text.replace(/<[^>]+>/g, '').replace(/&quot;/g, '"').replace(/&amp;/g, '&').trim();
    }
    
    // 获取排行榜
    async getRankList(seasonType, page = 1) {
        try {
            const url = `https://api.bilibili.com/pgc/web/rank/list?season_type=${seasonType}&pagesize=20&page=${page}&day=3`;
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.code === 0) {
                const items = data.result?.list || data.data?.list || [];
                return items.map(item => ({
                    vod_id: String(item.season_id || '').trim(),
                    vod_name: item.title?.trim() || '',
                    vod_pic: this.fixCoverUrl(item.cover || ''),
                    vod_remarks: item.new_ep?.index_show || item.index_show || ''
                }));
            }
            
            return [];
            
        } catch (error) {
            console.error(`getRankList error: ${error.message}`);
            return [];
        }
    }
    
    // 获取时间表
    async getTimeline(tid) {
        try {
            const url = `https://api.bilibili.com/pgc/web/timeline/v2?season_type=${tid}&day_before=2&day_after=4`;
            const response = await fetch(url, { headers: this.headers });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            const videos = [];
            
            if (data.code === 0 && data.result) {
                const result = data.result;
                
                const latestList = result.latest || [];
                latestList.forEach(vod => {
                    if (!vod.title?.includes('预告')) {
                        videos.push({
                            vod_id: String(vod.season_id || '').trim(),
                            vod_name: vod.title?.trim() || '',
                            vod_pic: this.fixCoverUrl(vod.cover || ''),
                            vod_remarks: (vod.pub_index || '') + '　' + (vod.follows || '').replace('系列', '')
                        });
                    }
                });
            }
            
            return videos;
            
        } catch (error) {
            console.error(`getTimeline error: ${error.message}`);
            return [];
        }
    }
}

// 导出 Spider 类
module.exports = Spider;
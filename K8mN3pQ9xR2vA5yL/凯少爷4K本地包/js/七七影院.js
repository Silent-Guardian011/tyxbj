var rule = {
    author: 'Jack',
    title: '七七影院',
    类型: '影视',
    host: 'https://www.77yykp.com',
    headers: {
        'User-Agent': 'MOBILE_UA',
        'Referer': '',
        'Cookie': ''
    },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: '/',
    url: '/vodtype/fyfilter/',   
    filter_url: '{{fl.cateId or "fyclass"}}{{fl.area}}{{fl.by}}{{fl.class}}{{fl.lang}}{{fl.letter}}/page/fypage/{{fl.year}}',
    detailUrl: 'voddetail/fyid/',
    searchUrl: '/search/wd/**/page/fypage/',
    搜索: '.entry-container;a&&title;.lazyload&&data-original;.video-title&&Text;a&&href',   
    //searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',
   //搜索: 'json:list;name;pic;en;id',    
    searchable: 2,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '电影&连续剧&综艺&动漫&短剧',
    class_url: 'dianying&dianshiju&zongyi&dongman&duanju',
    推荐: '*',

    一级: $js.toString(() => {
        let klist = pdfa(request(input), '.video-content-item');   
        let k = klist.map(it => ({
            title: pdfh(it, '.video-name&&Text'),
            pic_url: pd(it, 'a&&data-original', input),
            desc: pdfh(it, '.video-title&&Text'),
            url: pdfh(it, 'a&&href'),
            content: ''
        }));
        setResult(k);
    }),
    
    二级: $js.toString(() => {
        let html = request(input);
        VOD = {};
        VOD.vod_id = input;
        VOD.vod_name = pdfh(html, 'h1.detail-info-title&&Text');
        VOD.vod_pic = pdfh(html, '.block-fea&&data-original') || pdfh(html, '.block-fea&&data-original');
        VOD.vod_year = pdfh(html, 'p.mb-0:contains(年份)&&Text').replace(/.*年份：/, '');
        VOD.vod_area = pdfh(html, 'p.mb-0:contains(地区)&&Text').replace(/.*地区：/, '').split(' ')[0];
        VOD.vod_remarks = pdfh(html, 'em.text-theme&&Text');
        VOD.type_name = pdfh(html, 'p.mb-0:contains(类型)&&Text').replace(/.*类型：/, '').split(' ')[0];
        VOD.vod_actor = pdfa(html, 'p.mb-0:contains(演员) a').map(a => pdfh(a, 'body&&Text')).join('/');
        VOD.vod_director = pdfa(html, 'p.mb-0:contains(导演) a').map(a => pdfh(a, 'body&&Text')).join('/');
        VOD.vod_content = pdfh(html, '.entry-content&&Text').trim();
        
        //线路列表
        let playFroms = pdfa(html, '.ewave-playlist-tab li');
        let ktabs = playFroms.map(it => pdfh(it, 'a&&Text')); 
        VOD.vod_play_from = ktabs.join('$$$');

        // 播放列表
        let klists = [];
        let playLists = pdfa(html, '.ewave-tab-content');      
        playLists.forEach(container => {
            let episodes = pdfa(container, '.ewave-playlist-item a');
            let klist = episodes.map(ep => {
                let name = pdfh(ep, 'a&&Text');
                let url = pd(ep, 'a&&href', input);
                return name + '$' + url;
            }).join('#');
            if (klist) klists.push(klist);
        });
        
        VOD.vod_play_url = klists.join('$$$');
    }),
   
    //是否启用辅助嗅探: 1,0
    sniffer: 0,
    // 辅助嗅探规则
    isVideo: 'http((?!http).){26,}\\.(m3u8|mp4|flv|avi|mkv|wmv|mpg|mpeg|mov|ts|3gp|rm|rmvb|asf|m4a|mp3|wma)',
    
    play_parse: true,
    //播放地址通用解析
    lazy: $js.toString(() => {
        let kurl = JSON.parse(fetch(input).split('aaaa=')[1].split('<')[0]);        
        if (/\.(m3u8|mp4)/.test(kurl)) {
            input = {
                jx: 0,
                parse: 0,
                url: kurl,
                header: {
                    'User-Agent': MOBILE_UA,
                    'Referer': getHome(kurl)
                }
            };
        } else {
            input = {
                jx: 0,
                parse: 1,
                url: input
            };
        }
    }),
    
        filter: {
  
        
    }
}
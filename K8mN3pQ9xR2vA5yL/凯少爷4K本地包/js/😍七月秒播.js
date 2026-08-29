var rule = {
    author: '占海',
    title: '七月影院',
    类型: '影视',
    host: 'https://www.ys.mk/',
    headers: {
        'User-Agent': 'MOBILE_UA',
        'Referer': '',
        'Cookie': ''
    },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: '/',
    url: 'https://www.ys.mk/index.php/vod/type/id/fyclass.html',
    //filter_url: '{{fl.cateId}}{{fl.area}}{{fl.class}}fypage{{fl.year}}',
    detailUrl: '',
    // searchUrl: 'http://www.zjqhdq.com/search/**/fypage.html',    

    //searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',
    //'searchUrl: '/vodsearch/**----------fypage---.html',
    searchUrl: 'https://www.ys.mk/index.php/vod/search/page/fypage/wd/**html',
    //   搜索: 'json:list;name;pic;en;id',  
    //https://jin-bang.com.cn/vodsearch/%E7%88%B1%E6%83%85----------3---.html
    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '短剧&电影&电视剧&综艺&动漫',
    //静态分类值
    class_url: '5&1&2&3&4',
    推荐: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    // 一级分类列表
    一级: '.public-list-box;a&&title;.lazy&&data-src;.public-prt&&Text;a&&href',

    // 二级详情页

    二级: {
        title: ' h3.slide-info-title&&Text;.slide-info .hide:eq(1)&&Text',
        img: '.lazy&&data-src',
        desc: '.slide-info .hide:eq(1)&&Text;.slide-info .hide:eq(2)&&Text;.slide-info .hide:eq(3)&&Text;.slide:eq(5)&&Text',
        content: '.sketch .content&&Text',
        tabs: '.anthology-tab&&a',
        tab_text: 'a&&Text',
        lists: '.anthology-list-box&&ul&&li',
        list_text: 'span&&Text',
        list_url: 'a&&href'
    },

    搜索: '.public-list-box;a&&title;.lazy&&data-src;.public-prt&&Text;a&&href',
    //是否启用辅助嗅探: 1,0
    sniffer: 0,
    // 辅助嗅探规则
    isVideo: 'http((?!http).){26,}\\.(m3u8|mp4|flv|avi|mkv|wmv|mpg|mpeg|mov|ts|3gp|rm|rmvb|asf|m4a|mp3|wma)',

    play_parse: true,
    //播放地址通用解析
    lazy: $js.toString(() => {
        let kcode = JSON.parse(fetch(input).split('aaaa=')[1].split('<')[0]);
        let kurl = kcode.url;
        if (/\.(m3u8|mp4)/.test(kurl)) {
            input = {
                jx: 0,
                parse: 0,
                url: kurl,
                header: {
                    'User-Agent': MOBILE_UA,
                    'Referer': getHome(kurl)
                }
            }
        } else {
            input = {
                jx: 0,
                parse: 1,
                url: input
            }
        }
    }),

}
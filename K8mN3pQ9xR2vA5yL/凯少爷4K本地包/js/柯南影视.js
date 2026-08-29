var rule = {
    author: 'Jack',
    title: '柯南影视',
    类型: '影视',
    host: 'https://knvod.me',
    hostJs: '',
    headers: {'User-Agent': MOBILE_UA},
    编码: 'utf-8',
    timeout: 20000,
    homeUrl: '/',
    url: '/show/fyclass--------fypage---/',
    searchUrl: 'https://knvod.me/daxiaoren/**----------fypage---/',
    detailUrl: '',
    limit: 9,
    double: false,
    class_name: "电影&电视剧&动漫&综艺&短剧",
    class_url: "1&2&3&4&6",
    filter_def: {
        1: {cateId: '1'},
        2: {cateId: '2'},
        3: {cateId: '3'},
        4: {cateId: '4'},
        6: {cateId: '6'}
    },
    一级: '.public-list-exp;a&&title;.lazy&&data-src;.text_right&&Text;a&&href',
    推荐: '*',
    二级: {
        title: 'h3&&Text;.slide-info:contains(类型)&&Text',
        img: '.detail-pic&&data-src',
        desc: '.slide-info:contains(更新)&&Text;.slide-info:contains(年份)&&Text;.slide-info:contains(地区)&&Text;.slide-info:contains(演员)&&Text;.slide-info:contains(导演)&&Text',
        content: '.check.selected&&Text',
        tabs: '.anthology-tab.nav-swiper.b-b.br a',
        tab_text: 'Text',
        lists: '.anthology-list-play:eq(#id) li',
        list_text: 'a&&Text',
        list_url: 'a&&href'
    },
    搜索: '*',
    play_parse: true,
    lazy: $js.toString(() => {
        let kp = 0, kurl = '';
        let kcode = rule.safeParseJSON(fetch(input).match(/var player_[\s\S]*?=([\s\S]*?)</)?.[1]);
        kurl = decodeURIComponent(kcode?.url ?? '');
        if (!/\.(m3u8|mp4|mkv)/.test(kurl)) {
            kp =1;
            kurl = input; 
        }
        input = { jx: 0, parse: kp, url: kurl, header: rule.headers };
    })
}
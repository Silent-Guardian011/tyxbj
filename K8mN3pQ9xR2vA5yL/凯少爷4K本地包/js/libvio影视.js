var rule = {
    author: 'Jack',
    title: 'libvio影视',
    类型: '影视',
    host: 'https://www.libvio.cc',
    hostJs: '',
    headers: {'User-Agent': MOBILE_UA},
    编码: 'utf-8',
    timeout: 20000,
    homeUrl: '/',
    //https://www.libvio.cc/show/1-中国大陆-hits-喜剧-国语-------2025.html
    url:'/show/fyclass-fyfilter.html',
    filter_url:'{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}----fypage---{{fl.year}}',
    //url: '/show/fyclass--------fypage---.html',
    searchUrl: 'https://www.libvio.cc/search/**----------fypage---.html',
    detailUrl: 'https://www.libvio.cc/detail/fyid.html',
    limit: 9,
    double: false,
    class_parse:'.stui-header__menu li:gt(0):lt(7);a&&Text;a&&href;/(\\d+).html',
    //class_name: "电影&电视剧&动漫&日韩剧&欧美剧",
    //class_url: "1&2&4&15&16",
    filter_def: {
        1: {cateId: '1'},
        2: {cateId: '2'},
        3: {cateId: '3'},
        15: {cateId: '15'},
        16: {cateId: '16'}
    },
    推荐: '*', 
    一级: '.stui-vodlist li;a&&title;a&&data-original;.pic-text&&Text;a&&href',

二级: {
        title: 'h1&&Text',
        img: '.lazyload&&data-original',
        desc: '.data:contains(类型)&&Text;.data:contains(年份)&&Text;.data:contains(地区)&&Text;.data:contains(导演)&&Text;.data:contains(主演)&&Text',
        content: '.detail-sketch&&Text',
        tabs: '.stui-vodlist__head .stui-pannel__head h3',
        tab_text: 'Text',
        lists: '.stui-vodlist__head:eq(#id) .stui-content__playlist li a',
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





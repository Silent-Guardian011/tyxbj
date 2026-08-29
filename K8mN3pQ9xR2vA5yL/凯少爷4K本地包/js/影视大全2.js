var rule = {
    author: 'Jack',
    title: '影视大全',
    类型: '影视',
    host: 'http://www.365xuexi.net',
    homeUrl: '/',
    headers :{
        'User-Agent': 'MOBILE_UA'
},
    编码: 'utf-8',
    timeout: 5000,
    detailUrl: 'http://www.365xuexi.net/index.php/detail-id-fyid.html',
    url: '/index.php/vod/fyclass-fypage.html',
    searchUrl: 'http://www.365xuexi.net/index.php/so/page/fypage/wd/**.html',
  搜索: '*',
    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '电影&电视剧&综艺&动漫&短剧',
    //&短剧合集&有声动漫&Netflix电影
    class_url: '1&2&3&4&32&33&34&35',
   //&33&34&35
    推荐: '*',
    一级: '.fed-list-info.fed-part-rows&&li;.fed-list-title&&Text;a&&data-original;.fed-list-remarks&&Text;a&&href',
二级: {
    title: 'h1&&Text;li:contains(分类)&&Text',
    img: '.fed-list-pics&&data-original',
    desc: 'li:contains(更新)&&Text;li:contains(年份)&&Text;li:contains(地区)&&Text;li:contains(主演)&&Text;li:contains(导演)&&Text',
    content: '.fed-part-esan&&Text',
    tabs: '.fed-drop-btns a',
    tab_text: 'a&&Text',
    lists: '.fed-play-item:eq(#id) ul.fed-part-rows:last-child li',
    list_text: 'a&&Text',
    list_url: 'a&&href'
 },
      
    //是否启用辅助嗅探: 1,0
    sniffer: 0,
    // 辅助嗅探规则
    isVideo: 'http((?!http).){26,}\\.(m3u8|mp4|flv|avi|mkv|wmv|mpg|mpeg|mov|ts|3gp|rm|rmvb|asf|m4a|mp3|wma)',

    play_parse: true,
    //播放地址通用解析
    lazy: $js.toString(() => {
        let html = request(input);
        let kcode = JSON.parse(html.split('aaaa=')[1].split('<')[0]);
        let kurl = kcode.url;
        if (/\.(m3u8|mp4)/.test(kurl)) {
            input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
        } else {
            input = { jx: 0, parse: 1, url: input }
        }
    }),

}








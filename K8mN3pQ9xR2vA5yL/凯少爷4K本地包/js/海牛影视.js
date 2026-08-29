var rule = {
    author: 'Jack',
    title: '海牛影视',
    类型: '影视',
    host: 'http://www.hnjgzs.com',
    headers: {
    'User-Agent': 'MOBILE_UA',
    'Referer': '',
     'Cookie': ''
       },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: '/',
    
    //http://www.hcjzyynk.com/s/lianxuju/area/中国大陆/class/短剧/page/2/year/2025.html
      //url: '/s/fyfilter.html',
     url: '/vodtype/fyclass-fypage.html',
   //filter_url: '{{fl.cateId}}{{fl.area}}{{fl.class}}fypage{{fl.year}}',
    detailUrl: '/detail/fyid.html',    
 // searchUrl: 'http://www.zjqhdq.com/search/**/fypage.html',    
  搜索: '*',
  //searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',
  //'searchUrl: '/vodsearch/**----------fypage---.html',
  searchUrl: '/vodsearch/**----------fypage---.html',
  //   搜索: 'json:list;name;pic;en;id',  
//https://jin-bang.com.cn/vodsearch/%E7%88%B1%E6%83%85----------3---.html
    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '短剧&电影&电视剧&综艺&动漫&午夜饭',
    //静态分类值
    class_url: '29&1&32&3&4&20',
    推荐: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    一级: '.lazyload;a&&title;a&&data-original;.pic-text&&Text;a&&href',
    
  二级: $js.toString(() => {
    let html = request(input);
    VOD = {};
 VOD.vod_id = input;
 VOD.vod_name = pdfh(html, 'h1&&Text');
 VOD.type_name = pdfh(html, 'p:contains(类型)&&Text').replace('类型：','');
 VOD.vod_pic = pd(html, 'img&&data-original||img&&src');
 VOD.vod_remarks = pdfh(html, 'p:contains(状态)&&Text');
 VOD.vod_year = pdfh(html, 'p:contains(年份)&&Text').replace('年份：','');
VOD.vod_area = pdfh(html, 'p:contains(地区)&&Text').replace('地区：','');
VOD.vod_director = pdfh(html, 'p:contains(导演)&&Text').replace('导演：','');
 VOD.vod_actor = pdfh(html, 'p:contains(演员)&&Text').replace('演员：','');
 VOD.vod_content = pdfh(html, 'p:contains(简介)&&Text').replace('简介：','');
    //线路
    let r_ktabs = pdfa(html, '.nav.nav-tabs li');
    let ktabs = r_ktabs.map(it => pdfh(it, 'a&&Text'));
    VOD.vod_play_from = ktabs.join('$$$');

    let klists = [];
    let r_plists = pdfa(html, '.myui-content__list');
    r_plists.forEach((rp) => {
        let klist = pdfa(rp, 'a').map((it) => {
            return pdfh(it, 'a&&Text') + '$' + pd(it, 'a&&href', input);
        });
        klist = klist.join('#');
        klists.push(klist);
    });
    VOD.vod_play_url = klists.join('$$$');
}),
    
/*二级: {
    title: '.title strong&&Text;.title&&Text',
    img: '.myui-vodlist__thumb img&&data-original;.myui-vodlist__thumb img&&src',
    desc: '.pic-text&&Text;.data:contains(更新)&&Text;.data:contains(地区)&&Text;.data:contains(演员) a&&Text;.data:contains(导演) a&&Text',
    content: '.sketch&&Text',
    tabs: '.nav-tabs li',
    tab_text: 'a&&Text',
    lists: '.tab-content:eq(#id) .myui-content__list li',
    list_text: 'a&&Text',
    list_url: 'a&&href'

},*/
     
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
    input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
} else {
    input = { jx: 0, parse: 1, url: input }
}
}),

}




    

    
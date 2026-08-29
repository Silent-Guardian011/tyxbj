var rule = {
    author: 'Jack',
    title: '魅影影视',
    类型: '影视',
    host: 'https://www.tslznkj.com',
    headers: {
    'User-Agent': 'MOBILE_UA',
    'Referer': '',
     'Cookie': ''
       },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: '/',
    url: 'https://www.tslznkj.com/vodshow/fyclass--------fypage---.html', 
     //url: '/vodshow/fyfilter.html',
   //filter_url: '{{fl.cateId}}-{{fl.area}}-{{fl.by}}-{{fl.class}}--{{fl.letter}}---fypage---{{fl.year}}',         
    detailUrl: 'https://www.tslznkj.com/detail/fyid.html',    
 searchUrl: 'https://www.tslznkj.com/search/**----------fypage---.html',
 
    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '网红短剧&电影&电视剧&综艺&动漫',   
    //静态分类值
    class_url: '34&1&2&3&4',
    推荐: '*',
    搜索: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    一级: '.video-pic;a&&title;img&&data-original;.note.text-bg-r&&Text;a&&href',
    
    二级: $js.toString(() => {
    let html = request(input);
    VOD = {};
 VOD.vod_id = input;
 VOD.vod_name = pdfh(html, 'h1&&Text');
 VOD.type_name = pdfh(html, 'li:contains(类型)&&Text').replace('分类：','');
 VOD.vod_pic = pd(html, 'img&&data-original || img&&src');
 VOD.vod_remarks = pdfh(html, 'li:contains(状态)&&Text');
 VOD.vod_year = pdfh(html, 'li:contains(年份)&&Text').replace('年份：','');
VOD.vod_area = pdfh(html, 'li:contains(地区)&&Text').replace('地区：','');
VOD.vod_director = pdfh(html, 'li:contains(导演)&&Text').replace('导演：','');
 VOD.vod_actor = pdfh(html, 'li:contains(主演)&&Text').replace('主演：','');
 //VOD.vod_content = pdfh(html, 'li:contains(简介)&&Text').replace('简介：','');
 VOD.vod_content = pdfh(html, '.vod-content&&Text').replace('简介：','');
    //线路
    let r_ktabs = pdfa(html, '.nav.nav-tabs li');
    let ktabs = r_ktabs.map(it => pdfh(it, 'a&&Text'));
    VOD.vod_play_from = ktabs.join('$$$');

    let klists = [];
    let r_plists = pdfa(html, '.clearfix.fade');
    r_plists.forEach((rp) => {
        let klist = pdfa(rp, 'a').map((it) => {
            return pdfh(it, 'a&&Text') + '$' + pd(it, 'a&&href', input);
        });
        klist = klist.join('#');
        klists.push(klist);
    });
    VOD.vod_play_url = klists.join('$$$');
}),
    
    // 搜索: '.col-md-2.col-sm-3;a&&title;img&&data-original;.note.text-bg-r&&Text;a&&href',
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
})

}




    

    
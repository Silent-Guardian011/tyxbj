var rule = {
    author: '/251123/第1版',
    title: '樱桃影视',
    类型: '影视',
    host: 'http://yixinyingshiwang.jfsekj.com/',

    headers: {
    'User-Agent': 'MOBILE_UA',
    'Referer': '',
     'Cookie': ''
       },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: 'http://yixinyingshiwang.jfsekj.com/',
      url: '/c/fyclass-fypage/',

   // detailUrl: '/detail/fyid.html',    
  searchUrl: 'http://yixinyingshiwang.jfsekj.com/vodsearch/**----------fypage---/',    
   搜索: '*',
    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '电影&动作片&喜剧片&爱情片&科幻片&恐怖片&剧情片&战争片&伦理片&纪录片&电视剧&国产剧&港澳剧&欧美剧&台湾剧&日剧&韩剧&泰剧',
    //静态分类值
    class_url: 'dianying&dongzuo&xiju&aiqing&kehuan&kongbu&juqing&zhanzheng&lunlipian&jilupian&dianshiju&guochanju&gangaoju&oumeiju&taiwanju&riju&hanju&taiju',
 
    推荐: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    一级: '.user_list_kz;a&&title;img&&data-original;.pay&&Text;a&&href',    
    
    二级: $js.toString(() => {
let html = request(input);
VOD = {};
 VOD.vod_id = input;
VOD.vod_name = pdfh(html, 'h1&&Text');
VOD.type_name = pdfh(html, 'p:contains(类型：)&&Text').replace(/类型：|\//g,'');
 
 VOD.vod_pic = pd(html, 'img.movie-posterxq&&src', input);
 VOD.vod_remarks = pdfh(html, 'p:contains(状态：)&&Text');
vod_year: pdfh(html, 'p:contains(上映)&&Text').replace('上映：','');
        vod_area: pdfh(html, 'p:contains(地区)&&Text').replace('地区：','');
VOD.vod_director = pdfh(html, 'p:contains(导演)&&Text').replace('导演：','');
 VOD.vod_actor = pdfh(html, 'p:contains(主演)&&Text').replace('主演：','');
 VOD.vod_content = '祝您观影愉快！现为您介绍剧情:' + pdfh(html,'p:contains(简介：)&&Text').replace('简介：','');
 //↓线路数组
let r_ktabs = pdfa(html,'.nav.nav-tabs');
 let ktabs = r_ktabs.map(it => pdfh(it, 'Text'));
 VOD.vod_play_from = ktabs.join('$$$');
 
let klists = [];
//↓播放数组
let r_plists = pdfa(html, '.page_ullist.cl');
r_plists.forEach((rp) => {
    let klist = pdfa(rp, 'a').map((it) => {
        return pdfh(it, 'a&&Text') + '$' + pd(it, 'a&&href', input);
    }).filter(item => {
        // 过滤掉标题包含"APP播放"的无关项
        return !item.includes('APP播放');
    });
    klist = klist.join('#');
    klists.push(klist);
});
VOD.vod_play_url = klists.join('$$$');
}),
    /*二级: {
        title: '标题;类型',
        img: '图片链接',
        desc: '主要信息;年代;地区;演员;导演',
        content: '简介',
        tabs: '线路数组',
        tab_text: '线路标题',
        lists: '播放数组',       
        list_text: '播放标题',
        list_url: '播放链接',
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


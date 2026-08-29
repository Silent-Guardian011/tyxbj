var rule = {
    author: '/251205/第1版',
    title: '水牛影视',
    类型: '影视',
    host: 'http://www.shuiniuyingshi.cc/',
    
//    hostJs: `print(HOST); let html=request(HOST,{headers:{"User-Agent":MOBILE_UA}}); let src= jsp.pdfh(html,"h3&&a&&href"); print(src); HOST=src`,

    headers: {
    'User-Agent': 'MOBILE_UA',
    'Referer': '',
     'Cookie': ''
       },
    编码: 'utf-8',
    timeout: 5000,
    homeUrl: 'http://www.zjqhdq.com/',
//  filter_url: '{{fl.cateId}}-{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}-{{fl.letter}}---fypage---{{fl.year}}',
//filter_url: '{{fl.area}}{{fl.by}}{{fl.class}}/id/{{fl.cateId}}{{fl.lang}}{{fl.letter}}/page/fypage{{fl.year}}',
//https://m.jusyg.com/mbwusw/6-大陆-hits-动作-国语----2---2025.html
      url: 'http://www.zjqhdq.com/ys/fyclass/fypage.html',
   // filter_url: '{{fl.cateId}}-{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}-{{fl.letter}}---fypage---{{fl.year}}',
    detailUrl: '/detail/fyid.html',    
  searchUrl: 'http://www.zjqhdq.com/search/**/fypage.html',    
   搜索: '*',
//   searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',

//      搜索: 'json:list;name;pic;en;id',  

    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '电影&动作片&喜剧片&爱情片&科幻片&恐怖片&剧情片&战争片&连续剧&国产剧&港台剧&日韩剧&欧美剧&综艺&动漫&短剧',
    //静态分类值
    class_url: '1&6&7&8&9&10&11&12&2&13&14&15&16&3&4&5',
 
    推荐: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    一级: '.category_movie;img&&alt;img&&data-src;.text-right&&Text;a&&href',    
    
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
// 假设 pdfa/pdh/pdfh 是解析 HTML 的工具函数（提取元素/属性/文本）


// 提取线路名称（如“线路1”“线路2”），用 $$$ 拼接
let r_ktabs = pdfa(html, '.episodesxq h2'); // 修正选择器：.episodesxq 下的 h2
VOD.vod_play_from = r_ktabs.map(it => pdfh(it, 'Text')).join('$$$');
let klists = [];
// 提取所有播放链接并按线路分类
let all_links = pdfa(html, '.episodesxq a'); // .episodesxq 下的所有 a 标签
let source1_links = []; // 线路1（URL不含 -2-）
let source2_links = []; // 线路2（URL含 -2-）

all_links.forEach(link => {
    const text = pdfh(link, 'a&&Text'); // 单集文本（如“第1集”）
    const url = pd(link, 'a&&href', input); // 提取 a 标签的 href 属性
    const episode = `${text}$${url}`; // 单集格式：文本$链接

    // 按 URL 特征区分线路
    if (url.includes('-2-')) {
        source2_links.push(episode);
    } else {
        source1_links.push(episode);
    }
});

// 最终格式：线路1单集#单集$$$线路2单集#单集
VOD.vod_play_url = [source1_links.join('#'), source2_links.join('#')].join('$$$');
}),

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


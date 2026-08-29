var rule = {
    author: '冰水化合物/251125/第1版',
    title: '牛牛影院',
    类型: '影视',
    //主页 网页的域名根
    host: 'https://t.hzczwh.com/',
    hostJs: ``,
    headers :{
    
        'User-Agent': 'MOBILE_UA'
},
    
    //不填就默认utf-8，根据网页源码所显示的格式填，根据需要可填UTF-8，GBK，GB2312
    编码: 'utf-8',
    timeout: 5000,
    //首页链接，可以是完整路径或者相对路径,用于分类获取和推荐获取
    homeUrl: '/',
    //分类链接,分类参数用fyclasss,页码用fypage，带筛选的用fyfilter，第一页无页码的用[]括起，处理方式同xbpq方式，fyfilter代表filter_url里内容
      url: 'https://t.hzczwh.com/vodtype/fyclass-fypage.html',
//  filter_url: '{{fl.cateId}}-{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}-{{fl.letter}}---fypage---{{fl.year}}',
//filter_url: '{{fl.cateId}}{{fl.area}}{{fl.by}}{{fl.class}}{{fl.letter}}/page/fypage',
    //↓详情页url
   detailUrl: '/voddetail/fyid.html',
    //↓搜索链接 可以是完整路径或者相对路径,用于分类获取和推荐获取 **代表搜索词 fypage代表页数
// searchUrl: 'https://www.xqkk.live/index.php/vod/search/page/fypage/wd**.html',
    // ↓ 搜索页找参数  数组标题图片副标题链接
  搜索: '*',
    //rss搜索写法
   //searchUrl: '/rss/index.xml?wd=**&page=fypage',
   //ajax搜索写法
   searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',

// 搜索: 'json:list;name;pic;en;id',  

    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '动作片&爱情片&科幻片&恐怖片&战争片&喜剧片&纪录片&剧情片&国产剧&港台剧&美剧&日韩剧&海外剧&快手短剧&抖音短剧&电影&电视剧&综艺&动漫',
    //静态分类值
    class_url: '5&6&7&8&9&10&11&12&13&14&15&16&25&28&29&1&2&3&4',
    //推荐列表可以单独写也是几个参数，和一级列表部分参数一样的可以用*代替，不一样写不一样的，全和一级一样，可以用一个*代替
    推荐: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    //数组、标题、图片、副标题、链接，分类页找参数
  //  一级: '.hl-list-item;a&&title;a&&data-original;.remarks&&Text;a&&href',

一级: $js.toString(() => {
    let klist = pdfa(request(input), '.haiyang-vodlist__box');
    //数组
    let k = klist.map(it => ({
        title: pdfh(it, 'a&&title'),
        //标题
        pic_url: pdfh(it, '.lazyload&&data-original'),
        //图片
        desc: pdfh(it, '.text-right&&Text'),
       // 副标题
        url: pdfh(it, 'a&&href'),
        //链接
        content: ''
    }));
    setResult(k);
}),

    //详情页找参数
    //第一部分分别是对应参数式中的标题、类型、图片、备注、年份、地区、导演、主演、简介
    //第二部分分别对应参数式中的线路数组和线路标题
    //第三部分分别对应参数式中的播放数组、播放列表、播放标题、播放链接
    
二级: $js.toString(() => {
    let html = request(input);
    VOD = {
        vod_id: input,
        vod_name: pdfh(html, 'h1.title&&Text').replace(/\d+\.\d+$/,''), // 剔除标题后评分
        type_name: pdfh(html, 'p.data:eq(0) a:eq(0)&&Text'), // 匹配第一个data行的类型链接文本
        vod_pic: pd(html, 'img.lazyload&&data-original', input), // 匹配懒加载图片的真实地址
        vod_remarks: pdfh(html, 'span.pic-text&&Text'), // 已完结状态
        vod_year: pdfh(html, 'p.data:eq(0) a:eq(2)&&Text'), // 匹配年份链接文本
        vod_area: pdfh(html, 'p.data:eq(0) a:eq(1)&&Text'), // 匹配地区链接文本
        vod_director: pdfh(html, 'p.data:contains(导演) a&&Text'), // 精准匹配导演链接
        vod_actor: pdfh(html, 'p.data:contains(主演)&&Text').replace('主演：','').replace(/<a[^>]+>/g,'').replace(/<\/a>/g,'').replace(/&nbsp;/g,' ').trim(), // 提取所有主演并去标签
        vod_content: pdfh(html, 'p.desc&&Text').replace('简介：','').replace(/详情.*$/,'').trim() // 截取简介核心内容
    };


         let r_ktabs = pdfa(html,'.haiyang-pannel_hd');
         //线路列表
 let ktabs = r_ktabs.map(it => pdfh(it, 'h3&&Text'));
         //线路名称
 VOD.vod_play_from = ktabs.join('$$$');

let klists = [];
let r_plists = pdfa(html, '.haiyang-content__playlist.clearfix.column8');
r_plists.forEach((rp) => {
    let klist = pdfa(rp, 'a').reverse().map((it) => {
        return pdfh(it, 'a&&Text') + '$' + pd(it, 'a&&href', input);
    }).filter(item => {
        // 过滤掉标题行和排序按钮
        return !item.includes('1080') && !item.includes('视频排序：正序');
    });
    klist = klist.join('#');
    klists.push(klist);
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
let kcode = JSON.parse(fetch(input).split('aaaa=')[1].split('<')[0]);
let kurl = kcode.url;
if (/\.(m3u8|mp4)/.test(kurl)) {
    input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
} else {
    input = { jx: 0, parse: 1, url: input }
}
})


    

    
}
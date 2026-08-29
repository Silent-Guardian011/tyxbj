var rule = {
    author: '冰水化合物/251130/第1版',
    title: '高清影院',
    类型: '影视',
    //主页 网页的域名根
    host: 'https://www.beizeer.com.cn/',
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
      url: 'https://www.gmsconcepts.com/forum/type/fyfilter',
//filter_url: '{{fl.cateId or "fyclass"}}-{{fl.area}}-{{fl.by}}-{{fl.class}}-{{fl.lang}}-{{fl.letter}}---fypage---{{fl.year}}',
  
 // filter_url: '{{fl.area}}{{fl.by}}{{fl.class}}/id/{{fl.cateId or "fyclass"}}{{fl.lang}}{{fl.letter}}/page/fypage{{fl.year}}',
filter_url: '{{fl.cateId}}{{fl.area}}{{fl.by}}{{fl.class}}{{fl.letter}}/page/fypage{{fl.year}}',

    //↓详情页url
  // detailUrl: '/type/fyid.html',
    //↓搜索链接 可以是完整路径或者相对路径,用于分类获取和推荐获取 **代表搜索词 fypage代表页数
 searchUrl: '/vodsearch/**----------fypage---.html',
    // ↓ 搜索页找参数  数组标题图片副标题链接
  搜索: '*',
    //rss搜索写法
   //searchUrl: '/rss/index.xml?wd=**&page=fypage',
   //ajax搜索写法
   //searchUrl: '/index.php/ajax/suggest?mid=1&wd=**&page=fypage&limit=30',

// 搜索: 'json:list;name;pic;en;id',  

    searchable: 1,
    quickSearch: 1,
    filterable: 1,
    limit: 10,
    double: false,
    class_name: '电影&电视剧&综艺&动漫&短剧&少儿',
    //静态分类值
    class_url: 'dianying&dianshiju&zongyipian&dongmanpian&duanjudaquan&fulipian',

    filter_def: {
        dianying: {
            cateId: 'dianying'
        },
        dianshiju: {
            cateId: 'dianshiju'
        },
        zongyipian: {
            cateId: 'zongyipian'
        },
        dongmanpian: {
            cateId: 'dongmanpian'
        },
        
     duanjudaquan: {
            cateId: 'duanjudaquan'
        },
        fulipian: {
            cateId: 'fulipian'
        },

    },
    //推荐列表可以单独写也是几个参数，和一级列表部分参数一样的可以用*代替，不一样写不一样的，全和一级一样，可以用一个*代替
    推荐: '*',
    //推荐页的json模式
    //推荐: 'json:list;vod_name;vod_pic;vod_remarks;vod_id',
    //数组、标题、图片、副标题、链接，分类页找参数
  //  一级: '.hl-list-item;a&&title;a&&data-original;.remarks&&Text;a&&href',

一级: $js.toString(() => {
    let klist = pdfa(request(input), '.hl-lazy');
    //数组
    let k = klist.map(it => ({
        title: pdfh(it, 'a&&title'),
        //标题
        pic_url: pdfh(it, 'a&&data-original'),
        //图片
        desc: pdfh(it, '.remarks&&Text'),
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
            vod_name: pdfh(html, 'h2&&Text'),
            type_name: pdfh(html, 'li:contains(类型)&&Text').replace('类型：',''),
            vod_pic: pd(html, '.lazyload&&data-original', input),
            vod_remarks: pdfh(html, 'li:contains(状态)&&Text').replace('状态：',''),
            vod_year: pdfh(html, 'li:contains(年份)&&Text').replace('年份：',''),
            vod_area: pdfh(html, 'li:contains(地区)&&Text').replace('地区：',''),
            vod_director: pdfh(html, 'li:contains(导演)&&Text').replace('导演：',''),
            vod_actor: pdfh(html, 'li:contains(主演)&&Text').replace('主演：',''),
            vod_content: pdfh(html, 'li:contains(简介)&&Text').replace('简介：','')
        };      
         let r_ktabs = pdfa(html,'.hl-plays-from.hl-tabs a');
         //线路列表
 let ktabs = r_ktabs.map(it => pdfh(it, 'a&&Text'));
         //线路名称
 VOD.vod_play_from = ktabs.join('$$$');

let klists = [];
//播放数组列表
let r_plists = pdfa(html, '.hl-plays-list.hl-sort-list.clearfix');
r_plists.forEach((rp) => {
    let klist = pdfa(rp, 'a').map((it) => {
        return pdfh(it, 'a&&Text') + '$' + pd(it, 'a&&href', input);
    }).filter(item => {
        // 过滤掉标题行和排序按钮
        return !item.includes('展开全部') && !item.includes('视频排序：正序');
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
}),

filter: {

    "dianying": [

      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "福利片", "v": "fulipian"},
          {"n": "动作片", "v": "dongzuopian"},
          {"n": "喜剧片", "v": "xijupian"},
          {"n": "爱情片", "v": "aiqingpian"},
          {"n": "科幻片", "v": "kehuanpian"},
          {"n": "恐怖片", "v": "kongbupian"},
          {"n": "剧情片", "v": "juqingpian"},
          {"n": "战争片", "v": "zhanzhengpian"},
          {"n": "动画片", "v": "donghuapian"},
          {"n": "纪录片", "v": "jilupian"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "理论", "v": "/class/理论"},
          {"n": "喜剧", "v": "/class/喜剧"},
          {"n": "爱情", "v": "/class/爱情"},
          {"n": "恐怖", "v": "/class/恐怖"},
          {"n": "动作", "v": "/class/动作"},
          {"n": "科幻", "v": "/class/科幻"},
          {"n": "剧情", "v": "/class/剧情"},
          {"n": "战争", "v": "/class/战争"},
          {"n": "警匪", "v": "/class/警匪"},
          {"n": "犯罪", "v": "/class/犯罪"},
          {"n": "动画", "v": "/class/动画"},
          {"n": "奇幻", "v": "/class/奇幻"},
          {"n": "武侠", "v": "/class/武侠"},
          {"n": "冒险", "v": "/class/冒险"},
          {"n": "枪战", "v": "/class/枪战"},
          {"n": "悬疑", "v": "/class/悬疑"},
          {"n": "惊悚", "v": "/class/惊悚"},
          {"n": "经典", "v": "/class/经典"},
          {"n": "青春", "v": "/class/青春"},
          {"n": "文艺", "v": "/class/文艺"},
          {"n": "微电影", "v": "/class/微电影"},
          {"n": "古装", "v": "/class/古装"},
          {"n": "历史", "v": "/class/历史"},
          {"n": "运动", "v": "/class/运动"},
          {"n": "农村", "v": "/class/农村"},
          {"n": "儿童", "v": "/class/儿童"},
          {"n": "网络电影", "v": "/class/网络电影"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "大陆", "v": "/area/大陆"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "美国", "v": "/area/美国"},
          {"n": "法国", "v": "/area/法国"},
          {"n": "英国", "v": "/area/英国"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "韩国", "v": "/area/韩国"},
          {"n": "德国", "v": "/area/德国"},
          {"n": "泰国", "v": "/area/泰国"},
          {"n": "印度", "v": "/area/印度"},
          {"n": "意大利", "v": "/area/意大利"},
          {"n": "西班牙", "v": "/area/西班牙"},
          {"n": "加拿大", "v": "/area/加拿大"},
          {"n": "其他", "v": "/area/其他"}
        ]
      },
      {
        "key": "year",
        "name": "年份",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "2025", "v": "/year/2025"},
          {"n": "2024", "v": "/year/2024"},
          {"n": "2023", "v": "/year/2023"},
          {"n": "2022", "v": "/year/2022"},
          {"n": "2021", "v": "/year/2021"},
          {"n": "2020", "v": "/year/2020"},
          {"n": "2019", "v": "/year/2019"},
          {"n": "2018", "v": "/year/2018"},
          {"n": "2017", "v": "/year/2017"},
          {"n": "2016", "v": "/year/2016"},
          {"n": "2015", "v": "/year/2015"},
          {"n": "2014", "v": "/year/2014"},
          {"n": "2013", "v": "/year/2013"},
          {"n": "2012", "v": "/year/2012"},
          {"n": "2011", "v": "/year/2011"},
          {"n": "2010", "v": "/year/2010"},
          {"n": "2009", "v": "/year/2009"},
          {"n": "2008", "v": "/year/2008"},
          {"n": "2007", "v": "/year/2007"},
          {"n": "2006", "v": "/year/2006"},
          {"n": "2005", "v": "/year/2005"},
          {"n": "2004", "v": "/year/2004"},
          {"n": "2003", "v": "/year/2003"},
          {"n": "2002", "v": "/year/2002"},
          {"n": "2001", "v": "/year/2001"},
          {"n": "2000", "v": "/year/2000"}
        ]
      },
      {
        "key": "lang",
        "name": "语言",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国语", "v": "/lang/国语"},
          {"n": "英语", "v": "/lang/英语"},
          {"n": "粤语", "v": "/lang/粤语"},
          {"n": "闽南语", "v": "/lang/闽南语"},
          {"n": "韩语", "v": "/lang/韩语"},
          {"n": "日语", "v": "/lang/日语"},
          {"n": "法语", "v": "/lang/法语"},
          {"n": "德语", "v": "/lang/德语"},
          {"n": "其他", "v": "/lang/其他"}
        ]
      },
{
  "key": "letter",
  "name": "字母",
  "value": [
    {"n": "全部", "v": ""},
    {"n": "A", "v": "/letter/A"},
    {"n": "B", "v": "/letter/B"},
    {"n": "C", "v": "/letter/C"},
    {"n": "D", "v": "/letter/D"},
    {"n": "E", "v": "/letter/E"},
    {"n": "F", "v": "/letter/F"},
    {"n": "G", "v": "/letter/G"},
    {"n": "H", "v": "/letter/H"},
    {"n": "I", "v": "/letter/I"},
    {"n": "J", "v": "/letter/J"},
    {"n": "K", "v": "/letter/K"},
    {"n": "L", "v": "/letter/L"},
    {"n": "M", "v": "/letter/M"},
    {"n": "N", "v": "/letter/N"},
    {"n": "O", "v": "/letter/O"},
    {"n": "P", "v": "/letter/P"},
    {"n": "Q", "v": "/letter/Q"},
    {"n": "R", "v": "/letter/R"},
    {"n": "S", "v": "/letter/S"},
    {"n": "T", "v": "/letter/T"},
    {"n": "U", "v": "/letter/U"},
    {"n": "V", "v": "/letter/V"},
    {"n": "W", "v": "/letter/W"},
    {"n": "X", "v": "/letter/X"},
    {"n": "Y", "v": "/letter/Y"},
    {"n": "Z", "v": "/letter/Z"},
    {"n": "0-9", "v": "/letter/0-9"}
  ]
},
{
  "key": "by",
  "name": "排序",
  "value": [
    {"n": "按最新", "v": "/by/time"},
    {"n": "按最热", "v": "/by/hits"},
    {"n": "按评分", "v": "/by/score"}
  ]
}

        ],


    "dianshiju": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国产剧", "v": "guochanju"},
          {"n": "香港剧", "v": "xianggangju"},
          {"n": "台湾剧", "v": "taiwanju"},
          {"n": "欧美剧", "v": "oumeiju"},
          {"n": "日本剧", "v": "ribenju"},
          {"n": "韩国剧", "v": "hanguoju"},
          {"n": "泰国剧", "v": "taiguoju"},
          {"n": "海外剧", "v": "haiwaiju"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "古装", "v": "/class/古装"},
          {"n": "战争", "v": "/class/战争"},
          {"n": "青春偶像", "v": "/class/青春偶像"},
          {"n": "喜剧", "v": "/class/喜剧"},
          {"n": "家庭", "v": "/class/家庭"},
          {"n": "犯罪", "v": "/class/犯罪"},
          {"n": "动作", "v": "/class/动作"},
          {"n": "奇幻", "v": "/class/奇幻"},
          {"n": "剧情", "v": "/class/剧情"},
          {"n": "历史", "v": "/class/历史"},
          {"n": "经典", "v": "/class/经典"},
          {"n": "乡村", "v": "/class/乡村"},
          {"n": "情景", "v": "/class/情景"},
          {"n": "商战", "v": "/class/商战"},
          {"n": "网剧", "v": "/class/网剧"},
          {"n": "其他", "v": "/class/其他"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "内地", "v": "/area/内地"},
          {"n": "韩国", "v": "/area/韩国"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "美国", "v": "/area/美国"},
          {"n": "泰国", "v": "/area/泰国"},
          {"n": "英国", "v": "/area/英国"},
          {"n": "新加坡", "v": "/area/新加坡"}
        ]
},{
        "key": "year",
        "name": "年份",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "2025", "v": "/year/2025"},
          {"n": "2024", "v": "/year/2024"},
          {"n": "2023", "v": "/year/2023"},
          {"n": "2022", "v": "/year/2022"},
          {"n": "2021", "v": "/year/2021"},
          {"n": "2020", "v": "/year/2020"},
          {"n": "2019", "v": "/year/2019"},
          {"n": "2018", "v": "/year/2018"},
          {"n": "2017", "v": "/year/2017"},
          {"n": "2016", "v": "/year/2016"},
          {"n": "2015", "v": "/year/2015"},
          {"n": "2014", "v": "/year/2014"},
          {"n": "2013", "v": "/year/2013"},
          {"n": "2012", "v": "/year/2012"},
          {"n": "2011", "v": "/year/2011"},
          {"n": "2010", "v": "/year/2010"},
          {"n": "2009", "v": "/year/2009"},
          {"n": "2008", "v": "/year/2008"},
          {"n": "2007", "v": "/year/2007"},
          {"n": "2006", "v": "/year/2006"},
          {"n": "2005", "v": "/year/2005"},
          {"n": "2004", "v": "/year/2004"},
          {"n": "2003", "v": "/year/2003"},
          {"n": "2002", "v": "/year/2002"},
          {"n": "2001", "v": "/year/2001"},
          {"n": "2000", "v": "/year/2000"}
        ]
      },{
        "key": "lang",
        "name": "语言",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国语", "v": "/lang/国语"},
          {"n": "英语", "v": "/lang/英语"},
          {"n": "粤语", "v": "/lang/粤语"},
          {"n": "闽南语", "v": "/lang/闽南语"},
          {"n": "韩语", "v": "/lang/韩语"},
          {"n": "日语", "v": "/lang/日语"},
          {"n": "法语", "v": "/lang/法语"},
          {"n": "德语", "v": "/lang/德语"},
          {"n": "其他", "v": "/lang/其他"}
        ]
      },{
  "key": "letter",
  "name": "字母",
  "value": [
    {"n": "全部", "v": ""},
    {"n": "A", "v": "/letter/A"},
    {"n": "B", "v": "/letter/B"},
    {"n": "C", "v": "/letter/C"},
    {"n": "D", "v": "/letter/D"},
    {"n": "E", "v": "/letter/E"},
    {"n": "F", "v": "/letter/F"},
    {"n": "G", "v": "/letter/G"},
    {"n": "H", "v": "/letter/H"},
    {"n": "I", "v": "/letter/I"},
    {"n": "J", "v": "/letter/J"},
    {"n": "K", "v": "/letter/K"},
    {"n": "L", "v": "/letter/L"},
    {"n": "M", "v": "/letter/M"},
    {"n": "N", "v": "/letter/N"},
    {"n": "O", "v": "/letter/O"},
    {"n": "P", "v": "/letter/P"},
    {"n": "Q", "v": "/letter/Q"},
    {"n": "R", "v": "/letter/R"},
    {"n": "S", "v": "/letter/S"},
    {"n": "T", "v": "/letter/T"},
    {"n": "U", "v": "/letter/U"},
    {"n": "V", "v": "/letter/V"},
    {"n": "W", "v": "/letter/W"},
    {"n": "X", "v": "/letter/X"},
    {"n": "Y", "v": "/letter/Y"},
    {"n": "Z", "v": "/letter/Z"},
    {"n": "0-9", "v": "/letter/0-9"}
  ]
},{
  "key": "by",
  "name": "排序",
  "value": [
    {"n": "按最新", "v": "/by/time"},
    {"n": "按最热", "v": "/by/hits"},
    {"n": "按评分", "v": "/by/score"}
  ]
}

        ],


    "zongyipian": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "大陆综艺", "v": "daluzongyi"},
          {"n": "欧美综艺", "v": "oumeizongyi"},
          {"n": "港台综艺", "v": "gangtaizongyi"},
          {"n": "日韩综艺", "v": "rihanzongyi"}
        ]
      },
      {
        "key": "class",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "选秀", "v": "/class/选秀"},
          {"n": "情感", "v": "/class/情感"},
          {"n": "访谈", "v": "/class/访谈"},
          {"n": "播报", "v": "/class/播报"},
          {"n": "旅游", "v": "/class/旅游"},
          {"n": "音乐", "v": "/class/音乐"},
          {"n": "美食", "v": "/class/美食"},
          {"n": "纪实", "v": "/class/纪实"},
          {"n": "曲艺", "v": "/class/曲艺"},
          {"n": "生活", "v": "/class/生活"},
          {"n": "游戏互动", "v": "/class/游戏互动"},
          {"n": "财经", "v": "/class/财经"},
          {"n": "求职", "v": "/class/求职"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "内地", "v": "/area/大陆"},
          {"n": "港台", "v": "/area/港台"},
          {"n": "日韩", "v": "/area/日韩"},
          {"n": "欧美", "v": "/area/欧美"}
        ]
      },
{
  "key": "letter",
  "name": "字母",
  "value": [
    {"n": "全部", "v": ""},
    {"n": "A", "v": "/letter/A"},
    {"n": "B", "v": "/letter/B"},
    {"n": "C", "v": "/letter/C"},
    {"n": "D", "v": "/letter/D"},
    {"n": "E", "v": "/letter/E"},
    {"n": "F", "v": "/letter/F"},
    {"n": "G", "v": "/letter/G"},
    {"n": "H", "v": "/letter/H"},
    {"n": "I", "v": "/letter/I"},
    {"n": "J", "v": "/letter/J"},
    {"n": "K", "v": "/letter/K"},
    {"n": "L", "v": "/letter/L"},
    {"n": "M", "v": "/letter/M"},
    {"n": "N", "v": "/letter/N"},
    {"n": "O", "v": "/letter/O"},
    {"n": "P", "v": "/letter/P"},
    {"n": "Q", "v": "/letter/Q"},
    {"n": "R", "v": "/letter/R"},
    {"n": "S", "v": "/letter/S"},
    {"n": "T", "v": "/letter/T"},
    {"n": "U", "v": "/letter/U"},
    {"n": "V", "v": "/letter/V"},
    {"n": "W", "v": "/letter/W"},
    {"n": "X", "v": "/letter/X"},
    {"n": "Y", "v": "/letter/Y"},
    {"n": "Z", "v": "/letter/Z"},
    {"n": "0-9", "v": "/letter/0-9"}
  ]
},{
  "key": "by",
  "name": "排序",
  "value": [
    {"n": "按最新", "v": "/by/time"},
    {"n": "按最热", "v": "/by/hits"},
    {"n": "按评分", "v": "/by/score"}
  ]
}

        ],

    "dongmanpian": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国产动漫", "v": "guochandongman"},
          {"n": "日韩动漫", "v": "rihandongman"},
          {"n": "欧美动漫", "v": "oumeidongman"},
          {"n": "港台动漫", "v": "gangtaidongman"},
          {"n": "海外动漫", "v": "haiwaidongman"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "情感", "v": "/class/情感"},
          {"n": "科幻", "v": "/class/科幻"},
          {"n": "热血", "v": "/class/热血"},
          {"n": "推理", "v": "/class/推理"},
          {"n": "搞笑", "v": "/class/搞笑"},
          {"n": "冒险", "v": "/class/冒险"},
          {"n": "萝莉", "v": "/class/萝莉"},
          {"n": "校园", "v": "/class/校园"},
          {"n": "动作", "v": "/class/动作"},
          {"n": "机战", "v": "/class/机战"},
          {"n": "运动", "v": "/class/运动"},
          {"n": "战争", "v": "/class/战争"},
          {"n": "少年", "v": "/class/少年"},
          {"n": "少女", "v": "/class/少女"},
          {"n": "社会", "v": "/class/社会"},
          {"n": "原创", "v": "/class/原创"},
          {"n": "亲子", "v": "/class/亲子"},
          {"n": "益智", "v": "/class/益智"},
          {"n": "励志", "v": "/class/励志"},
          {"n": "其他", "v": "/class/其他"}
        ]
      },
      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国产", "v": "/area/大陆"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "欧美", "v": "/area/欧美"},
          {"n": "其他", "v": "/area/其他"}
        ]
      },
{
  "key": "letter",
  "name": "字母",
  "value": [
    {"n": "全部", "v": ""},
    {"n": "A", "v": "/letter/A"},
    {"n": "B", "v": "/letter/B"},
    {"n": "C", "v": "/letter/C"},
    {"n": "D", "v": "/letter/D"},
    {"n": "E", "v": "/letter/E"},
    {"n": "F", "v": "/letter/F"},
    {"n": "G", "v": "/letter/G"},
    {"n": "H", "v": "/letter/H"},
    {"n": "I", "v": "/letter/I"},
    {"n": "J", "v": "/letter/J"},
    {"n": "K", "v": "/letter/K"},
    {"n": "L", "v": "/letter/L"},
    {"n": "M", "v": "/letter/M"},
    {"n": "N", "v": "/letter/N"},
    {"n": "O", "v": "/letter/O"},
    {"n": "P", "v": "/letter/P"},
    {"n": "Q", "v": "/letter/Q"},
    {"n": "R", "v": "/letter/R"},
    {"n": "S", "v": "/letter/S"},
    {"n": "T", "v": "/letter/T"},
    {"n": "U", "v": "/letter/U"},
    {"n": "V", "v": "/letter/V"},
    {"n": "W", "v": "/letter/W"},
    {"n": "X", "v": "/letter/X"},
    {"n": "Y", "v": "/letter/Y"},
    {"n": "Z", "v": "/letter/Z"},
    {"n": "0-9", "v": "/letter/0-9"}
  ]
},{
  "key": "by",
  "name": "排序",
  "value": [
    {"n": "按最新", "v": "/by/time"},
    {"n": "按最热", "v": "/by/hits"},
    {"n": "按评分", "v": "/by/score"}
  ]
}

],

    "duanjudaquan": [
      {
        "key": "cateId",
        "name": "类型",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "重生民国", "v": "chongshengminguo"},
          {"n": "穿越年代", "v": "chuanyueniandai"},
          {"n": "现代言情", "v": "xiandaiyanqing"},
          {"n": "反转爽文", "v": "fanzhuanshuangwen"},
          {"n": "女恋总裁", "v": "nvlianzongcai"},
          {"n": "闪婚离婚", "v": "shanhunlihun"},
          {"n": "都市脑洞", "v": "dushinaodong"},
          {"n": "古装仙侠", "v": "guzhuangxianxia"}
        ]
      },
      {
        "key": "class",
        "name": "剧情",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "穿越", "v": "/class/穿越"},
          {"n": "重生", "v": "/class/重生"},
          {"n": "现代", "v": "/class/现代"},
          {"n": "都市", "v": "/class/都市"},
          {"n": "古装", "v": "/class/古装"},
          {"n": "仙侠", "v": "/class/仙侠"},
          {"n": "剧情", "v": "/class/剧情"},
          {"n": "喜剧", "v": "/class/喜剧"},
          {"n": "纪录", "v": "/class/纪录"},
          {"n": "动画", "v": "/class/动画"},
          {"n": "微电影", "v": "/class/微电影"}
        ]
      }
        ],

    "fulipian": [

      {
        "key": "area",
        "name": "地区",
        "value": [
          {"n": "全部", "v": ""},
          {"n": "国产", "v": "/area/大陆"},
          {"n": "日本", "v": "/area/日本"},
          {"n": "香港", "v": "/area/香港"},
          {"n": "台湾", "v": "/area/台湾"},
          {"n": "泰国", "v": "/area/泰国"},
          {"n": "韩国", "v": "/area/韩国"}
        ]
      },

{
  "key": "by",
  "name": "排序",
  "value": [
    {"n": "按最新", "v": "/by/time"},
    {"n": "按最热", "v": "/by/hits"},
    {"n": "按评分", "v": "/by/score"}
  ]
}

]
    }

    
}
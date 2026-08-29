var rule = {
    title: '[密] 鸭鸭视频',
    
    host: 'https://www.forduck29.com/',
    url: 'https://www.forduck29.com/searchav?k=fyclass&p=fypage',
    homeUrl: 'https://www.forduck29.com/searchav?k=%E4%B8%AD%E5%9B%BD%E5%9B%BD%E4%BA%A7',
    
   searchUrl: 'https://www.forduck29.com/searchav?k=**&p=fypage',
    detailUrl: '',

    searchable: 2,
    quickSearch: 1,
    filterable: 1,
    limit: 30,
    编码: 'utf-8',
    timeout: 5000,
    headers: {
      'User-Agent': 'Mozilla/5.0 (Linux; Android 15; RMX3770 Build/AP3A.240617.008; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.6723.58 Mobile Safari/537.36',
      'referer': ''
      
    
    },
  class_parse: 'grids a:has(img);a&&title;a&&href;/searchav\\?k=([^&]+)',
  
  
    
    
    
   class_name: '人兽&排泄&日本人&中国国产&角色扮演&黑丝&麻豆传媒&恋足&台湾SWAG&巨乳&青少年&制服&口交&熟女&大学生&校园&网红主播&女同&恋物癖&高清&Cosplay&贫乳&女性自慰&素人&韩国人&爆菊&色情日漫&亚洲人&女仆&3P&辣妈&卡通&公众野战&老少配&内射中出&捆绑&女性高潮&巨屌&潮吹&多人&黑人女&俄国人&乱交群欢&合集&肥臀&风情少女&按摩&粗暴性爱&射精&第一视角&试镜&指交&金发女&纹身女&音乐&录音&人妖系列&肌肉男&双性恋男&男同&男性自慰',
   class_url:  '人兽&排泄&jav&中国国产&角色扮演&黑丝&麻豆传媒&恋足&台湾SWAG&巨乳&青少年&制服&口交&熟女&大学生&校园&网红主播&女同&恋物癖&高清&Cosplay&贫乳&女性自慰&素人&韩国人&爆菊&色情日漫&亚洲人&女仆&3P&辣妈&卡通&公众野战&老少配&内射中出&捆绑&女性高潮&巨屌&色情日漫&亚洲人&女仆&3P&辣妈&卡通&公众野战&老少配&内射中出&捆绑&女性高潮&巨屌&潮吹&多人&黑人女&俄国人&乱交群欢&合集&肥臀&风情少女&按摩&粗暴性爱&射精&vr&试镜&潮吹&多人&黑人女&俄国人&乱交群欢&合集&肥臀&风情少女&按摩&粗暴性爱&射精&第一视角&试镜指交&金发女&纹身女&音乐&录音&人妖系列&肌肉男&双性恋男&男同&男性自慰',
//    图片来源: '@Referer=https://xg.acubsam.top/label/sort/@User-Agent=Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
    
    //是否启用辅助嗅探: 1,0
    sniffer: 0,
    // 辅助嗅探规则
    isVideo: 'http((?!http).){26,}\\.(m3u8|mp4|flv|avi|mkv|wmv|mpg|mpeg|mov|ts|3gp|rm|rmvb|asf|m4a|mp3|wma)',
    play_parse: true,
   lazy: $js.toString(() => {
        input = {
            parse: 1,
            url: input,
            js: 'document.querySelector("#playleft iframe").contentWindow.document.querySelector("#start").click();'
        };
    }),
        
    
  lazy: $js.toString(() => {
    
    let kurl = fetch(input).split('html5player.setVideoHLS(\'')[1].split('\')')[0].replace(/\\\//g, '/');

if (/\.(m3u8|mp4)/.test(kurl)) {
    input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
} else {
    input = { jx: 0, parse: 1, url: input }
}
}),
/*
  let kcode = JSON.parse(fetch(input).split('aaaa=')[1].split('<')[0]);
let kurl = kcode.url;
if (/\.(m3u8|mp4)/.test(kurl)) {
    input = { jx: 0, parse: 0, url: kurl, header: {'User-Agent': MOBILE_UA, 'Referer': getHome(kurl)} }
} else {
    input = { jx: 0, parse: 1, url: input }
}
}),*/

    double: false,
    
    tab_rename: {
        '道长在线': '鸭鸭专线'
    },
    hikerListCol: "movie_2",
    hikerClassListCol: "movie_2",
    推荐: '*',
    
/*    一级: $js.toString(() => {
    let klist=pdfa(request(input),'.item:has(.img)');
     let k=[];
    klist.forEach(it=>{
     k.push({
    title: pdfh(it,'a&&title'),
     pic_url: !pdfh(it,'.lazyload&&data-src').startsWith('http') ? HOST + pdfh(it,'.lazyload&&data-src') : pdfh(it,'.lazyload&&data-src'),

    desc: '请您欣赏！',
     url: pdfh(it,'a&&href'),
    content: ''    
     })
    });
    setResult(k)
    }),*/
    
    

  一级: '.frame-block;p&&a&&title;img&&data-src;.duration&&Text;a&&href',
    二级: '*',
   搜索: '.frame-block;p&&a&&title;img&&data-src;.duration&&Text;a&&href',
}
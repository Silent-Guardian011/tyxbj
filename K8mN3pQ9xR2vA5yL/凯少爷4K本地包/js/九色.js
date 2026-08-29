var rule = {
    author: '',
    title: '九色',
    //网站域名
    host: 'https://c.jstv9170.com/',
    //分类url        
    url: '/video/category/fyclass/fypage',
    //主页url
    homeUrl: '/video',
    //搜索url
    searchUrl: '/search?keywords=**&page=fypage',
    //是否启用全局搜索,
    searchable: 2,
    //是否启用快速搜索,
    quickSearch: 1,
    //是否启用分类筛选,
    filterable: 1,
    limit: 30,
    编码: 'utf-8',
    timeout: 5000,
    //请求头
    headers: {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 13; M2102J2SC Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/138.0.7204.3 Mobile Safari/537.36'
    },
    //静态分类
    //class_name: '国产传媒',
    //静态分类值
    //class_url: 'hd',
    //动态分类: '定位数组;标题;链接;链接正则匹配',
    class_parse: '.list .item;div&&Text;div&&data-href;/video/category/(.*)',

    //推荐: '数组;标题;图片;副标题;链接',
    推荐: '*',
    //一级: '数组;标题;图片;副标题;链接',
    一级: '.row .colVideoList;.title&&Text;.img&&style;.vip-layer&&Text;a&&href',

    二级: {
        tabs: '.justify-content-center&&.nav-item:eq(1)',
        lists: '.justify-content-center&&.nav-item',
    },
    //搜索: '搜索数组;标题;图片;副标题;链接',
    搜索: '.row .colVideoList;.title&&Text;.img&&style;.vip-layer&&Text;a&&href',
}
var rule = {
    title: '麒麟影视',
    host: 'https://www.70ys.site',
    //域名
    url: '/index.php/vod/type/id/fyclass/page/fypage.html',
    //分类url
    homeUrl: '/index.php/vod/type/id/fyclass.html',
    //主页url
    searchUrl: '/index.php/vod/search.html?wd=**',
    //搜索url
    searchable: 2,
    quickSearch: 1,
    filterable: 1,
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36 SE 2.X MetaSr 1.0',
    },
    //请求头
    class_name: '电影&剧集&综艺&动漫&短剧&少儿',
    //分类: '电影&剧集&综艺&动漫&短剧&少儿',
    class_url: '1&2&3&4&5&46',
    //分类值: '1&2&3&4&5&46',
    推荐: '*',
    //推荐: '数组;标题;图片;副标题;链接',
    一级: '.show_play;a&&title;img&&data-original;.tc_wz&&Text;a&&href',
    //一级: '数组;标题;图片;副标题;链接',
    二级: {
        title: 'h1&&Text;i:contains(类型)&&Text',
        img: '.detail-pic&&data-src',
        desc: 'i:contains(状态)&&Text;i:contains(年份)&&Text;i:contains(地区)&&Text;i:contains(主演)&&Text;i:contains(导演)&&Text',
        content: '.yplx_c3.hidden-mobile&&Text',
        tabs: '.playlist-tab&&.con_c2_title&&li',
        tab_text: '.tab-switch&&Text',
        lists: '.con_c2_list&&li',
        list_text: 'Text',
        list_url: 'a&&href',
    },
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
    搜索: '.reusltbox;.result_title&&Text;img&&src;li:contains(状态)&&Text;a&&href',
    //搜索: '数组;标题;图片;副标题;链接',
}
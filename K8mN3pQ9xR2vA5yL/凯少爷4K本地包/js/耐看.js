var rule = {
    title: '耐看影视',
    host: 'https://nkvod.me',
    //域名
    url: '/show/fyclass--------fypage---.html',
    //分类url
    homeUrl: '/show/fyclass-----------.html',
    //主页url
    searchUrl: '/nk/-------------.html?wd=**',
    //搜索url
    searchable: 2,
    quickSearch: 1,
    filterable: 1,
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36 SE 2.X MetaSr 1.0',
    },
    //请求头
    class_name: '电影&电视剧&综艺&动漫',
    //分类: '电影&电视剧&综艺&动漫',
    class_url: '1&2&3&4',
    //分类值: '1&2&3&4',
    推荐: '*',
    //推荐: '数组;标题;图片;副标题;链接',
    一级: '.public-list-box;a&&title;img&&data-src;.public-list-subtitle&&Text;a&&href',
    //一级: '数组;标题;图片;副标题;链接',
    二级: {
        title: 'h3&&Text;li:contains(类型)&&Text',
        img: '.detail-pic&&data-src',
        desc: 'li:contains(状态)&&Text;li:contains(年份)&&Text;li:contains(地区)&&Text;li:contains(主演)&&Text;li:contains(导演)&&Text',
        content: 'li:contains(简介)&&Text',
        tabs: '.anthology-tab&&.swiper-wrapper&&a',
        tab_text: '.swiper-slide&&Text',
        lists: '.anthology-list-box&&.anthology-list-play&&li',
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
    搜索: '*',
    //搜索: '数组;标题;图片;副标题;链接',
}
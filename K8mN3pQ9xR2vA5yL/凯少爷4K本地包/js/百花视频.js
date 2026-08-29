var rule = {
    title: '百花视频',
    host: 'https://www.bh1014.top',
    //域名
    url: '/type/fyclass/fypage',
    //分类url
    homeUrl: '/type/fyclass/fypage',
    //主页url
    searchUrl: '/search/video/**/fypage',
    //搜索url
    searchable: 2,
    quickSearch: 1,
    filterable: 1,
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36 SE 2.X MetaSr 1.0',
    },
    //请求头
    class_name: '国产&日本无码&日本有码&欧美&动漫&主播专区&网曝黑料&AV解说&伦理三级&AI换脸',
    //分类: '国产&日本无码&日本有码&欧美&动漫&主播专区&网曝黑料&AV解说&伦理三级&AI换脸',
    class_url: '1&2&3&4&5&6&7&8&9&10',
    //分类值: '1&2&3&4&5&6&7&8&9&10',
    推荐: '*',
    //推荐: '数组;标题;图片;副标题;链接',
    一级: '.item;.title&&Text;img&&src;.duration.iconfont&&Text;a&&href',
    //一级: '数组;标题;图片;副标题;链接',
    二级: '*',
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
    搜索: '.item;.title&&Text;img&&src;.duration.iconfont&&Text;a&&href',
    //搜索: '数组;标题;图片;副标题;链接',
}
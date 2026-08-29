/**
 * 清风影视爬虫
 * @config
 * debug: true
 * percent: 80,60
 * returnType: dom
 * timeout: 30
 * keywords: 系统安全验证|系统提示|人机验证
 * blockImages: true
 * blockList: *.[ico|png|jpeg|jpg|gif|webp]*|*.css
 */
const baseUrl = 'https://www.tuozhuhao.com';
function init(cfg) {
	console.log('初始化被调用')
    return {};
}
async function homeContent(filter) {
    const filterConfig = {
        class: [
            { type_id: "1", type_name: "电影" },
            { type_id: "2", type_name: "剧集" },
            { type_id: "3", type_name: "综艺" },
            { type_id: "4", type_name: "动漫" },
            { type_id: "5", type_name: "短剧" }
        ],
        filters: {
            "1": [
                { key: "cateId", name: "分类", value: [ {n:"全部",v:""}, {n:"动作片",v:"6"}, {n:"喜剧片",v:"7"}, {n:"爱情片",v:"8"}, {n:"科幻片",v:"9"}, {n:"恐怖片",v:"10"}, {n:"剧情片",v:"11"}, {n:"战争片",v:"12"}, {n:"纪录片",v:"13"}, {n:"悬疑片",v:"14"}, {n:"犯罪片",v:"15"}, {n:"奇幻片",v:"16"}, {n:"动画片",v:"31"}, {n:"预告片",v:"32"} ] },
                { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"喜剧",v:"喜剧"}, {n:"爱情",v:"爱情"}, {n:"恐怖",v:"恐怖"}, {n:"动作",v:"动作"}, {n:"科幻",v:"科幻"}, {n:"剧情",v:"剧情"}, {n:"战争",v:"战争"}, {n:"警匪",v:"警匪"}, {n:"犯罪",v:"犯罪"}, {n:"动画",v:"动画"}, {n:"奇幻",v:"奇幻"}, {n:"武侠",v:"武侠"}, {n:"冒险",v:"冒险"}, {n:"枪战",v:"枪战"}, {n:"悬疑",v:"悬疑"}, {n:"惊悚",v:"惊悚"}, {n:"经典",v:"经典"}, {n:"青春",v:"青春"}, {n:"文艺",v:"文艺"}, {n:"微电影",v:"微电影"}, {n:"古装",v:"古装"}, {n:"历史",v:"历史"}, {n:"运动",v:"运动"}, {n:"农村",v:"农村"}, {n:"儿童",v:"儿童"}, {n:"网络电影",v:"网络电影"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"大陆",v:"大陆"}, {n:"香港",v:"香港"}, {n:"台湾",v:"台湾"}, {n:"美国",v:"美国"}, {n:"法国",v:"法国"}, {n:"英国",v:"英国"}, {n:"日本",v:"日本"}, {n:"韩国",v:"韩国"}, {n:"德国",v:"德国"}, {n:"泰国",v:"泰国"}, {n:"印度",v:"印度"}, {n:"意大利",v:"意大利"}, {n:"西班牙",v:"西班牙"}, {n:"加拿大",v:"加拿大"}, {n:"其他",v:"其他"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"法语",v:"法语"}, {n:"德语",v:"德语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "2": [
                { key: "cateId", name: "分类", value: [ {n:"全部",v:""}, {n:"国产剧",v:"17"}, {n:"港台剧",v:"18"}, {n:"日韩剧",v:"20"}, {n:"欧美剧",v:"21"}, {n:"海外剧",v:"22"} ] },
                { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"古装",v:"古装"}, {n:"战争",v:"战争"}, {n:"青春偶像",v:"青春偶像"}, {n:"喜剧",v:"喜剧"}, {n:"家庭",v:"家庭"}, {n:"犯罪",v:"犯罪"}, {n:"动作",v:"动作"}, {n:"奇幻",v:"奇幻"}, {n:"剧情",v:"剧情"}, {n:"历史",v:"历史"}, {n:"经典",v:"经典"}, {n:"乡村",v:"乡村"}, {n:"情景",v:"情景"}, {n:"商战",v:"商战"}, {n:"网剧",v:"网剧"}, {n:"其他",v:"其他"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"内地",v:"内地"}, {n:"韩国",v:"韩国"}, {n:"香港",v:"香港"}, {n:"台湾",v:"台湾"}, {n:"日本",v:"日本"}, {n:"美国",v:"美国"}, {n:"泰国",v:"泰国"}, {n:"英国",v:"英国"}, {n:"新加坡",v:"新加坡"}, {n:"其他",v:"其他"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "3": [
                { key: "cateId", name: "分类", value: [ {n:"全部",v:""}, {n:"大陆综艺",v:"23"}, {n:"日韩综艺",v:"24"}, {n:"欧美综艺",v:"25"}, {n:"港台综艺",v:"26"} ] },
                { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"选秀",v:"选秀"}, {n:"情感",v:"情感"}, {n:"访谈",v:"访谈"}, {n:"播报",v:"播报"}, {n:"旅游",v:"旅游"}, {n:"音乐",v:"音乐"}, {n:"美食",v:"美食"}, {n:"纪实",v:"纪实"}, {n:"曲艺",v:"曲艺"}, {n:"生活",v:"生活"}, {n:"游戏互动",v:"游戏互动"}, {n:"财经",v:"财经"}, {n:"求职",v:"求职"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"内地",v:"内地"}, {n:"港台",v:"港台"}, {n:"日韩",v:"日韩"}, {n:"欧美",v:"欧美"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"}, {n:"2009",v:"2009"}, {n:"2008",v:"2008"}, {n:"2007",v:"2007"}, {n:"2006",v:"2006"}, {n:"2005",v:"2005"}, {n:"2004",v:"2004"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "4": [
                { key: "cateId", name: "分类", value: [ {n:"全部",v:""}, {n:"国产动漫",v:"27"}, {n:"日韩动漫",v:"28"}, {n:"欧美动漫",v:"29"}, {n:"其他动漫",v:"30"} ] },
                { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"情感",v:"情感"}, {n:"科幻",v:"科幻"}, {n:"热血",v:"热血"}, {n:"推理",v:"推理"}, {n:"搞笑",v:"搞笑"}, {n:"冒险",v:"冒险"}, {n:"萝莉",v:"萝莉"}, {n:"校园",v:"校园"}, {n:"动作",v:"动作"}, {n:"机战",v:"机战"}, {n:"运动",v:"运动"}, {n:"战争",v:"战争"}, {n:"少年",v:"少年"}, {n:"少女",v:"少女"}, {n:"社会",v:"社会"}, {n:"原创",v:"原创"}, {n:"亲子",v:"亲子"}, {n:"益智",v:"益智"}, {n:"励志",v:"励志"}, {n:"其他",v:"其他"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"国产",v:"国产"}, {n:"日本",v:"日本"}, {n:"欧美",v:"欧美"}, {n:"其他",v:"其他"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"}, {n:"2009",v:"2009"}, {n:"2008",v:"2008"}, {n:"2007",v:"2007"}, {n:"2006",v:"2006"}, {n:"2005",v:"2005"}, {n:"2004",v:"2004"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "5": [
                { key: "class", name: "类型", value: [ {n:"全部",v:""}, {n:"短剧",v:"短剧"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"大陆",v:"大陆"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ]
        }
    };
    return filterConfig;
}
async function homeVideoContent() {
    const document = await Java.wvOpen(baseUrl);
    return { list: parseVideoList() };
}
async function categoryContent(tid, pg, filter, extend) {
    console.log(`分类: tid=${tid}, pg=${pg}`);
	const document = await Java.wvOpen(`${baseUrl}/haosw/${extend?.cateId||tid}-${extend?.area}-${extend?.by}-${extend?.class}-${extend?.lang}-${extend?.letter}---${pg||1}---${extend?.year}.html`);		
    const pagecount = parseInt([...document.querySelectorAll('.mo-page-info a[href*="--------"]')].pop()?.href?.match(/\/haosw\/\d+--------(\d+)---\.html/)?.[1] || '1');    
    return { 
        code: 1, 
        msg: "数据列表", 
        list: parseVideoList(), 
        page: parseInt(pg) || 1, 
        pagecount: pagecount, 
        limit: 40, 
        total: pagecount * 40
    };
}
async function detailContent(ids) {
    const res = Java.req(baseUrl + ids[0]);
    if (res.error) return Result.error('详情获取失败:' + res.error);
    const document = res.doc;
    return {
        code: 1,
        msg: "数据列表",
        list: parseDetailPage(document, ids[0]), 
        page: 1, 
        pagecount: 1,
        limit: 1, 
        total: 1
    };
}
async function searchContent(key, quick, pg) {
    const searchUrl = `${baseUrl}/haosc/${key}----------${pg || 1}---.html`;
    const captcha = Java.getSearchCode();
    
    if (captcha && captcha.success) {
        console.log('获取到的cookie:', captcha.cookie);    
        const verifyRes = await Java.req(`${baseUrl}/index.php/ajax/verify_check?type=search&verify=${captcha.code}`, {
            headers: { "Cookie": captcha.cookie }
        });
        console.log('验证码校验结果:', verifyRes.body);        
    }
    
    const res = await Java.req(searchUrl, {
        headers: captcha?.cookie ? { "Cookie": captcha.cookie } : {}
    });
    if (res?.doc?.querySelector('.mx-mac_msg_jump') || 
        res?.doc?.title?.includes("系统安全验证") ||
        res?.doc?.querySelector('.mac_verify_img')) {
        return {
            SearchCode: true,
            site: '清风影视',
            autoOcr: true,
            url: `${baseUrl}/index.php/verify/index.html?${Date.now()}`
        };
    }    
    const vods = [];
    res?.doc?.querySelectorAll('.mo-deta-info.mo-cols-rows').forEach(item => {
        const picEl = item.querySelector('a.mo-situ-pics');
        vods.push({
            vod_id: picEl?.getAttribute('href') || '',
            vod_name: item.querySelector('h1 a')?.textContent?.trim() || '',
            vod_pic: picEl?.getAttribute('data-original') || '',
            vod_remarks: item.querySelector('span.mo-situ-rema')?.textContent?.trim() || ''
        });
    });    
    const total = parseInt(res?.doc?.querySelector('#mo-page-sums')?.textContent || '0');
    const currentPage = parseInt(res?.doc?.querySelector('#mo-page-this')?.textContent || pg || '1');
    const pageText = [...res?.doc?.querySelectorAll('.mo-page-info .mo-part-bans.mo-back-disad')]
        .map(el => el.textContent).find(t => t.includes('/'));
    const pagecount = parseInt(pageText?.match(/\/(\d+)/)?.[1] || '1');    
    return {
        code: 1,
        msg: "数据列表",
        list: vods,
        page: currentPage,
        pagecount: pagecount,
        limit: 16,
        total: total
    };
}
async function playerContent(flag, id, vipFlags) {
   console.log("播放内容:", flag, id);
   return {
       type: 'sniff',
       url: `${baseUrl}${id}`,
       keyword: '.m3u8|.mp4|.flv',
       script: `try{document.querySelector("#playleft iframe").contentWindow.document.querySelector("#start").click();}catch(e){}`
   };
}
async function action(actionStr) {
    try {
        const params = JSON.parse(actionStr);
        console.log("action params:", params);
    } catch (e) {
        console.log("action is not JSON, treat as string");
    }
    return;
}
function parseVideoList() {
    const vods = [];
    document.querySelectorAll('li.mo-cols-lg2').forEach(item => {
        const picEl = item.querySelector('a.mo-situ-pics');
        const style = picEl?.getAttribute('style') || '';
        const picMatch = style.match(/url\(["']?(.*?)["']?\)/);        
        vods.push({
            vod_id: picEl?.getAttribute('href') || '',
            vod_name: item.querySelector('a.mo-situ-name')?.textContent?.trim() || '',
            vod_pic: picMatch?.[1] || '',
            vod_remarks: item.querySelector('span.mo-situ-rema')?.textContent?.trim() || ''
        });
    });
    return vods;
}
function parseDetailPage(document, vid) {
    const findInfo = label => [...document.querySelectorAll('li')].find(li => li.textContent.includes(label));   
    const picEl = document.querySelector('a.mo-situ-pics');
    const vod_pic = picEl?.getAttribute('data-original') || '';
    const actorEl = findInfo('主演:');
    const directorEl = findInfo('导演:');
    const typeEl = findInfo('分类:');
    const areaEl = findInfo('地区:');
    const yearEl = findInfo('年份:');
    const descEl = findInfo('简介:');
    const playFrom = [...document.querySelectorAll('.mo-sort-head .mo-movs-btns')].map(s => s.textContent.trim()).filter(Boolean).join('$$$');
    const playLists = document.querySelectorAll('.mo-sort-boxs.mo-movs-item');
    const playUrls = [...playLists].map(list => {
        const eps = [...list.querySelectorAll('li a')].map(a => {
            const name = a.textContent.trim();
            const url = a.getAttribute('href');
            return name && url ? `${name}$${url}` : null;
        }).filter(Boolean);
        return eps.join('#');
    }).join('$$$');    
    return [{
        vod_id: vid,
        vod_name: document.querySelector('h1 a')?.textContent?.trim() || '',
        vod_pic: vod_pic,
        vod_remarks: document.querySelector('span.mo-situ-rema')?.textContent?.trim() || '',
        vod_year: yearEl?.querySelector('a')?.textContent?.trim() || '',
        vod_director: [...directorEl?.querySelectorAll('a') || []].map(a => a.textContent.trim()).filter(Boolean).join('/'),
        vod_actor: [...actorEl?.querySelectorAll('a') || []].map(a => a.textContent.trim()).filter(Boolean).join('/'),
        vod_content: descEl?.textContent?.replace('简介:', '').trim() || '',
        type_name: typeEl?.querySelector('a')?.textContent?.trim() || '',
        vod_area: [...areaEl?.querySelectorAll('a') || []].map(a => a.textContent.trim()).filter(Boolean).join('/'),
        vod_play_from: playFrom,
        vod_play_url: playUrls
    }];
}
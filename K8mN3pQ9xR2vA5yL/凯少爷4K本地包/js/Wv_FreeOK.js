const baseUrl = 'https://www.freeok.red';
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
            { type_id: "4", type_name: "动漫" }
        ],
        filters: {
            "1": [
                { key: "class", name: "剧情", value: [ {n:"全部",v:""}, {n:"喜剧",v:"喜剧"}, {n:"爱情",v:"爱情"}, {n:"恐怖",v:"恐怖"}, {n:"动作",v:"动作"}, {n:"科幻",v:"科幻"}, {n:"剧情",v:"剧情"}, {n:"战争",v:"战争"}, {n:"警匪",v:"警匪"}, {n:"犯罪",v:"犯罪"}, {n:"动画",v:"动画"}, {n:"奇幻",v:"奇幻"}, {n:"武侠",v:"武侠"}, {n:"冒险",v:"冒险"}, {n:"枪战",v:"枪战"}, {n:"悬疑",v:"悬疑"}, {n:"惊悚",v:"惊悚"}, {n:"经典",v:"经典"}, {n:"青春",v:"青春"}, {n:"文艺",v:"文艺"}, {n:"微电影",v:"微电影"}, {n:"古装",v:"古装"}, {n:"历史",v:"历史"}, {n:"运动",v:"运动"}, {n:"农村",v:"农村"}, {n:"儿童",v:"儿童"}, {n:"网络电影",v:"网络电影"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"大陆",v:"大陆"}, {n:"香港",v:"香港"}, {n:"台湾",v:"台湾"}, {n:"美国",v:"美国"}, {n:"法国",v:"法国"}, {n:"英国",v:"英国"}, {n:"日本",v:"日本"}, {n:"韩国",v:"韩国"}, {n:"德国",v:"德国"}, {n:"泰国",v:"泰国"}, {n:"印度",v:"印度"}, {n:"意大利",v:"意大利"}, {n:"西班牙",v:"西班牙"}, {n:"加拿大",v:"加拿大"}, {n:"其他",v:"其他"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"法语",v:"法语"}, {n:"德语",v:"德语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "2": [
                { key: "class", name: "剧情", value: [ {n:"全部",v:""}, {n:"古装",v:"古装"}, {n:"战争",v:"战争"}, {n:"青春偶像",v:"青春偶像"}, {n:"喜剧",v:"喜剧"}, {n:"家庭",v:"家庭"}, {n:"犯罪",v:"犯罪"}, {n:"动作",v:"动作"}, {n:"奇幻",v:"奇幻"}, {n:"剧情",v:"剧情"}, {n:"历史",v:"历史"}, {n:"经典",v:"经典"}, {n:"乡村",v:"乡村"}, {n:"情景",v:"情景"}, {n:"商战",v:"商战"}, {n:"网剧",v:"网剧"}, {n:"其他",v:"其他"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"内地",v:"内地"}, {n:"韩国",v:"韩国"}, {n:"香港",v:"香港"}, {n:"台湾",v:"台湾"}, {n:"日本",v:"日本"}, {n:"美国",v:"美国"}, {n:"泰国",v:"泰国"}, {n:"英国",v:"英国"}, {n:"新加坡",v:"新加坡"}, {n:"其他",v:"其他"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"}, {n:"2009",v:"2009"}, {n:"2008",v:"2008"}, {n:"2006",v:"2006"}, {n:"2005",v:"2005"}, {n:"2004",v:"2004"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "3": [
                { key: "class", name: "剧情", value: [ {n:"全部",v:""}, {n:"选秀",v:"选秀"}, {n:"情感",v:"情感"}, {n:"访谈",v:"访谈"}, {n:"播报",v:"播报"}, {n:"旅游",v:"旅游"}, {n:"音乐",v:"音乐"}, {n:"美食",v:"美食"}, {n:"纪实",v:"纪实"}, {n:"曲艺",v:"曲艺"}, {n:"生活",v:"生活"}, {n:"游戏互动",v:"游戏互动"}, {n:"财经",v:"财经"}, {n:"求职",v:"求职"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"内地",v:"内地"}, {n:"港台",v:"港台"}, {n:"日韩",v:"日韩"}, {n:"欧美",v:"欧美"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"}, {n:"2009",v:"2009"}, {n:"2008",v:"2008"}, {n:"2007",v:"2007"}, {n:"2006",v:"2006"}, {n:"2005",v:"2005"}, {n:"2004",v:"2004"} ] },
                { key: "letter", name: "字母", value: [ {n:"字母",v:""}, {n:"A",v:"A"}, {n:"B",v:"B"}, {n:"C",v:"C"}, {n:"D",v:"D"}, {n:"E",v:"E"}, {n:"F",v:"F"}, {n:"G",v:"G"}, {n:"H",v:"H"}, {n:"I",v:"I"}, {n:"J",v:"J"}, {n:"K",v:"K"}, {n:"L",v:"L"}, {n:"M",v:"M"}, {n:"N",v:"N"}, {n:"O",v:"O"}, {n:"P",v:"P"}, {n:"Q",v:"Q"}, {n:"R",v:"R"}, {n:"S",v:"S"}, {n:"T",v:"T"}, {n:"U",v:"U"}, {n:"V",v:"V"}, {n:"W",v:"W"}, {n:"X",v:"X"}, {n:"Y",v:"Y"}, {n:"Z",v:"Z"}, {n:"0-9",v:"0-9"} ] },
                { key: "by", name: "排序", value: [ {n:"时间排序",v:"time"}, {n:"人气排序",v:"hits"}, {n:"评分排序",v:"score"} ] }
            ],
            "4": [
                { key: "class", name: "剧情", value: [ {n:"全部",v:""}, {n:"情感",v:"情感"}, {n:"科幻",v:"科幻"}, {n:"热血",v:"热血"}, {n:"推理",v:"推理"}, {n:"搞笑",v:"搞笑"}, {n:"冒险",v:"冒险"}, {n:"萝莉",v:"萝莉"}, {n:"校园",v:"校园"}, {n:"动作",v:"动作"}, {n:"机战",v:"机战"}, {n:"运动",v:"运动"}, {n:"战争",v:"战争"}, {n:"少年",v:"少年"}, {n:"少女",v:"少女"}, {n:"社会",v:"社会"}, {n:"原创",v:"原创"}, {n:"亲子",v:"亲子"}, {n:"益智",v:"益智"}, {n:"励志",v:"励志"}, {n:"其他",v:"其他"} ] },
                { key: "area", name: "地区", value: [ {n:"全部",v:""}, {n:"国产",v:"国产"}, {n:"日本",v:"日本"}, {n:"欧美",v:"欧美"}, {n:"其他",v:"其他"} ] },
                { key: "lang", name: "语言", value: [ {n:"全部",v:""}, {n:"国语",v:"国语"}, {n:"英语",v:"英语"}, {n:"粤语",v:"粤语"}, {n:"闽南语",v:"闽南语"}, {n:"韩语",v:"韩语"}, {n:"日语",v:"日语"}, {n:"其它",v:"其它"} ] },
                { key: "year", name: "年份", value: [ {n:"全部",v:""}, {n:"2026",v:"2026"}, {n:"2025",v:"2025"}, {n:"2024",v:"2024"}, {n:"2023",v:"2023"}, {n:"2022",v:"2022"}, {n:"2021",v:"2021"}, {n:"2020",v:"2020"}, {n:"2019",v:"2019"}, {n:"2018",v:"2018"}, {n:"2017",v:"2017"}, {n:"2016",v:"2016"}, {n:"2015",v:"2015"}, {n:"2014",v:"2014"}, {n:"2013",v:"2013"}, {n:"2012",v:"2012"}, {n:"2011",v:"2011"}, {n:"2010",v:"2010"}, {n:"2009",v:"2009"}, {n:"2008",v:"2008"}, {n:"2007",v:"2007"}, {n:"2006",v:"2006"}, {n:"2005",v:"2005"}, {n:"2004",v:"2004"} ] },
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
	const document = await Java.wvOpen(`${baseUrl}/vodshow/${extend?.type||tid}-${extend?.area}-${extend?.by}-${extend?.class}-${extend?.lang}-${extend?.letter}---${pg||1}---${extend?.year}.html`);	
    const pagecount = parseInt(document.querySelector('#page a[title="尾页"]')?.href?.match(/\/vodshow\/\d+--------(\d+)---.html/)?.[1] || '1');
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
    const searchUrl = `${baseUrl}/vodsearch/${key}----------${pg || 1}---.html`;
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
    if (res?.doc?.title?.includes("系统安全验证") || res?.doc?.querySelector('.mx-mac_msg_jump')) {
        return {
            SearchCode: true,
            site: 'FreeOK',
            autoOcr: true,
            url: `${baseUrl}/index.php/verify/index.html?${Date.now()}`
        };
    }
    const vods = [];
    res?.doc?.querySelectorAll('.module-card-item').forEach(item => {
        const link = item.querySelector('.module-card-item-title a');
        const img = item.querySelector('.module-item-pic img');
        const desc = item.querySelector('.module-info-item-content');
        vods.push({
            vod_id: link?.getAttribute('href') || '',
            vod_name: link?.textContent?.trim() || '',
            vod_pic: img?.getAttribute('data-original') || img?.getAttribute('src') || '',
            vod_remarks: desc?.textContent?.trim() || ''
        });
    });
    return {
        code: 1,
        msg: "数据列表",
        list: vods, 
        page: pg, 
        pagecount: parseInt(res?.doc?.querySelector("#page > a:nth-child(9)")?.href?.match(/\/vodshow\/\d+--------(\d+)---.html/)?.[1] || '1'),
        limit: 16, 
        total: parseInt(res?.doc?.querySelector("strong.mac_total")?.textContent || '0')
    };
}
async function playerContent(flag, id, vipFlags) {
    return { url: `${baseUrl}${id}`, parse: 1 };
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
    document.querySelectorAll('a.module-poster-item').forEach(item => {
        vods.push({
            vod_id: item.getAttribute('href') || '',
            vod_name: item.getAttribute('title') || '',
            vod_pic: item.querySelector('img')?.getAttribute('data-original') || '',
            vod_remarks: item.querySelector('.module-item-note')?.textContent?.trim() || ''
        });
    });
    return vods;
}
function parseDetailPage(document, vid) {
    const text = s => document.querySelector(s)?.textContent?.trim() || '';
    const attr = (s, a) => document.querySelector(s)?.getAttribute(a) || '';
    const findInfo = label => [...document.querySelectorAll('.module-info-item')].find(el => el.textContent.includes(label));
    const tagLinks = document.querySelectorAll('.module-info-tag-link');
    const vod_year = tagLinks[0]?.querySelector('a')?.getAttribute('title') || '';
    const vod_area = tagLinks[1]?.querySelector('a')?.getAttribute('title') || '';
    const typeLinks = tagLinks[2]?.querySelectorAll('a') || [];
    const type_name = [...typeLinks].map(a => a.textContent.trim()).filter(Boolean).join('/');    
    const playUrls = [];
    document.querySelectorAll('.his-tab-list').forEach(list => {
        const eps = [...list.querySelectorAll('.module-play-list-link')].map(link => {
            const name = link.querySelector('span')?.textContent?.trim();
            const url = link.getAttribute('href');
            return name && url ? `${name}$${url}` : null;
        }).filter(Boolean);
        if (eps.length) playUrls.push(eps.join('#'));
    });
    const playFrom = [...document.querySelectorAll('.module-tab-item span')]
        .map(s => s.textContent.trim())
        .filter(Boolean)
        .join('$$$');    
    let vod_director = '';
    const directorEl = findInfo('导演');
    if (directorEl) {
        vod_director = [...directorEl.querySelectorAll('a')].map(a => a.textContent.trim()).join('/');
    }    
    let vod_actor = '';
    const actorEl = findInfo('主演');
    if (actorEl) {
        vod_actor = [...actorEl.querySelectorAll('a')].map(a => a.textContent.trim()).join('/');
    }   
    return [{
        vod_id: vid,
        vod_name: text('.module-info-heading h1'),
        vod_pic: attr('.module-info-poster img', 'data-original') || attr('.module-info-poster img', 'src'),
        vod_remarks: findInfo('集数')?.querySelector('.module-info-item-content')?.textContent?.trim() || findInfo('更新')?.querySelector('.module-info-item-content')?.textContent?.trim() || '',
        vod_year: vod_year,
        vod_director: vod_director,
        vod_actor: vod_actor,
        vod_content: text('.module-info-introduction-content p'),
        type_name: type_name,
        vod_area: vod_area,
        vod_play_from: playFrom,
        vod_play_url: playUrls.join('$$$')
    }];
}

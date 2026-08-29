let host = 'https://www.nkdvd.cc';
let headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 13; M2102J2SC Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/144.0.7559.31 Mobile Safari/537.36'
};

async function init(cfg) {}

function getList(html) {
    let videos = [];
    let selector = '';
    if (html.includes('class="module-items')) selector = '.module-item';
    if (!selector) return videos;
    const items = pdfa(html, selector);
    items.forEach(it => {
        let idMatch = it.match(/href="([\s\S]*?)"/);
        let nameMatch = it.match(/title="([\s\S]*?)"/) || it.match(/alt="([\s\S]*?)"/);
        let picMatch = it.match(/data-src="([\s\S]*?)"/) || it.match(/data-original="([\s\S]*?)"/) || it.match(/src="([\s\S]*?)"/);
        let remarksMatch = it.match(/class="pic-text[\s\S]*?text-right">([\s\S]*?)</) || it.match(/video-info-header">[\s\S]*?">([\s\S]*?)</) || it.match(/module-item-text">([\s\S]*?)</) || it.match(/v_note">([\s\S]*?)<\/div/) || it.match(/v-ins"><p>([\s\S]*?)<\/p>/) || it.match(/module-item-note">([\s\S]*?)</) || it.match(/class="[\s\S]*?remarks"([\s\S]*?)</) || it.match(/v-item-bottom">([\s\S]*?)<\/span>/) || it.match(/class="pic_text[\s\S]*?">([\s\S]*?)</) || it.match(/<span class="qb">([\s\S]*?)<\/span>/) || it.match(/ft2">([\s\S]*?)<\/span>/);
        if (idMatch && nameMatch) {
            let pic = picMatch ? (picMatch[1] || picMatch[2]) : "";
            videos.push({
                vod_id: idMatch[1],
                vod_name: nameMatch[1].trim() || "未知片名",
                vod_pic: (pic && pic !== '') ? (pic.startsWith('/') ? host + pic : pic) : 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
                vod_remarks: remarksMatch?.[1]?.trim() || "未知备注"
            });
        }
    });
    return videos;
}

async function home(filter) {
    return JSON.stringify({
            class: [{"type_id": "20","type_name": "电影"},{"type_id": "21","type_name": "剧集"},{"type_id": "22","type_name": "动漫"},{"type_id": "23","type_name": "综艺"},{"type_id": "24","type_name": "纪录片"},{"type_id": "25","type_name": "爽剧"}],filters: {"20":[{"key":"cateId","name":"类型","value":[{"n":"全部","v":"20"},{"n":"动作片","v":"26"},{"n":"喜剧片","v":"27"},{"n":"爱情片","v":"28"},{"n":"科幻片","v":"29"},{"n":"恐怖片","v":"30"},{"n":"剧情片","v":"31"},{"n":"战争片","v":"32"},{"n":"动画片","v":"33"}]},{"key":"class_","name":"剧情","value":[{"n":"全部","v":""},{"n":"Netflix","v":"Netflix"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"犯罪","v":"犯罪"},{"n":"动画","v":"动画"},{"n":"奇幻","v":"奇幻"},{"n":"武侠","v":"武侠"},{"n":"冒险","v":"冒险"},{"n":"枪战","v":"枪战"},{"n":"恐怖","v":"恐怖"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"家庭","v":"家庭"},{"n":"同性","v":"同性"},{"n":"运动","v":"运动"},{"n":"儿童","v":"儿童"},{"n":"经典","v":"经典"},{"n":"青春","v":"青春"},{"n":"文艺","v":"文艺"},{"n":"微电影","v":"微电影"},{"n":"纪录片","v":"纪录片"},{"n":"网络电影","v":"网络电影"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":""},{"n":"中国大陆","v":"中国大陆"},{"n":"美国","v":"美国"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"},{"n":"泰国","v":"泰国"},{"n":"中国香港","v":"中国香港"},{"n":"中国台湾","v":"中国台湾"},{"n":"新加坡","v":"新加坡"},{"n":"马来西亚","v":"马来西亚"},{"n":"印度","v":"印度"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"德国","v":"德国"},{"n":"加拿大","v":"加拿大"},{"n":"西班牙","v":"西班牙"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"其它","v":"其它"}]},{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"汉语普通话","v":"汉语普通话"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"}]},{"key":"letter","name":"字母","value":[{"n":"全部","v":""},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],"21":[{"key":"cateId","name":"类型","value":[{"n":"全部","v":"21"},{"n":"国产剧","v":"34"},{"n":"港台剧","v":"35"},{"n":"日韩剧","v":"36"},{"n":"欧美剧","v":"37"},{"n":"泰国剧","v":"38"}]},{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"Netflix","v":"Netflix"},{"n":"爱情","v":"爱情"},{"n":"言情","v":"言情"},{"n":"都市","v":"都市"},{"n":"家庭","v":"家庭"},{"n":"战争","v":"战争"},{"n":"喜剧","v":"喜剧"},{"n":"古装","v":"古装"},{"n":"武侠","v":"武侠"},{"n":"偶像","v":"偶像"},{"n":"历史","v":"历史"},{"n":"悬疑","v":"悬疑"},{"n":"科幻","v":"科幻"},{"n":"冒险","v":"冒险"},{"n":"惊悚","v":"惊悚"},{"n":"犯罪","v":"犯罪"},{"n":"运动","v":"运动"},{"n":"恐怖","v":"恐怖"},{"n":"剧情","v":"剧情"},{"n":"奇幻","v":"奇幻"},{"n":"纪录片","v":"纪录片"},{"n":"灾难","v":"灾难"},{"n":"动作","v":"动作"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":"全部"},{"n":"中国大陆","v":"中国大陆"},{"n":"美国","v":"美国"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"},{"n":"泰国","v":"泰国"},{"n":"中国香港","v":"中国香港"},{"n":"中国台湾","v":"中国台湾"},{"n":"新加坡","v":"新加坡"},{"n":"马来西亚","v":"马来西亚"},{"n":"印度","v":"印度"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"德国","v":"德国"},{"n":"加拿大","v":"加拿大"},{"n":"西班牙","v":"西班牙"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"}]},{"key":"letter","name":"字母","value":[{"n":"全部","v":""},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],"22":[{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"Netflix","v":"Netflix"},{"n":"奇幻","v":"奇幻"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"喜剧","v":"喜剧"},{"n":"冒险","v":"冒险"},{"n":"后宫","v":"后宫"},{"n":"爱情","v":"爱情"},{"n":"悬疑","v":"悬疑"},{"n":"机战","v":"机战"},{"n":"战争","v":"战争"},{"n":"其他","v":"其他"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":"全部"},{"n":"中国大陆","v":"中国大陆"},{"n":"日本","v":"日本"},{"n":"美国","v":"美国"},{"n":"韩国","v":"韩国"},{"n":"中国香港","v":"中国香港"},{"n":"中国台湾","v":"中国台湾"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"加拿大","v":"加拿大"},{"n":"西班牙","v":"西班牙"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"}]},{"key":"letter","name":"字母","value":[{"n":"全部","v":""},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],"23":[{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"Netflix","v":"Netflix"},{"n":"真人秀","v":"真人秀"},{"n":"音乐","v":"音乐"},{"n":"喜剧","v":"喜剧"},{"n":"脱口秀","v":"脱口秀"},{"n":"文化","v":"文化"},{"n":"美食","v":"美食"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":"全部"},{"n":"美国","v":"美国"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"},{"n":"中国香港","v":"中国香港"},{"n":"中国台湾","v":"中国台湾"},{"n":"印度","v":"印度"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"德国","v":"德国"},{"n":"加拿大","v":"加拿大"},{"n":"西班牙","v":"西班牙"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"}]},{"key":"letter","name":"字母","value":[{"n":"全部","v":""},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],"24":[{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"Netflix","v":"Netflix"},{"n":"真人秀","v":"真人秀"},{"n":"音乐","v":"音乐"},{"n":"喜剧","v":"喜剧"},{"n":"脱口秀","v":"脱口秀"},{"n":"文化","v":"文化"},{"n":"美食","v":"美食"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":"全部"},{"n":"中国大陆","v":"中国大陆"},{"n":"美国","v":"美国"},{"n":"韩国","v":"韩国"},{"n":"日本","v":"日本"},{"n":"中国香港","v":"中国香港"},{"n":"中国台湾","v":"中国台湾"},{"n":"印度","v":"印度"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"德国","v":"德国"},{"n":"加拿大","v":"加拿大"},{"n":"西班牙","v":"西班牙"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"}]},{"key":"letter","name":"字母","value":[{"n":"全部","v":""},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],"25":[{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"}]},{"key":"letter","name":"字母","value":[{"n":"全部","v":""},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}]}});}

async function homeVod() {
    let resp = await req(host, {
        headers
    });
    return JSON.stringify({
        list: getList(resp.content)
    });
}

async function category(tid, pg, filter, extend) {
  const p = pg || 1;
  const seg = [`/id/${extend.cateId || tid}`, `/page/${p}.html`];
  if (extend.area)   seg.unshift(`/area/${extend.area}`);
  if (extend.by)     seg.unshift(`/by/${extend.by}`);
  if (extend.class_)  seg.unshift(`/class/${extend.class_}`);
  if (extend.lang)   seg.unshift(`/lang/${extend.lang}`);
  if (extend.letter) seg.unshift(`/letter/${extend.letter}`);
  if (extend.year)   seg.unshift(`/year/${extend.year}`); 
  const url = host + '/vodshow' + seg.join('');
  const resp = await req(url, { headers });
  return JSON.stringify({
    list: getList(resp.content),
    page: parseInt(p)
  });
}

async function detail(id) {
    const url = host + id;
    const resp = await req(url, {
        headers
    });
    const html = resp.content;
    const blockList = ["自建.C","自建.Z","JL超清"];
    const tabs = pdfa(html, '.module-tab-item');
    const lists = pdfa(html, '.module-play-list');
    const playPairs = tabs.map((tab, idx) => {
        const name = (tab.match(/<span>([\s\S]*?)<\/span>/) || ['', '未知线路'])[1].trim();
        const urlArr = pdfa(lists[idx] || '', 'a').map(a => {
            const n = (a.match(/<span>([\s\S]*?)<\/span>/) || ['', '未知播放'])[1];
            const v = a.match(/href="([\s\S]*?)"/);
            return n + '$' + (v ? v[1] : '');
        }).join('#');
        return {
            name,
            url: urlArr
        };
    }).filter(item => !blockList.includes(item.name));
    const playFrom = playPairs.map(p => p.name).join('$$$');
    const playUrl = playPairs.map(p => p.url).join('$$$');
    return JSON.stringify({
        list: [{
            vod_id: id,
            vod_name: (html.match(/<h1>([\s\S]*?)<\/h1>/) || ['', ''])[1],
            vod_pic: (html.match(/data-original="([\s\S]*?)"/) || ["", ""])[1],
            vod_year: (html.match(/year\/[\s\S]*?.html">([\s\S]*?)<\/a>/) || ['', ''])[1],
            vod_area: (html.match(/area\/[\s\S]*?">([\s\S]*?)<\/a>/) || ['', ''])[1],
            vod_remarks: (html.match(/备注：<\/span>[\s\S]*?<div class="module-info-item-content">([\s\S]*?)<\/div>/) || ['', ''])[1] + "|" + "更新：" + (html.match(/更新：<\/span>[\s\S]*?<div class="module-info-item-content">([\s\S]*?)<\/div>/) || ['', ''])[1],
            type_name: (() => {
                const links = html.match(/<div class="module-info-tag-link"[^>]*>[\s\S]*?<\/div>/g) || [];
                for (let div of links) {
                    if (/<span[^>]*class="[^"]*slash[^"]*"[^>]*>\s*\/\s*<\/span>/.test(div)) {
                        return Array.from(div.matchAll(/<a [^>]*>([^<]+)<\/a>/g)).map(m => m[1].trim()).join(' / ');
                    }
                }
                return '';
            })() || '',
            vod_actor: Array.from(
                html.match(/主演：<\/span>([\s\S]*?)<\/div>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []
            ).map(m => m[1]).join(' / ') || '',
            vod_director: Array.from(
                html.match(/导演：<\/span>([\s\S]*?)<\/div>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []
            ).map(m => m[1]).join(' / ') || '',
            vod_content: (html.match(/<p>([\s\S]*?)<\/p>/) || ['', ''])[1].replace(/<.*?>/g, ''),
            vod_play_from: playFrom,
            vod_play_url: playUrl
        }]
    });
}

async function search(wd, quick, pg) {
    let p = pg || 1;
    let url = `${host}/vodsearch.html?wd=${wd}`;
    let resp = await req(url, {
        headers
    });
    return JSON.stringify({
        list: getList(resp.content)
    });
}
async function play(flag, id, flags) {
    try {
        let playUrl = !/^http/.test(id) ? `${host}${id}` : id;
        let resHtml = (await req(playUrl, {
            headers
        })).content;
        let kcode = safeParseJSON(
            resHtml.match(/var\s+player_\w+\s*=\s*(\{[^]*?\})\s*</)?.[1] ?? ''
        );
        let kurl = kcode?.url ?? '';
        let kp = /m3u8|mp4|mkv/i.test(kurl) ? 0 : 1;
        if (kp) kurl = playUrl;
        return JSON.stringify({
            jx: 0,
            parse: kp,
            url: kurl,
            header: headers
        });
    } catch (e) {
        return JSON.stringify({
            jx: 0,
            parse: 0,
            url: '',
            header: {}
        });
    }
}

function safeParseJSON(str) {
    try {
        return JSON.parse(str.trim().replace(/;+$/, ''));
    } catch {
        return null;
    }
}

export default {
    init,
    home,
    homeVod,
    category,
    detail,
    search,
    play
};
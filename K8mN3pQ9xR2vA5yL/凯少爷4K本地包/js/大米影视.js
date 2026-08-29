let host = 'https://www.dmdh.cc';

let headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; M2102J2SC Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.3 Mobile Safari/537.36"
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
        let remarksMatch = it.match(/class="module-item-text">([\s\S]*?)</) || it.match(/module-item-caption">[\s\S]*?">([\s\S]*?)</) || it.match(/module-item-text">([\s\S]*?)</) || it.match(/v_note">([\s\S]*?)<\/div/) || it.match(/v-ins"><p>([\s\S]*?)<\/p>/) || it.match(/module-item-note">([\s\S]*?)</) || it.match(/class="[\s\S]*?remarks"([\s\S]*?)</) || it.match(/v-item-bottom">([\s\S]*?)<\/span>/) || it.match(/class="pic_text[\s\S]*?">([\s\S]*?)</) || it.match(/<span class="qb">([\s\S]*?)<\/span>/) || it.match(/ft2">([\s\S]*?)<\/span>/);
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
       class: [
	        {"type_id": "1","type_name": "电影"},
			{"type_id": "2","type_name": "剧集"},
			{"type_id": "3","type_name": "综艺"},
			{"type_id": "4","type_name": "动漫"}],
			
   filters: {
	   "1":[
	        {"key":"cateId","name":"类型","value":[{"n":"全部","v":"1"},{"n":"动作片","v":"6"},{"n":"喜剧片","v":"7"},{"n":"爱情片","v":"8"},{"n":"科幻片","v":"9"},{"n":"恐怖片","v":"10"},{"n":"剧情片","v":"11"},{"n":"战争片","v":"12"}]},
            {"key":"class_","name":"剧情","value":[{"n":"全部","v":""},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"警匪","v":"警匪"},{"n":"犯罪","v":"犯罪"},{"n":"动画","v":"动画"},{"n":"奇幻","v":"奇幻"},{"n":"武侠","v":"武侠"},{"n":"冒险","v":"冒险"},{"n":"枪战","v":"枪战"},{"n":"恐怖","v":"恐怖"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"经典","v":"经典"},{"n":"青春","v":"青春"},{"n":"文艺","v":"文艺"},{"n":"微电影","v":"微电影"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"运动","v":"运动"},{"n":"农村","v":"农村"},{"n":"儿童","v":"儿童"},{"n":"网络电影","v":"网络电影"}]},
			{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"法语","v":"法语"},{"n":"德语","v":"德语"},{"n":"其它","v":"其它"}]},
	        {"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"}]},
			{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],
			
	   "2":[
	   	    {"key":"cateId","name":"类型","value":[{"n":"全部","v":"2"},{"n":"国产剧","v":"13"},{"n":"港台剧","v":"14"},{"n":"日韩剧","v":"15"},{"n":"欧美剧","v":"16"}]},
			{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"爱情","v":"爱情"},{"n":"古装","v":"古装"},{"n":"战争","v":"战争"},{"n":"青春偶像","v":"青春偶像"},{"n":"喜剧","v":"喜剧"},{"n":"家庭","v":"家庭"},{"n":"犯罪","v":"犯罪"},{"n":"动作","v":"动作"},{"n":"奇幻","v":"奇幻"},{"n":"剧情","v":"剧情"},{"n":"历史","v":"历史"},{"n":"经典","v":"经典"},{"n":"乡村","v":"乡村"},{"n":"情景","v":"情景"},{"n":"商战","v":"商战"},{"n":"网剧","v":"网剧"},{"n":"其他","v":"其他"}]},
			{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},
	        {"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"}]},
			{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],
		
	   "3":[
	   		{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"选秀","v":"选秀"},{"n":"情感","v":"情感"},{"n":"音乐","v":"音乐"},{"n":"访谈","v":"访谈"},{"n":"播报","v":"播报"},{"n":"旅游","v":"旅游"},{"n":"音乐","v":"音乐"},{"n":"美食","v":"美食"},{"n":"曲艺","v":"曲艺"},{"n":"纪实","v":"纪实"},{"n":"游戏互动","v":"游戏互动"},{"n":"财经","v":"财经"},{"n":"求职","v":"求职"}]},
			{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"法语","v":"法语"},{"n":"德语","v":"德语"},{"n":"其它","v":"其它"}]},
	        {"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"}]},
			{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}],
		
	   "4":[
	   	   	{"key":"class_","name":"剧情","value":[{"n":"全部","v":"全部"},{"n":"情感","v":"情感"},{"n":"科幻","v":"科幻"},{"n":"热血","v":"热血"},{"n":"搞笑","v":"搞笑"},{"n":"冒险","v":"冒险"},{"n":"萝莉","v":"萝莉"},{"n":"校园","v":"校园"},{"n":"动作","v":"动作"},{"n":"机战","v":"机战"},{"n":"运动","v":"运动"},{"n":"战争","v":"战争"},{"n":"少年","v":"少年"},{"n":"少女","v":"少女"},{"n":"社会","v":"社会"},{"n":"原创","v":"原创"},{"n":"亲子","v":"亲子"},{"n":"益智","v":"益智"},{"n":"励志","v":"励志"},{"n":"其他","v":"其他"}]},
			{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"法语","v":"法语"},{"n":"德语","v":"德语"},{"n":"其它","v":"其它"}]},
	        {"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2026","v":"2026"},{"n":"2025","v":"2025"},{"n":"2024","v":"2024"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"}]},
			{"key":"by","name":"排序","value":[{"n":"时间","v":"time"},{"n":"人气","v":"hits"},{"n":"评分","v":"score"}]}]
							
}});}

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
  const seg = [`${extend.cateId || tid}`, `${p}.html`];
  if (extend.area)   seg.unshift(`${extend.area}`);
  if (extend.by)     seg.unshift(`${extend.by}`);
  if (extend.class_)  seg.unshift(`${extend.class_}`);
  if (extend.lang)   seg.unshift(`${extend.lang}`);
  if (extend.year)   seg.unshift(`${extend.year}`); 
  const url = `${host}/vodshow/${extend?.cateId || tid}--${extend?.by ?? ''}-${extend?.class ?? ''}-${extend?.lang ?? ''}----${pg}---${extend?.year ?? ''}.html`;
  const resp = await req(url, { headers });
  return JSON.stringify({
    list: getList(resp.content),
    page: parseInt(p)
  });
}

async function detail(id) {
    let url = host + id;
    let resp = await req(url, { headers });
    let html = resp.content; 
	
    const blockList = ["","",""];
    const tabs = pdfa(html, '.module-tab-item');
    const lists = pdfa(html, '.module-blocklist');
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
            vod_name: (html.match(/<h1 class="page-title">(.*?)<\/h1>/) || ["", ""])[1],
            vod_pic: (html.match(/data-src="(.*?)"/) || ["", ""])[1],
            vod_year: (html.match(/<a class="tag-link" href="\/vodshow\/.*?-----------.*?.html">(.*?)<\/a>/) || ["", ""])[1],
            vod_area: (html.match(/<a class="tag-link" href="\/vodshow\/.*?-.*?----------.html">(.*?)<\/a>/) || ["", ""])[1],
            vod_remarks: (html.match(/集数：<\/span><div class="video-info-item">([\s\S]*?)<\/div>/) || ["", ""])[1],
            type_name: (html.match(/<a href="\/vodshow\/.*?---.*?--------.html">([\s\S]*?)<\/a>/) || ["", ""])[1],
            vod_actor: Array.from(
            html.match(/主演：<\/span>([\s\S]*?)<\/div>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            vod_director: Array.from(
            html.match(/导演：<\/span>([\s\S]*?)<\/div>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            vod_content: "秦时明月汉时关,万里长征人未还。但使龙城飞将在,不教胡马度阴山。" + (html.match(/剧情：<\/span>"([\s\S]*?)"<\/div>/) || ["", ""])[1].replace(/<.*?>/g, ""),
            vod_play_from: playFrom,
            vod_play_url: playUrl
        }]
    });
}
async function search(wd, quick, pg) {
    let p = pg || 1;
    let url = host + "/vodsearch/" + "-------------.html?wd=" + encodeURIComponent(wd);
    let resp = await req(url, { headers });
    return JSON.stringify({ list: getList(resp.content) });
}
async function play(flag, id, flags) {
    let url = host + id;
    let resp = await req(url, { headers });
    let m3u8 = resp.content.match(/"url":"([^"]+\.m3u8)"/);
    if (m3u8) {
        return JSON.stringify({
            parse: 0,
            url: m3u8[1].replace(/\\/g, ""),
            header: headers
        });
    }
    let jump = resp.content.match(/(?:iframe|video)\s+[^>]*\bsrc\s*=\s*["']([^"']+\.m3u8(?:\?[^"']*)?)["']/i) ||
               resp.content.match(/location\.href\s*=\s*["']([^"']+\.m3u8(?:\?[^"']*)?)["']/i);
    if (jump) {
        let realUrl = jump[1].startsWith("http") ? jump[1] : host + jump[1];
        return JSON.stringify({
            parse: 0,
            url: realUrl,
            header: headers
        });
    }
    return JSON.stringify({
        parse: 1,
        url: url,
        header: headers
    });
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

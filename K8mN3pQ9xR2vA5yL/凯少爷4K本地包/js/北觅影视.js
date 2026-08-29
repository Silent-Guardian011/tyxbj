//网站域名
let host = 'https://v.luttt.com';
//请求头(基本不用动)
let headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; M2102J2SC Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.3 Mobile Safari/537.36"
};
async function init(cfg) {}
function getList(html) {
    let videos = [];
    //数组
    let items = pdfa(html, ".hl-list-item");
    items.forEach(it => {
        //链接
        let idMatch = it.match(/\/voddetail\/(\d+).html/);
        //标题
        let nameMatch = it.match(/title="(.*?)"/) || it.match(/alt="(.*?)"/);
        //图片
        let picMatch = it.match(/data-original="(.*?)"/) || it.match(/src="(.*?)"/);
        //副标题
        let remarksMatch = it.match(/<span class="hl-lc-1 remarks">(.*?)<\/span>/);
        if (idMatch && nameMatch) {
            let pic = picMatch ? (picMatch[1] || picMatch[2]) : "";
            videos.push({
                vod_id: idMatch[1],
                vod_name: nameMatch[1].replace(/<.*?>/g, ""),
                vod_pic: pic.startsWith('/') ? host + pic : pic,
                vod_remarks: (remarksMatch || ["", ""])[1].replace(/<.*?>/g, "")
            });
        }
    });
    return videos;
}
async function home(filter) {
    return JSON.stringify({
        "class": [{"type_id": "1","type_name": "电影"},{"type_id": "2","type_name": "电视剧"},{"type_id": "3","type_name": "综艺"},{"type_id": "4","type_name": "动漫"}]});
}
async function homeVod() {
    let resp = await req(host, { headers });
    return JSON.stringify({ list: getList(resp.content) });
}
async function category(tid, pg, filter, extend) {
    let p = pg || 1;
    let targetId = (extend && extend.class) ? extend.class : tid;
    //分类url(根据网站自己拼接)
    let url = host + "/vodshow/" + targetId + "--------" + (parseInt(p) > 1 ? p + "---.html" : "1---.html");
    let resp = await req(url, { headers });
    return JSON.stringify({ list: getList(resp.content), page: parseInt(p) });
}
async function detail(id) {
    //二级链接拼接
    let url = host + '/voddetail/' + id + '.html';
    let resp = await req(url, { headers });
    let html = resp.content;
    //线路数组
    let playFrom = pdfa(html, ".hl-tabs-btn")
         //线路标题(基本不用动)
        .map(it => (it.match(/alt="(.*?)"/) || ["", "线路"])[1]).join('$$$');
    //播放数组
    let playUrl = pdfa(html, ".hl-plays-list").map(list =>    //播放列表(基本不用动)
        pdfa(list, "a").map(a => {
            //播放标题(基本不用动)
            let n = (a.match(/html">(.*?)<\/a>/) || ["", "展开全部"])[1];
            //播放链接(基本不用动)
            let v = a.match(/href="(.*?)"/);
            return n + '$' + (v ? v[1] : "");
        }).join('#')
    ).join('$$$');
    return JSON.stringify({
        list: [{
            vod_id: id,
            vod_name: (html.match(/<h2 class="hl-dc-title hl-data-menu">(.*?)<\/h2>/) || ["", ""])[1],
            vod_pic: (html.match(/data-original=(.*?)/) || ["", ""])[1],
            vod_year: (html.match(/年份：<\/em>([\s\S]*?)<\/li>/) || ["", ""])[1],
            vod_area: (html.match(/地区：<\/em>([\s\S]*?)<\/li>/) || ["", ""])[1],
            vod_remarks: (html.match(/更新：<\/em>([\s\S]*?)<\/li>/) || ["", ""])[1],
            type_name: (html.match(/<a href="\/vodsearch\/----.*?---------.html" target="_blank">(.*?)<\/a>/) || ["", ""])[1],
            vod_actor: Array.from(
                html.match(/主演：<\/em>([\s\S]*?)<\/li>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            vod_director: Array.from(
                html.match(/导演：<\/em>([\s\S]*?)<\/li>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            vod_content: (html.match(/简介：<\/em>([\s\S]*?)<\/li>/) || ["", ""])[1].replace(/<.*?>/g, ""),
            vod_play_from: playFrom,
            vod_play_url: playUrl
        }]
    });
}
async function search(wd, quick, pg) {
    let p = pg || 1;
    //搜索url(根据网站自己拼接)
    let url = host + "/vodsearch/" + "----------" + ".html?wd=" + encodeURIComponent(wd) + "&submit=";
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

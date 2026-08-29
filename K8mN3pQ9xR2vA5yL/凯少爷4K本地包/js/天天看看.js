let host = 'http://www.ruichengcorp.net';
let headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
};

async function init(cfg) {}

function getList(html) {
    const videos = [];
    if (html.includes('id="searchList"')) {
        const blocks = html.split(/<li[^>]*class="clearfix"[^>]*>/);
        blocks.shift();
        blocks.forEach(bl => {
            const idM = bl.match(/href="\/(dongman_\d+)\.html"/);
            const nameM = bl.match(/title="([^"]*)"/);
            const picM = bl.match(/data-original="([^"]*)"/);
            const noteM = bl.match(/<span[^>]*class="pic-text[^>]*>([^<]+)<\/span>/);
            if (idM && nameM) {
                videos.push({
                    vod_id: idM[1].replace('dongman_', ''),
                    vod_name: nameM[1],
                    vod_pic: picM ? picM[1] : '',
                    vod_remarks: '✨冉神甄选✨' + (noteM ? noteM[1].trim() : '')
                });
            }
        });
        return videos;
    }

    const items = pdfa(html, '.myui-vodlist li.col-xs-3');
    items.forEach(it => {
        const idM = it.match(/href="\/(dongman_\d+)\.html"/);
        const nameM = it.match(/title="([^"]*)"/);
        const picM = it.match(/data-original="([^"]*)"/);
        const noteM = it.match(/<span[^>]*class="pic-text[^>]*>([^<]+)<\/span>/);

        if (idM && nameM) {
            videos.push({
                vod_id: idM[1].replace('dongman_', ''),
                vod_name: nameM[1],
                vod_pic: picM ? picM[1] : '',
                vod_remarks: '✨冉神甄选✨' + (noteM ? noteM[1].trim() : '')
            });
        }
    });
    return videos;
}

async function home(filter) {
    return JSON.stringify({
        "class": [{
            "type_id": "1",
            "type_name": "电影"
        }, {
            "type_id": "2",
            "type_name": "连续剧"
        }, {
            "type_id": "3",
            "type_name": "综艺节目"
        }, {
            "type_id": "4",
            "type_name": "热播动漫"
        }, {
            "type_id": "6",
            "type_name": "动作片"
        }, {
            "type_id": "7",
            "type_name": "喜剧片"
        }, {
            "type_id": "8",
            "type_name": "爱情片"
        }, {
            "type_id": "9",
            "type_name": "科幻片"
        }, {
            "type_id": "10",
            "type_name": "恐怖片"
        }, {
            "type_id": "11",
            "type_name": "剧情片"
        }, {
            "type_id": "12",
            "type_name": "战争片"
        }, {
            "type_id": "13",
            "type_name": "电视剧"
        }, {
            "type_id": "14",
            "type_name": "港台剧"
        }, {
            "type_id": "15",
            "type_name": "日韩剧"
        }, {
            "type_id": "16",
            "type_name": "欧美剧"
        }, {
            "type_id": "20",
            "type_name": "泰国剧"
        }, {
            "type_id": "22",
            "type_name": "国产动漫"
        }, {
            "type_id": "23",
            "type_name": "欧美动漫"
        }, {
            "type_id": "21",
            "type_name": "日本动漫"
        }]
    });
}

async function homeVod() {
    let resp = await req(host, {
        headers: headers
    });
    return JSON.stringify({
        list: getList(resp.content)
    });
}

async function category(tid, pg, filter, extend) {
    let p = pg || 1;
    let targetId = (extend && extend.class) ? extend.class : tid;
    let url = host + "/vodshow/" + targetId + "--------" + (parseInt(p) > 1 ? p + "---.html" : "1---.html");

    let resp = await req(url, {
        headers
    });
    return JSON.stringify({
        list: getList(resp.content),
        page: parseInt(p)
    });
}

async function detail(id) {
    let url = host + '/dongman_' + id + '.html';
    let resp = await req(url, {
        headers: headers
    });
    let html = resp.content;

    let playFrom = pdfa(html, ".nav-tabs li").map(it => "✨冉神👉" + (it.match(/tab">(.*?)<\/a>/) || ["", "线路"])[1]).join('$$$');
    let playUrl = pdfa(html, ".myui-content__list").map(list =>
        pdfa(list, "a").map(a => {
            let n = "📽️冉神👉" + (a.match(/">(.*?)<\/a>/) || ["", "播放"])[1];
            let v = a.match(/href="\/anime_(.*?).html"/);
            return n + '$' + (v ? v[1] : "");
        }).join('#')
    ).join('$$$');

    return JSON.stringify({
        list: [{
            'vod_id': id,
            'vod_name': (html.match(/<title>(.*?)-.*?<\/title>/) || ["", ""])[1],
            'vod_pic': (html.match(/data-original="(.*?)"/) || ["", ""])[1],
            'vod_year': (html.match(/<a href="\/vodsearch\/-------------(.*?).html" target="_blank">(.*?)<\/a>/) || ["", ""])[1],
            'vod_area': (html.match(/<a href="\/vodsearch\/--.*?-----------.html" target="_blank">(.*?)<\/a>/) || ["", ""])[1],
            'type_name': (html.match(/<a href="\/vodsearch\/----.*?---------.html"[\s\S]*?>(.*?)<\/a>/) || ["", ""])[1].trim(),
            'vod_remarks': (html.match(/<span class="text-muted">更新时间:<\/span>([\s\S]*?)<\/p>/) || ["", ""])[1].trim(),
            'vod_actor': Array.from(
                html.match(/<span class="text-muted">主演：<\/span>([\s\S]*?)<\/p>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            'vod_director': Array.from(
                html.match(/<span class="text-muted">导演：<\/span>([\s\S]*?)<\/p>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            'vod_content': "😸冉神🎉为你介绍剧情📢本资源来源于网络🚓侵权请联系删除👉" + (html.match(/剧情简介[\s\S]*?<\/strong>[\s\S]*?。([\s\S]*?)<\/div>/) || ["", ""])[1].replace(/<.*?>/g, "").replace("特别提醒如果您对影片有自己的看法请留言弹幕评论。", ""),
            'vod_play_from': playFrom,
            'vod_play_url': playUrl
        }]
    });
}

async function search(wd, quick, pg) {
    let p = pg || 1;
    let url = host + "/vodsearch/" + encodeURIComponent(wd) + "----------" + (parseInt(p) > 1 ? parseInt(p) + "---.html" : "1---.html");
    let resp = await req(url, {
        headers: headers
    });
    return JSON.stringify({
        list: getList(resp.content)
    });
}

async function play(flag, id, flags) {
    let url = host + "/anime_" + id + ".html";
    let resp = await req(url, {
        headers
    });
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
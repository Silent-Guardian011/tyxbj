let host = 'https://zrys.pw';
let headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; M2102J2SC Build/TKQ1.221114.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/143.0.7499.3 Mobile Safari/537.36"
};

async function init(cfg) {}

function getList(html) {
    let videos = [];
    let items = pdfa(html, ".module-item");

    items.forEach(it => {
        let idMatch = it.match(/detail\/id\/(\d+).html/);
        let nameMatch = it.match(/title="(.*?)"/) || it.match(/alt="(.*?)"/);
        let picMatch = it.match(/data-original="(.*?)"/) || it.match(/src="(.*?)"/);
        let remarksMatch = it.match(/<div class="module-item-note">([^>]+)<\/div>/);

        if (idMatch && nameMatch) {
            let pic = picMatch ? (picMatch[1] || picMatch[2]) : "";
            videos.push({
                vod_id: idMatch[1],
                vod_name: nameMatch[1].replace(/<.*?>/g, ""),
                vod_pic: pic.startsWith('/') ? host + pic : pic,
                vod_remarks: "✨冉神甄选✨" + (remarksMatch || ["", ""])[1].replace(/<.*?>/g, "").replace("第", "")
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
            },
            {
                "type_id": "2",
                "type_name": "剧集"
            },
            {
                "type_id": "3",
                "type_name": "综艺"
            },
            {
                "type_id": "4",
                "type_name": "动漫"
            },
            {
                "type_id": "47",
                "type_name": "短视频"
            }
        ],
        "filters": {
            "1": [{
                "key": "class",
                "name": "类型",
                "value": [{
                    "n": "全部",
                    "v": ""
                }, {
                    "n": "动作片",
                    "v": "6"
                }, {
                    "n": "喜剧片",
                    "v": "7"
                }, {
                    "n": "爱情片",
                    "v": "8"
                }, {
                    "n": "科幻片",
                    "v": "9"
                }, {
                    "n": "恐怖片",
                    "v": "11"
                }]
            }],
            "2": [{
                "key": "class",
                "name": "类型",
                "value": [{
                    "n": "全部",
                    "v": ""
                }, {
                    "n": "国产剧",
                    "v": "13"
                }, {
                    "n": "港台剧",
                    "v": "14"
                }, {
                    "n": "日剧",
                    "v": "15"
                }, {
                    "n": "韩剧",
                    "v": "33"
                }, {
                    "n": "欧美剧",
                    "v": "16"
                }]
            }],
            "3": [{
                "key": "class",
                "name": "类型",
                "value": [{
                    "n": "全部",
                    "v": ""
                }, {
                    "n": "内地综艺",
                    "v": "27"
                }, {
                    "n": "港台综艺",
                    "v": "28"
                }, {
                    "n": "日本综艺",
                    "v": "29"
                }, {
                    "n": "韩国综艺",
                    "v": "36"
                }]
            }],
            "4": [{
                "key": "class",
                "name": "类型",
                "value": [{
                    "n": "全部",
                    "v": ""
                }, {
                    "n": "国产动漫",
                    "v": "31"
                }, {
                    "n": "日本动漫",
                    "v": "32"
                }, {
                    "n": "欧美动漫",
                    "v": "42"
                }, {
                    "n": "其他动漫",
                    "v": "43"
                }]
            }]
        }
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
    let url = host + "/index.php/vod/show/id/" + targetId + "/" + (parseInt(p) > 1 ? "page/" + p + ".html" : "");
    let resp = await req(url, {
        headers: headers
    });
    return JSON.stringify({
        "list": getList(resp.content),
        "page": parseInt(p)
    });
}

async function detail(id) {
    let url = host + '/index.php/vod/detail/id/' + id + '.html';
    let resp = await req(url, {
        headers: headers
    });
    let html = resp.content;

    let playFrom = pdfa(html, ".tab-item").map(it => "✨冉神👉" + (it.match(/<span>(.*?)<\/span>/) || ["", "线路"])[1]).join('$$$');
    let playUrl = pdfa(html, ".module-play-list-content").map(list =>
        pdfa(list, "a").map(a => {
            let n = "📽️冉神👉" + (a.match(/<span>(.*?)<\/span>/) || ["", "播放"])[1];
            let v = a.match(/href="\/index.php\/vod\/play\/id\/(.*?).html"/);
            return n + '$' + (v ? v[1] : "");
        }).join('#')
    ).join('$$$');

    return JSON.stringify({
        list: [{
            'vod_id': id,
            'vod_name': (html.match(/<h1>(.*?)<\/h1>/) || ["", ""])[1],
            'vod_pic': (html.match(/data-original="(.*?)"/) || ["", ""])[1],
            'vod_year': (html.match(/<a title="(\d{4})" href="\/index.php\/vod\/show\/id\/(\d+)\/year\/(\d{4}).html">(\d{4})<\/a>/) || ["", ""])[1],
            'vod_area': (html.match(/<a title="([^>]+)" href="\/index.php\/vod\/show\/area\/([^>]+)\/id\/(\d+).html">([^>]+)<\/a>/) || ["", ""])[1],
            'vod_lang': (html.match(/<span class="module-info-item-title">语言：<\/span>\s*<div class="module-info-item-content">\s*([^<]+)\s*<\/div>/) || ["", ""])[1].trim(),
            'vod_remarks': (html.match(/<span class="module-info-item-title">集数：<\/span>\s*<div class="module-info-item-content">\s*([^<]+)\s*<\/div>/) || html.match(/<span class="module-info-item-title">备注：<\/span>\s*<div class="module-info-item-content">\s*([^<]+)\s*<\/div>/) || html.match(/<span class="module-info-item-title">连载：<\/span>\s*<div class="module-info-item-content">\s*([^<]+)\s*<\/div>/) || ["", ""])[1].trim(),
            'type_name': (() => {
                const links = Array.from(
                    html.matchAll(/<div class="module-info-tag-link">([\s\S]*?)<\/div>/g)
                );
                const third = links[2];
                if (!third) return '';
                return Array.from(
                    third[1].matchAll(/<a[^>]*>([^<]+)<\/a>/g),
                    m => m[1].trim()
                ).join(' / ');
            })(),
            'vod_actor': Array.from(
                html.match(/<span class="module-info-item-title">主演：<\/span>\s*<div class="module-info-item-content">([\s\S]*?)<\/div>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            'vod_director': Array.from(
                html.match(/<span class="module-info-item-title">导演：<\/span>\s*<div class="module-info-item-content">([\s\S]*?)<\/div>/)?.[1]?.matchAll(/<a [^>]*>([^<]+)<\/a>/g) || []).map(m => m[1]).join(' / ') || '',
            'vod_content': "😸冉神🎉为你介绍剧情📢本资源来源于网络🚓侵权请联系删除👉" + (html.match(/module-info-introduction">.*?<p>(.*?)<\/p>/s) || ["", ""])[1].replace(/<.*?>/g, ""),
            'vod_play_from': playFrom,
            'vod_play_url': playUrl
        }]
    });
}

async function search(wd, quick, pg) {
    let p = pg || 1;
    let url = `${host}/index.php/vod/search` + (parseInt(p) > 1 ? `/page/${p}` : '') + `/wd/${encodeURIComponent(wd)}.html`;
    let resp = await req(url, {
        headers: headers
    });
    return JSON.stringify({
        list: getList(resp.content)
    });
}

async function play(flag, id, flags) {
    let url = host + "/index.php/vod/play/id/" + id + ".html";
    let resp = await req(url, {
        headers: headers
    });
    let m3u8 = resp.content.match(/"url":"([^"]+\.m3u8)"/);
    if (m3u8) return JSON.stringify({
        parse: 0,
        url: m3u8[1].replace(/\\/g, ""),
        header: headers
    });
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
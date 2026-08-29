/*
@header({
  searchable: 1,
  filterable: 1,
  quickSearch: 1,
  title: '芸芸音乐[听]',
  lang: 'cat'
})
*/

let siteName = '芸芸音乐', siteKey = '', siteType = 0;

const GD_API = 'https://music-api.gdstudio.xyz/api.php';
const NETEASE_HOST = 'https://music.163.com';

const filterOptions = [
    { key: "area", name: "分类", value: [
        { "n": "推荐歌单", "v": "recommend" },
        { "n": "排行榜", "v": "toplist" },
        { "n": "热门歌单", "v": "hot" },
        { "n": "热门歌手", "v": "artist" }
    ]}
];

function init(cfg) {
    siteName = cfg.skey?.split('_')[1] || cfg.skey || '芸芸音乐';
    siteKey = cfg.skey;
    siteType = cfg.stype;
}

function safeJSONParse(str, defaultValue = {}) {
    if (!str || typeof str === 'object') return str || defaultValue;
    try { return JSON.parse(str); } catch { return defaultValue; }
}

async function request(url, options = {}) {
    const reqHeaders = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Referer': 'https://music.163.com/',
        ...options.headers
    };
    try {
        const response = await req(url, {
            method: options.method || 'GET',
            headers: reqHeaders,
            data: options.data,
            timeout: options.timeout || 10000
        });
        return response?.content || response?.data || response;
    } catch { return ''; }
}

function sleep(seconds) {
    return new Promise(resolve => setTimeout(resolve, seconds * 1000));
}

function getPicUrl(pic, size = '500y500') {
    if (!pic) return '';
    return pic + '?param=' + size;
}

function getSongPic(song, defaultPic, size = '300y300') {
    let pic = song.al?.picUrl || song.album?.picUrl || defaultPic;
    if (pic) {
        pic = pic.replace('?param=500y500', '?param=' + size);
        pic = pic.replace('?param=300y300', '?param=' + size);
    }
    return pic || '';
}

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 10000) return (num / 10000).toFixed(1) + '万';
    return num.toString();
}

async function gdGetUrl(id, br) {
    const url = `${GD_API}?types=url&id=${id}&source=netease&br=${br}`;
    const html = await request(url);
    if (!html) return null;
    return safeJSONParse(html);
}

function buildPlayData(tracks, defaultPic) {
    let songPicArr = tracks.map(s => getSongPic(s, defaultPic, '300y300'));
    const playPic = songPicArr.join('#');
    const playUrl = tracks.map(s => {
        let songPic = getSongPic(s, defaultPic, '300y300');
        let artistName = s.ar?.map(a => a.name).join('/') || s.artists?.map(a => a.name).join('/') || '';
        let displayName = artistName ? `${s.name} - ${artistName}` : s.name;
        return `${displayName}$${s.id}&&${songPic}`;
    }).join('#');
    return { playUrl, playPic };
}

async function home(filter) {
    return JSON.stringify({
        class: [
            { type_name: '推荐歌单', type_id: 'recommend' },
            { type_name: '排行榜', type_id: 'toplist' },
            { type_name: '热门歌单', type_id: 'hot' },
            { type_name: '热门歌手', type_id: 'artist' }
        ],
        filters: {
            recommend: filterOptions,
            toplist: filterOptions,
            hot: filterOptions,
            artist: filterOptions
        }
    });
}

async function homeVod() {
    const videos = await getList('recommend', 1, {});
    return JSON.stringify({ list: videos.slice(0, 20) });
}

async function getList(type, page, extend) {
    const limit = 20;
    const offset = (page - 1) * limit;
    let videos = [];
    try {
        let url = '';
        let html = '';
        let json = {};
        switch (type) {
            case 'recommend':
                url = `${NETEASE_HOST}/api/personalized/playlist?limit=${page * limit}`;
                html = await request(url);
                json = safeJSONParse(html);
                (json.result || []).slice(offset).forEach(it => {
                    videos.push({
                        vod_id: `playlist@${it.id}`,
                        vod_name: it.name,
                        vod_pic: getPicUrl(it.picUrl, '300y300'),
                        vod_remarks: `🎧${formatNumber(it.playCount || 0)}`
                    });
                });
                break;
            case 'toplist':
                url = `${NETEASE_HOST}/api/toplist`;
                html = await request(url);
                json = safeJSONParse(html);
                (json.list || []).slice(offset, offset + limit).forEach(it => {
                    videos.push({
                        vod_id: `toplist@${it.id}`,
                        vod_name: it.name,
                        vod_pic: getPicUrl(it.coverImgUrl || it.picUrl, '300y300'),
                        vod_remarks: it.updateFrequency || `${it.trackCount || 0}首`
                    });
                });
                break;
            case 'hot':
                const cat = extend?.cat || '全部';
                url = `${NETEASE_HOST}/api/playlist/list?cat=${encodeURIComponent(cat)}&limit=${limit}&offset=${offset}&order=hot`;
                html = await request(url);
                json = safeJSONParse(html);
                (json.playlists || []).forEach(it => {
                    videos.push({
                        vod_id: `playlist@${it.id}`,
                        vod_name: it.name,
                        vod_pic: getPicUrl(it.coverImgUrl, '300y300'),
                        vod_remarks: it.playCount ? formatNumber(it.playCount) : ''
                    });
                });
                break;
            case 'artist':
                url = `${NETEASE_HOST}/api/artist/top?limit=${limit}&offset=${offset}`;
                html = await request(url);
                json = safeJSONParse(html);
                (json.artists || []).forEach(it => {
                    videos.push({
                        vod_id: `artist@${it.id}`,
                        vod_name: it.name,
                        vod_pic: getPicUrl(it.img1v1Url || it.picUrl, '300y300'),
                        vod_remarks: `${it.albumSize || 0}张专辑`
                    });
                });
                break;
        }
    } catch (e) {}
    return videos;
}

async function getDetail(type, id) {
    let vod = {};
    try {
        let url = '';
        let html = '';
        let json = {};
        let tracks = [];
        let data = {};
        if (type === 'artist') {
            url = `${NETEASE_HOST}/api/artist/${id}`;
            html = await request(url);
            json = safeJSONParse(html);
            data = json.artist || {};
            tracks = json.hotSongs || [];
            const defaultPic = getPicUrl(data.picUrl || data.img1v1Url, '500y500');
            const { playUrl, playPic } = buildPlayData(tracks, defaultPic);
            vod = {
                vod_id: `artist@${id}`,
                vod_name: data.name || '未知歌手',
                vod_pic: defaultPic,
                vod_content: data.briefDesc || data.name,
                vod_remarks: `共${tracks.length}首`,
                vod_play_from: '芸芸音乐',
                vod_play_url: playUrl,
                vod_play_pic: playPic,
                vod_play_pic_ratio: 1.0
            };
        } else {
            url = `${NETEASE_HOST}/api/playlist/detail?id=${id}`;
            html = await request(url);
            json = safeJSONParse(html);
            const playlist = json.result || json.playlist || {};
            data = playlist;
            tracks = playlist.tracks || [];
            const defaultPic = getPicUrl(data.coverImgUrl || data.picUrl, '500y500');
            const { playUrl, playPic } = buildPlayData(tracks, defaultPic);
            vod = {
                vod_id: `playlist@${id}`,
                vod_name: data.name || '未知歌单',
                vod_pic: defaultPic,
                vod_content: data.description || data.name,
                vod_remarks: `${formatNumber(data.playCount || 0)} | 共${tracks.length}首`,
                vod_play_from: '芸芸音乐',
                vod_play_url: playUrl,
                vod_play_pic: playPic,
                vod_play_pic_ratio: 1.0
            };
        }
    } catch (e) {}
    return vod;
}

async function playSong(id) {
    try {
        const parts = id.split('&&');
        const firstPart = parts[0] || '';
        const firstParts = firstPart.split('$');
        const songId = firstParts.length > 1 ? firstParts[1] : firstParts[0];
        const albumPic = parts[1] || '';

        const qualities = [
            { name: 'FLAC无损', br: 2000 },
            { name: 'HQ高品质', br: 320 },
            { name: '标准品质', br: 192 },
            { name: 'AAC流畅', br: 128 }
        ];

        let urls = [];
        let seenUrls = new Set();
        for (let q of qualities) {
            try {
                let res = await gdGetUrl(songId, q.br);
                if (res?.url && !seenUrls.has(res.url)) {
                    seenUrls.add(res.url);
                    urls.push(q.name, res.url);
                }
            } catch (e) {}
        }

        let [lyricJson, cover] = await Promise.all([
            (async () => {
                const res = await request(`${NETEASE_HOST}/api/song/lyric?id=${songId}&lv=1&kv=1&tv=-1`);
                const json = safeJSONParse(res);
                let lrc = json.lrc?.lyric || '';
                if (json.tlyric?.lyric) lrc = lrc + '\n\n【翻译】\n' + json.tlyric.lyric;
                return lrc;
            })(),
            (async () => {
                if (albumPic) return albumPic;
                try {
                    let infoRes = await request(`${NETEASE_HOST}/api/song/detail?ids=[${songId}]`);
                    let infoJson = safeJSONParse(infoRes);
                    let song = infoJson.songs?.[0];
                    return song?.al?.picUrl ? song.al.picUrl + '?param=500y500' : (song?.album?.picUrl ? song.album.picUrl + '?param=500y500' : '');
                } catch { return ''; }
            })()
        ]);

        return JSON.stringify({
            parse: 0,
            url: urls,
            header: { 'User-Agent': 'Mozilla/5.0' },
            pic: cover,
            cover: cover,
            lrc: lyricJson || '',
            height: 720
        });
    } catch (e) {
        return JSON.stringify({ parse: 0, url: id });
    }
}

async function searchNetease(wd, page) {
    const results = [];
    try {
        const url = `${NETEASE_HOST}/api/search/get?s=${encodeURIComponent(wd)}&type=1&offset=${(page - 1) * 30}&limit=30`;
        const html = await request(url);
        const json = safeJSONParse(html);
        const songs = json.result?.songs || json.songs || [];
        for (let it of songs) {
            let songId = it.id || '';
            let songName = it.name || '未知歌曲';
            let artists = it.ar?.map(a => a.name).join('/') || it.artists?.map(a => a.name).join('/') || '未知歌手';
            let picUrl = it.al?.picUrl || it.album?.picUrl || '';
            if (picUrl && !picUrl.startsWith('http')) picUrl = 'https://p1.music.126.net/' + picUrl;
            let displayName = `${songName} - ${artists}`;
            results.push({
                vod_id: `song@${songId}`,
                vod_name: displayName,
                vod_pic: getPicUrl(picUrl, '300y300'),
                vod_remarks: it.al?.name || it.album?.name || '网易云音乐'
            });
        }
    } catch (e) {}
    return results;
}

async function cfs(wd, pg) {
    const page = pg || 1;
    const results = await searchNetease(wd, page);
    return JSON.stringify({ list: results, page: page, pagecount: page + 1, limit: results.length, total: results.length * (page + 1) });
}

async function category(tid, pg, filter, extend) {
    const page = pg || 1;
    extend = extend || {};
    const searchKeyword = extend?.custom;
    if (searchKeyword) return await cfs(searchKeyword, pg);
    const area = filter?.area || extend?.area || tid;
    const videos = await getList(area, page, extend);
    return JSON.stringify({ list: videos, page: page, pagecount: page + 1, limit: videos.length, total: videos.length * (page + 1) });
}

async function detail(id) {
    const parts = id.split('@');
    const type = parts[0] || 'song';
    const did = parts.slice(1).join('@');
    let vod = {};

    if (type === 'song') {
        try {
            const infoRes = await request(`${NETEASE_HOST}/api/song/detail?ids=[${did}]`);
            const infoJson = safeJSONParse(infoRes);
            const song = infoJson.songs?.[0];
            if (song) {
                let artistName = song.ar?.map(a => a.name).join('/') || '';
                let songPic = getSongPic(song, '', '300y300');
                vod = {
                    vod_id: `song@${did}`,
                    vod_name: artistName ? `${song.name} - ${artistName}` : song.name,
                    vod_pic: songPic,
                    vod_play_from: '芸芸音乐',
                    vod_play_url: `${song.name}$${did}&&${songPic}`,
                    vod_play_pic: songPic,
                    vod_play_pic_ratio: 1.0
                };
            }
        } catch (e) {}
    } else {
        vod = await getDetail(type, did);
    }

    return JSON.stringify({ list: [vod] });
}

async function play(flag, id, flags) {
    return await playSong(id);
}

async function search(wd, quick, pg) {
    const page = pg || 1;
    const results = await searchNetease(wd, page);
    return JSON.stringify({ list: results, page: page, pagecount: page + 1, limit: results.length, total: results.length * (page + 1) });
}

export function __jsEvalReturn() {
    return { init, home, homeVod, category, detail, play, search, cfs };
}
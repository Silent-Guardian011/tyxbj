const API_BASE = 'https://x.xvideos4.tk/api.php/v1/records';
const API_KEY = 'text';
const NAV = [
  { sort: 'daily',    label: '今日',   href: '/zh-CN/',        icon: '🔥', range: 'today' },
  { sort: 'weekly',   label: '本周',   href: '/zh-CN/weekly/', icon: '📅', range: 'week' },
  { sort: 'monthly',  label: '本月',   href: '/zh-CN/monthly/',icon: '🗓', range: 'month' },
  { sort: 'favorite', label: '全部',   href: '/zh-CN/all/',    icon: '✨', range: 'all' },
];
const CATEGORIES = [
  { id: 'gay',             name: '男娘' },
  { id: 'anime',           name: '动漫' },
  { id: 'lolita',          name: '少女' },
  { id: 'shaved',          name: '白虎' },
  { id: 'kyonyu',          name: '巨乳' },
  { id: 'jk',              name: '高中生' },
  { id: 'beautiful-girl',  name: '美少女' },
  { id: 'small-breasts',   name: '贫乳' },
  { id: 'sm',              name: 'SM' },
  { id: 'masturbation',    name: '自慰' },
  { id: 'hamedori',        name: '自拍' },
  { id: 'female-pervert',  name: '痴女' },
  { id: 'personal-filming',name: '私拍' },
  { id: 'outdoor',         name: '户外' },
  { id: 'big-sister',      name: '姐姐' },
  { id: 'incest',          name: '乱伦' },
  { id: 'married-woman',   name: '人妻' },
  { id: 'orgy',            name: '群交' },
  { id: 'fellatio',        name: '口交' },
  { id: 'bukkake',         name: '颜射' },
];
async function apiList(options) {
  const sort = options.sort;
  const category = options.category;
  const page = options.page;
  const q = options.q;
  const navItem = NAV.find(function(n) { return n.sort === sort; }) || NAV[0];
  const qp = new URLSearchParams({
    api_key: API_KEY,
    range:   navItem.range,
    type:    'video',
    page:    String(page || 1),
    limit:   '20'
  });
  let keyword = '';
  if (q) {
    keyword = q;
    qp.set('q', q);
  } else if (category) {
    const cat = CATEGORIES.find(function(c) { return c.id === category; });
    keyword = cat ? cat.name : category;
    qp.set('q', keyword);
  }
  const res = await fetch(API_BASE + '?' + qp.toString(), {
    headers: { 'Accept': 'application/json' }
  });
  if (!res.ok) return null;
  const json = await res.json().catch(function() { return null; });
  if (json && json.data && keyword) {
    json.data = json.data.filter(function(item) {
      return (item.tweet_text && item.tweet_text.indexOf(keyword) !== -1) ||
             (item.author_name && item.author_name.indexOf(keyword) !== -1);
    });
  }
  return json;
}
async function apiDetail(id) {
  const qpQ = new URLSearchParams({ 
    api_key: API_KEY, 
    range: 'all',
    type: 'video',
    page: '1', 
    limit: '1', 
    q: id 
  });
  const res = await fetch(API_BASE + '?' + qpQ.toString(), {
    headers: { 'Accept': 'application/json' }
  });
  if (!res.ok) return null;
  const data = await res.json().catch(function() { return null; });
  const list = (data && data.data) ? data.data : [];
  if (!list.length) return null;
  return list.find(function(i) { return String(i.id) === String(id); }) || list[0] || null;
}
function normalizeItem(item) {
  const video = (item.media && item.media.videos && item.media.videos[0]) ? item.media.videos[0] : {};
  return {
    id:       item.id          || '',
    title:    item.tweet_text  || '未知',
    thumb:    video.thumbnail  || '',
    videoUrl: video.url        || '',
    time:     item.duration_str || '00:00',
    pv:       '0',
    favorite: '0',
  };
}
function isHlsUrl(url) {
  if (!url) return false;
  return /\.m3u8|playlist|\/HLS\/|\/hls\//i.test(url);
}
function isMp4Url(url) {
  if (!url) return false;
  return /\.mp4(\?|$)|\.webm(\?|$)|\.ogg(\?|$)/i.test(url);
}
function jsonResponse(data, status) {
  status = status || 200;
  return new Response(JSON.stringify(data), {
    status: status,
    headers: {
      'Content-Type':                'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control':               'no-cache',
    },
  });
}
export default {
  async fetch(request) {
    const url    = new URL(request.url);
    const path   = url.pathname;
    const params = url.searchParams;
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin':  '*',
          'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS, POST',
          'Access-Control-Allow-Headers': 'Range, Content-Type',
        }
      });
    }
    try {
      if (path === '/play')        return handlePlay(params);
      if (path === '/api/resolve') return handleResolve(params);
      if (path === '/api/refresh') return handleRefresh(params.get('id') || '');
      if (path === '/api/extract' && request.method === 'POST') {
        const body = await request.json();
        const res = await fetch('https://x.xvideos4.tk/extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body)
        });
        const data = await res.json();
        return jsonResponse(data, res.status);
      }
      if (path.indexOf('/movie/') !== -1) {
        const parts = path.split('/').filter(Boolean);
        const id = parts.pop();
        return handleDetail(id);
      }
      if (path === '/search') {
        const q    = params.get('tag') || params.get('q') || '';
        const page = parseInt(params.get('page') || '1', 10);
        return handleList({ sort: 'favorite', category: '', q: q, page: page, isSearch: true });
      }
      const catMatch = path.match(/\/category\/([^\/\s?]+)/);
      if (catMatch) {
        const page = parseInt(params.get('page') || '1', 10);
        return handleList({ sort: 'favorite', category: catMatch[1], page: page });
      }
      const sortMap = {
        '/zh-cn/weekly':  'weekly',  '/zh-CN/weekly':  'weekly',
        '/zh-cn/weekly/': 'weekly',  '/zh-CN/weekly/': 'weekly',
        '/zh-cn/monthly': 'monthly', '/zh-CN/monthly': 'monthly',
        '/zh-cn/monthly/':'monthly', '/zh-CN/monthly/':'monthly',
        '/zh-cn/all':     'favorite','/zh-CN/all':     'favorite',
        '/zh-cn/all/':    'favorite','/zh-CN/all/':    'favorite',
      };
      const sort = sortMap[path] || 'daily';
      const page = parseInt(params.get('page') || '1', 10);
      return handleList({ sort: sort, category: '', page: page });
    } catch (e) {
      return new Response('Error: ' + e.message + '\n' + e.stack, { status: 500 });
    }
  }
};
async function handleResolve(params) {
  const rawUrl = params.get('url') || '';
  if (!rawUrl || rawUrl.indexOf('http') !== 0) {
    return jsonResponse({ error: 'invalid_url' }, 400);
  }
  let origin = '';
  try { origin = new URL(rawUrl).origin; } catch (_) {}
  const commonHeaders = {
    'User-Agent':
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
      + 'AppleWebKit/605.1.15 (KHTML, like Gecko) '
      + 'Version/17.0 Mobile/15E148 Safari/604.1',
    'Referer': origin ? origin + '/' : 'https://x.xvideos4.tk/',
    'Origin':  origin || 'https://x.xvideos4.tk',
    'Accept':  'video/mp4,video/webm,application/x-mpegurl,*/*;q=0.9',
  };
  try {
    const ctrl  = new AbortController();
    const timer = setTimeout(function() { ctrl.abort(); }, 8000);
    const res   = await fetch(rawUrl, {
      method: 'HEAD', redirect: 'follow', signal: ctrl.signal, headers: commonHeaders,
    });
    clearTimeout(timer);
    const ct       = res.headers.get('content-type') || '';
    const finalUrl = res.url || rawUrl;
    const isHls    = ct.indexOf('mpegurl') !== -1 || ct.indexOf('x-mpegurl') !== -1 || isHlsUrl(finalUrl);
    const isMp4    = ct.indexOf('video/') === 0 || isMp4Url(finalUrl);
    return jsonResponse({ url: finalUrl, isHls: isHls, isMp4: isMp4, contentType: ct, status: res.status });
  } catch (headErr) {
    try {
      const ctrl2  = new AbortController();
      const timer2 = setTimeout(function() { ctrl2.abort(); }, 8000);
      const res2   = await fetch(rawUrl, {
        method: 'GET', redirect: 'follow', signal: ctrl2.signal, headers: commonHeaders,
      });
      clearTimeout(timer2);
      const ct2       = res2.headers.get('content-type') || '';
      const finalUrl2 = res2.url || rawUrl;
      const isHls2    = ct2.indexOf('mpegurl') !== -1 || ct2.indexOf('x-mpegurl') !== -1 || isHlsUrl(finalUrl2);
      const isMp42    = ct2.indexOf('video/') === 0 || isMp4Url(finalUrl2);
      return jsonResponse({ url: finalUrl2, isHls: isHls2, isMp4: isMp42, contentType: ct2, status: res2.status });
    } catch (getErr) {
      return jsonResponse({
        url: rawUrl, isHls: isHlsUrl(rawUrl), isMp4: isMp4Url(rawUrl), error: getErr.message,
      });
    }
  }
}
async function handleRefresh(id) {
  if (!id) return jsonResponse({ error: 'no id' }, 400);
  try {
    const raw = await apiDetail(id);
    if (!raw) return jsonResponse({ error: 'not_found' }, 404);
    const item = normalizeItem(raw);
    const proxySrc = item.videoUrl;
    if (!proxySrc) return jsonResponse({ error: 'no_url' }, 404);
    return jsonResponse({ proxySrc: proxySrc, isHls: isHlsUrl(proxySrc) });
  } catch (e) {
    return jsonResponse({ error: e.message }, 500);
  }
}
async function handleList(options) {
  const data     = await apiList(options);
  const list     = (data && data.data) ? data.data : [];
  const movies   = list.map(normalizeItem);
  const page     = options.page;
  const lastPage = page + 1; 
  const category = options.category;
  const catLabel = CATEGORIES.find(function(c) { return c.id === category; })?.name || category;
  const title    = category ? '# ' + catLabel : (options.isSearch ? '搜索：' + options.q : (NAV.find(function(n) { return n.sort === options.sort; })?.label || '今日'));
  return new Response(
    renderLayout(renderList(movies, options), title, options.sort),
    { headers: { 'Content-Type': 'text/html;charset=UTF-8' } }
  );
}
async function handleDetail(id) {
  const raw   = await apiDetail(id);
  const movie = raw ? normalizeItem(raw) : {
    id: id, title: id, thumb: '', videoUrl: '', time: '00:00', pv: '0', favorite: '0'
  };
  return new Response(
    renderLayout(renderDetail(movie), movie.title, ''),
    { headers: { 'Content-Type': 'text/html;charset=UTF-8' } }
  );
}
async function handlePlay(params) {
  const videoUrl = params.get('v') || '';
  if (!videoUrl || videoUrl.indexOf('http') !== 0) {
    return new Response('无效的播放链接', { status: 400 });
  }
  return new Response(null, { status: 302, headers: { Location: videoUrl } });
}
function renderList(movies, options) {
  const sort = options.sort;
  const category = options.category;
  const q = options.q;
  const page = options.page;
  const isSearch = options.isSearch;
  const grid = movies.map(function(m) {
    const thumb      = m.thumb || 'https://placehold.co/300x533/111/333?text=No+Image';
    const playHref   = m.videoUrl ? m.videoUrl : '/zh-CN/movie/' + encodeURIComponent(m.id);
    const playTarget = m.videoUrl ? ' target="_blank" rel="noopener noreferrer"' : '';
    return '<div class="card">' +
  '<a href="' + playHref + '"' + playTarget + ' class="card-thumb">' +
    '<img loading="lazy" src="' + thumb + '" alt="' + esc(m.title) + '"' +
         ' onerror="this.src=\'https://placehold.co/300x533/111/333?text=No+Image\'"> ' +
    '<span class="badge-time">' + esc(m.time) + '</span>' +
  '</a>' +
  '<div class="card-body">' +
    '<a href="/zh-CN/movie/' + encodeURIComponent(m.id) + '" class="card-title-link">' +
      '<h3 class="card-title">' + esc(m.title) + '</h3>' +
    '</a>' +
    '<div class="card-meta">' +
      '<span>👁 ' + esc(m.pv) + '</span>' +
      '<span class="fav">❤ ' + esc(m.favorite) + '</span>' +
    '</div>' +
  '</div>' +
'</div>';
  }).join('');
  function pageUrl(p) {
    if (isSearch) return '/search?tag=' + encodeURIComponent(q || category || '') + '&page=' + p;
    if (category) return '/zh-CN/category/' + encodeURIComponent(category) + '?page=' + p;
    return (NAV.find(function(n) { return n.sort === sort; })?.href || '/zh-CN/') + '?page=' + p;
  }
  const pagination = (page > 1 || movies.length > 0) ? 
'<div class="pagination">' +
  (page > 1
    ? '<a href="' + pageUrl(page-1) + '" class="page-btn">← 上一页</a>'
    : '<span class="page-btn disabled">← 上一页</span>') +
  '<span class="page-info">第 ' + page + ' 页</span>' +
  (movies.length >= 20
    ? '<a href="' + pageUrl(page+1) + '" class="page-btn">下一页 →</a>'
    : '<span class="page-btn disabled">下一页 →</span>') +
'</div>' : '';
  const catChips = CATEGORIES.map(function(c) {
    return '<a href="/zh-CN/category/' + c.id + '" class="chip' + (category === c.id ? ' chip-active' : '') + '">' + esc(c.name) + '</a>';
  }).join('');
  const empty = movies.length === 0 ? 
'<div class="empty-state">' +
  '<div class="empty-icon">📭</div>' +
  '<div class="empty-text">暂无内容</div>' +
'</div>' : '';
  return '<div class="page-wrap">' +
  '<div class="extract-section">' +
    '<div class="extract-label">帖子链接</div>' +
    '<div class="extract-box">' +
      '<input type="text" id="extractUrl" placeholder="https://x.com/user/status/1234567890…" autocomplete="off">' +
      '<button id="extractBtn" onclick="doExtract()">' +
        '<span id="extractBtnIcon">⬇</span>' +
        '<span id="extractBtnText">提取</span>' +
      '</button>' +
    '</div>' +
    '<div id="extractStatus" class="extract-status"></div>' +
    '<div id="extractResult" class="extract-result-area" style="display:none"></div>' +
  '</div>' +
  '<div class="search-bar-wrap">' +
    '<form action="/search" method="GET" class="search-form">' +
      '<input type="search" name="tag" placeholder="搜索标签 / 账号…"' +
             ' value="' + esc(isSearch ? (q || category) : '') + '"' +
             ' autocomplete="off" enterkeyhint="search">' +
      '<button type="submit" aria-label="搜索">' +
        '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">' +
          '<circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>' +
        '</svg>' +
      '</button>' +
    '</form>' +
  '</div>' +
  '<div class="chips-wrap">' +
    '<div class="chips-scroll">' +
      '<a href="/zh-CN/" class="chip' + (!category ? ' chip-active' : '') + '">全部分类</a>' +
      catChips +
    '</div>' +
  '</div>' +
  (movies.length > 0 ? '<div class="grid">' + grid + '</div>' + pagination : empty) +
'</div>' +
'<script>' +
'async function doExtract() {' +
'  var url = document.getElementById("extractUrl").value.trim();' +
'  var btn = document.getElementById("extractBtn");' +
'  var status = document.getElementById("extractStatus");' +
'  var resultArea = document.getElementById("extractResult");' +
'  if (!url) {' +
'    status.innerText = "请输入帖子链接";' +
'    status.className = "extract-status error";' +
'    return;' +
'  }' +
'  btn.disabled = true;' +
'  document.getElementById("extractBtnText").innerText = "提取中...";' +
'  status.innerText = "正在提取中...";' +
'  status.className = "extract-status loading";' +
'  resultArea.style.display = "none";' +
'  try {' +
'    var res = await fetch("/api/extract", {' +
'      method: "POST",' +
'      headers: { "Content-Type": "application/json" },' +
'      body: JSON.stringify({ url: url })' +
'    });' +
'    var json = await res.json();' +
'    if (res.ok) {' +
'      status.innerText = "提取成功！";' +
'      status.className = "extract-status success";' +
'      renderExtractResult(json);' +
'    } else {' +
'      status.innerText = json.error || "提取失败，请检查链接";' +
'      status.className = "extract-status error";' +
'    }' +
'  } catch (e) {' +
'    status.innerText = "网络错误: " + e.message;' +
'    status.className = "extract-status error";' +
'  } finally {' +
'    btn.disabled = false;' +
'    document.getElementById("extractBtnText").innerText = "提取";' +
'  }' +
'}' +
'function renderExtractResult(json) {' +
'  var area = document.getElementById("extractResult");' +
'  var videos = (json.media && json.media.videos) ? json.media.videos : [];' +
'  var images = (json.media && json.media.images) ? json.media.images : [];' +
'  var html = "<div class=\'res-grid\'>";' +
'  videos.forEach(function(v) {' +
'    html += "<div class=\'res-item\'>" +' +
'              "<div class=\'res-thumb\'>" +' +
'                "<img src=\'" + (v.thumbnail || "") + "\' border=\'0\'>" +' +
'                "<span class=\'res-badge\'>视频</span>" +' +
'              "</div>" +' +
'              "<a href=\'" + v.url + "\' target=\'_blank\' class=\'res-dl-btn\'>下载视频</a>" +' +
'            "</div>";' +
'  });' +
'  images.forEach(function(img) {' +
'    html += "<div class=\'res-item\'>" +' +
'              "<div class=\'res-thumb\'>" +' +
'                "<img src=\'" + img.url + "\' border=\'0\'>" +' +
'                "<span class=\'res-badge\'>图片</span>" +' +
'              "</div>" +' +
'              "<a href=\'" + img.url + "\' target=\'_blank\' class=\'res-dl-btn\'>下载图片</a>" +' +
'            "</div>";' +
'  });' +
'  html += "</div>";' +
'  area.innerHTML = html;' +
'  area.style.display = "block";' +
'}' +
'</script>';
}
function renderDetail(movie) {
  const thumbSrc  = movie.thumb   || '';
  const proxySrc  = movie.videoUrl || '';
  const movieId   = movie.id      || '';
  const guessHls  = isHlsUrl(proxySrc);
  const noVideoBlock = '<div class="no-video"><span>🎬</span><p>视频链接不可用</p></div>';
  const playerBlock = proxySrc ? 
'<div class="player-shell" id="playerShell">' +
  '<div class="player-poster" id="playerPoster">' +
    (thumbSrc
      ? '<img src="' + esc(thumbSrc) + '" alt="' + esc(movie.title) + '" class="poster-img">'
      : '<div class="poster-img poster-blank"></div>') +
    '<button class="big-play-btn" id="bigPlayBtn" aria-label="播放">' +
      '<svg viewBox="0 0 24 24" fill="white" width="44" height="44"><polygon points="5,3 19,12 5,21"/></svg>' +
    '</button>' +
    '<div class="player-spinner hidden" id="playerSpinner">' +
      '<div class="spinner-ring"></div>' +
    '</div>' +
    '<div class="player-error hidden" id="playerError">' +
      '<span>⚠️</span>' +
      '<p id="playerErrorMsg">加载失败</p>' +
      '<button class="retry-btn" onclick="initPlayer()">重试</button>' +
    '</div>' +
  '</div>' +
  '<video id="mainVideo" class="main-video" playsinline webkit-playsinline preload="none" ' +
    (thumbSrc ? 'poster="' + esc(thumbSrc) + '"' : '') +
    ' crossorigin="anonymous"></video>' +
'</div>' : noVideoBlock;
  const playerScript = proxySrc ? 
'<script>' +
'(function () {' +
'  var SRC      = ' + JSON.stringify(proxySrc) + ';' +
'  var THUMB    = ' + JSON.stringify(thumbSrc) + ';' +
'  var GUESS_HLS = ' + guessHls + ';' +
'  var HLS_CDN  = "https://cdn.jsdelivr.net/npm/hls.js@1/dist/hls.min.js";' +
'  var video        = document.getElementById("mainVideo");' +
'  var poster       = document.getElementById("playerPoster");' +
'  var bigPlayBtn   = document.getElementById("bigPlayBtn");' +
'  var spinner      = document.getElementById("playerSpinner");' +
'  var errorBox     = document.getElementById("playerError");' +
'  var errorMsg     = document.getElementById("playerErrorMsg");' +
'  var hlsInstance  = null;' +
'  var started      = false;' +
'  function show(el){ el && el.classList.remove("hidden"); }' +
'  function hide(el){ el && el.classList.add("hidden"); }' +
'  function initPlayer() {' +
'    hide(errorBox); show(bigPlayBtn); show(poster);' +
'    video.src = "";' +
'    if(hlsInstance){ hlsInstance.destroy(); hlsInstance = null; }' +
'  }' +
'  function startLoad() {' +
'    if(started) return; started = true;' +
'    hide(bigPlayBtn); show(spinner);' +
'    if(GUESS_HLS) {' +
'      if(video.canPlayType("application/vnd.apple.mpegurl")) {' +
'        video.src = SRC; video.play().catch(function(e){ console.error(e); });' +
'      } else {' +
'        var s = document.createElement("script");' +
'        s.src = HLS_CDN;' +
'        s.onload = function() {' +
'          if(!Hls.isSupported()) {' +
'            hide(spinner); show(errorBox); errorMsg.innerText = "浏览器不支持 HLS"; return;' +
'          }' +
'          hlsInstance = new Hls(); hlsInstance.loadSource(SRC); hlsInstance.attachMedia(video);' +
'          hlsInstance.on(Hls.Events.MANIFEST_PARSED, function(){ video.play().catch(function(e){ console.error(e); }); });' +
'        };' +
'        document.head.appendChild(s);' +
'      }' +
'    } else {' +
'      video.src = SRC; video.play().catch(function(e){ console.error(e); });' +
'    }' +
'  }' +
'  video.addEventListener("playing", function(){ hide(poster); hide(spinner); });' +
'  video.addEventListener("error", function(){ hide(spinner); show(errorBox); errorMsg.innerText = "视频加载出错"; });' +
'  bigPlayBtn.onclick = startLoad;' +
'})();' +
'</script>' : '';
  return '<div class="detail-wrap">' +
  '<a href="javascript:history.back()" class="back-btn">' +
    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">' +
      '<path d="M19 12H5M12 19l-7-7 7-7"/>' +
    '</svg>' +
    ' 返回' +
  '</a>' +
  '<div class="detail-card">' +
    '<div class="video-wrap">' + playerBlock + '</div>' +
    '<div class="detail-body">' +
      '<h1 class="detail-title">' + esc(movie.title) + '</h1>' +
      '<div class="detail-meta">' +
        '<span>👁 ' + esc(movie.pv) + '</span>' +
        '<span class="fav">❤ ' + esc(movie.favorite) + '</span>' +
        '<span>⏱ ' + esc(movie.time) + '</span>' +
      '</div>' +
    '</div>' +
  '</div>' +
'</div>' +
playerScript;
}
function esc(s) {
  return String(s || '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function renderLayout(content, title, activeSort) {
  const navLinks = NAV.map(function(n) {
    return '<a href="' + n.href + '" class="nav-link' + (activeSort === n.sort ? ' active' : '') + '">' + n.label + '</a>';
  }).join('');
  const bottomNav = NAV.map(function(n) {
    return '<a href="' + n.href + '" class="bnav-item' + (activeSort === n.sort ? ' active' : '') + '">' +
       '<span class="bnav-icon">' + n.icon + '</span>' +
       '<span class="bnav-label">' + n.label + '</span>' +
     '</a>';
  }).join('');
  return '<!DOCTYPE html>' +
'<html lang="zh-CN">' +
'<head>' +
'<meta charset="UTF-8">' +
'<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' +
'<meta name="theme-color" content="#000000">' +
'<title>' + esc(title) + ' - OTC VIDEO</title>' +
'<style>' +
'*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}' +
':root{' +
'  --bg:#000;--surface:#0d0d0d;--surface2:#161616;--border:rgba(255,255,255,0.07);' +
'  --text:#e8e8e8;--muted:#555;--accent:#e8195a;--accent2:#ff6b9d;' +
'  --radius:14px;--nav-h:56px;--bnav-h:60px;--safe-b:env(safe-area-inset-bottom,0px);' +
'}' +
'html{scroll-behavior:smooth}' +
'body{background:var(--bg);color:var(--text);font-family:sans-serif;font-size:14px;' +
'  line-height:1.5;-webkit-font-smoothing:antialiased;overflow-x:hidden;}' +
'a{color:inherit;text-decoration:none}' +
'img{display:block;max-width:100%}' +
'button{cursor:pointer;border:none;font-family:inherit}' +
'.topnav{' +
'  position:sticky;top:0;z-index:100;height:var(--nav-h);' +
'  background:rgba(0,0,0,0.85);' +
'  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);' +
'  border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 20px;gap:16px;}' +
'.logo{font-size:20px;font-weight:800;letter-spacing:-0.5px;white-space:nowrap;flex-shrink:0;}' +
'.logo span{color:var(--accent)}' +
'.topnav-search{' +
'  flex:1;max-width:340px;display:flex;align-items:center;' +
'  background:var(--surface2);border:1px solid var(--border);' +
'  border-radius:10px;overflow:hidden;transition:border-color .2s;}' +
'.topnav-search:focus-within{border-color:rgba(232,25,90,.4)}' +
'.topnav-search input{' +
'  flex:1;background:transparent;border:none;outline:none;' +
'  color:var(--text);font-size:13px;padding:8px 12px;}' +
'.topnav-search input::placeholder{color:var(--muted)}' +
'.topnav-search button{' +
'  background:transparent;color:var(--muted);padding:8px 12px;' +
'  display:flex;align-items:center;transition:color .2s;}' +
'.topnav-search button:hover{color:var(--accent2)}' +
'.topnav-links{display:flex;gap:4px;margin-left:auto}' +
'.nav-link{' +
'  padding:6px 14px;border-radius:8px;font-size:13px;font-weight:700;' +
'  color:var(--muted);transition:background .15s,color .15s;white-space:nowrap;}' +
'.nav-link:hover{color:var(--text);background:var(--surface2)}' +
'.nav-link.active{color:#fff;background:var(--accent)}' +
'.extract-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; margin-bottom: 24px; }' +
'.extract-label { font-size: 14px; color: var(--text); margin-bottom: 12px; font-weight: 500; }' +
'.extract-box { display: flex; gap: 10px; align-items: stretch; }' +
'.extract-box input { flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; color: var(--text); padding: 12px 16px; font-size: 14px; outline: none; }' +
'.extract-box input:focus { border-color: var(--accent); }' +
'.extract-box button { background: #1d9bf0; color: #fff; padding: 0 20px; border-radius: 8px; font-weight: 700; display: flex; align-items: center; gap: 6px; transition: opacity .2s; }' +
'.extract-box button:hover { opacity: 0.9; }' +
'.extract-box button:disabled { opacity: 0.5; cursor: not-allowed; }' +
'.extract-status { margin-top: 10px; font-size: 12px; }' +
'.extract-status.error { color: #ff4d4f; }' +
'.extract-status.success { color: #52c41a; }' +
'.extract-status.loading { color: #1d9bf0; }' +
'.extract-result-area { margin-top: 20px; padding-top: 20px; border-top: 1px dashed var(--border); }' +
'.res-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 12px; }' +
'.res-item { background: var(--surface2); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }' +
'.res-thumb { position: relative; aspect-ratio: 16/9; }' +
'.res-thumb img { width: 100%; height: 100%; object-fit: cover; }' +
'.res-badge { position: absolute; top: 4px; right: 4px; background: rgba(0,0,0,0.6); color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; }' +
'.res-dl-btn { padding: 8px; text-align: center; font-size: 12px; font-weight: 700; background: var(--accent); color: #fff; }' +
'.bnav{' +
'  position:fixed;bottom:0;left:0;right:0;z-index:100;' +
'  height:calc(var(--bnav-h) + var(--safe-b));padding-bottom:var(--safe-b);' +
'  background:rgba(0,0,0,0.92);' +
'  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);' +
'  border-top:1px solid var(--border);flex-direction:row;align-items:stretch;display:none;}' +
'.bnav-item{' +
'  flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;' +
'  gap:3px;color:var(--muted);transition:color .15s;' +
'  -webkit-tap-highlight-color:transparent;user-select:none;}' +
'.bnav-item.active{color:var(--accent)}' +
'.bnav-icon{font-size:18px;line-height:1}' +
'.bnav-label{font-size:10px;font-weight:700}' +
'.main-content{min-height:calc(100vh - var(--nav-h))}' +
'.page-wrap{max-width:1400px;margin:0 auto;padding:20px 16px 32px}' +
'.search-bar-wrap{display:none;margin-bottom:16px}' +
'.search-form{' +
'  display:flex;align-items:center;background:var(--surface2);' +
'  border:1px solid var(--border);border-radius:12px;overflow:hidden;transition:border-color .2s;}' +
'.search-form:focus-within{border-color:rgba(232,25,90,.4)}' +
'.search-form input{' +
'  flex:1;background:transparent;border:none;outline:none;color:var(--text);' +
'  font-size:15px;padding:13px 16px;min-width:0;}' +
'.search-form input::placeholder{color:var(--muted)}' +
'.search-form button{' +
'  background:var(--accent);color:#fff;padding:0 18px;height:100%;min-height:50px;' +
'  display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:background .15s;}' +
'.search-form button:hover{background:var(--accent2)}' +
'.chips-wrap{' +
'  margin-bottom:20px;' +
'  -webkit-mask:linear-gradient(to right,#000 88%,transparent 100%);' +
'  mask:linear-gradient(to right,#000 88%,transparent 100%);}' +
'.chips-scroll{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;scrollbar-width:none}' +
'.chips-scroll::-webkit-scrollbar{display:none}' +
'.chip{' +
'  flex-shrink:0;padding:7px 14px;border-radius:999px;font-size:12px;font-weight:700;' +
'  background:var(--surface2);border:1px solid var(--border);color:var(--muted);' +
'  white-space:nowrap;transition:background .15s,color .15s,border-color .15s;' +
'  -webkit-tap-highlight-color:transparent;}' +
'.chip:hover{color:var(--accent2);border-color:rgba(232,25,90,.35)}' +
'.chip-active{background:var(--accent);border-color:var(--accent);color:#fff !important}' +
'.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}' +
'.card{' +
'  background:var(--surface);border-radius:var(--radius);overflow:hidden;' +
'  border:1px solid var(--border);transition:border-color .2s,transform .2s;will-change:transform;}' +
'.card:hover{border-color:rgba(232,25,90,.35);transform:translateY(-2px)}' +
'.card:active{transform:scale(.97)}' +
'.card-thumb{display:block;position:relative;aspect-ratio:9/16;overflow:hidden;background:var(--surface2)}' +
'.card-thumb img{width:100%;height:100%;object-fit:cover;transition:transform .4s}' +
'.card:hover .card-thumb img{transform:scale(1.05)}' +
'.badge-time{' +
'  position:absolute;bottom:6px;right:6px;background:rgba(0,0,0,.75);color:#fff;' +
'  font-size:10px;font-family:monospace;' +
'  padding:2px 6px;border-radius:5px;backdrop-filter:blur(4px);}' +
'.card-body{padding:10px 10px 8px}' +
'.card-title{' +
'  font-size:11px;font-weight:500;color:#ccc;' +
'  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;' +
'  overflow:hidden;line-height:1.45;min-height:32px;margin-bottom:6px;}' +
'.card-title-link{display:block;color:inherit;text-decoration:none}' +
'.card-title-link:hover .card-title{color:var(--accent2)}' +
'.card-meta{display:flex;justify-content:space-between;font-size:10px;color:var(--muted)}' +
'.fav{color:var(--accent2)}' +
'.pagination{' +
'  display:flex;align-items:center;justify-content:center;' +
'  gap:12px;padding:32px 0 8px;flex-wrap:wrap;}' +
'.page-btn{' +
'  display:inline-flex;align-items:center;padding:11px 24px;' +
'  background:var(--surface2);border:1px solid var(--border);' +
'  border-radius:10px;font-size:13px;font-weight:700;color:var(--text);' +
'  transition:background .15s,border-color .15s;-webkit-tap-highlight-color:transparent;}' +
'.page-btn:not(.disabled):hover{background:var(--accent);border-color:var(--accent)}' +
'.page-btn.disabled{opacity:.3;pointer-events:none}' +
'.page-info{font-size:12px;color:var(--muted)}' +
'.empty-state{text-align:center;padding:80px 20px}' +
'.empty-icon{font-size:48px;opacity:.25;margin-bottom:12px}' +
'.empty-text{font-size:16px;font-weight:700;color:var(--muted)}' +
'.detail-wrap{max-width:960px;margin:0 auto;padding:20px 16px 40px}' +
'.back-btn{' +
'  display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:700;' +
'  color:var(--muted);padding:8px 0;margin-bottom:16px;transition:color .15s;' +
'  -webkit-tap-highlight-color:transparent;min-height:44px;}' +
'.back-btn:hover{color:var(--accent2)}' +
'.detail-card{' +
'  background:var(--surface);border-radius:20px;overflow:hidden;' +
'  border:1px solid var(--border);}' +
'.video-wrap{' +
'  position:relative; width:100%; aspect-ratio:16/9; background:#000; overflow:hidden;' +
'}' +
'.player-shell{' +
'  position:absolute;inset:0; display:flex;align-items:center;justify-content:center; background:#000;' +
'}' +
'.main-video{' +
'  position:absolute;inset:0; width:100%;height:100%; object-fit:contain; background:#000; z-index:1;' +
'}' +
'.player-poster{' +
'  position:absolute;inset:0; display:flex;flex-direction:column; align-items:center;justify-content:center; z-index:10; background:#000; transition:opacity .4s ease;' +
'}' +
'.poster-img{' +
'  position:absolute;inset:0; width:100%;height:100%; object-fit:cover; opacity:.55;' +
'}' +
'.poster-blank{background:var(--surface2)}' +
'.big-play-btn{' +
'  position:relative;z-index:11; width:76px;height:76px;border-radius:50%; background:var(--accent);' +
'  display:flex;align-items:center;justify-content:center; padding-left:5px; box-shadow:0 6px 32px rgba(232,25,90,.55);' +
'  transition:transform .15s,background .15s; -webkit-tap-highlight-color:transparent;' +
'}' +
'.big-play-btn:hover{transform:scale(1.1);background:var(--accent2)}' +
'.big-play-btn:active{transform:scale(.95)}' +
'.player-spinner{' +
'  position:absolute;inset:0;z-index:12; display:flex;align-items:center;justify-content:center; background:rgba(0,0,0,.45);' +
'}' +
'.spinner-ring{' +
'  width:44px;height:44px;border-radius:50%; border:3px solid rgba(255,255,255,.15); border-top-color:var(--accent); animation:spin .8s linear infinite;' +
'}' +
'@keyframes spin{to{transform:rotate(360deg)}}' +
'.player-error{' +
'  position:absolute;inset:0;z-index:13; display:flex;flex-direction:column; align-items:center;justify-content:center;gap:10px; background:rgba(0,0,0,.75);color:var(--text);text-align:center;padding:20px;' +
'}' +
'.player-error span{font-size:32px}' +
'.player-error p{font-size:13px;color:var(--muted);max-width:260px}' +
'.retry-btn{' +
'  margin-top:4px;padding:9px 22px;border-radius:999px; background:var(--accent);color:#fff;font-size:13px;font-weight:700; transition:background .15s;' +
'}' +
'.retry-btn:hover{background:var(--accent2)}' +
'.no-video{' +
'  position:absolute;inset:0; display:flex;flex-direction:column; align-items:center;justify-content:center; gap:10px;color:var(--muted);font-size:14px;' +
'}' +
'.no-video span{font-size:40px;opacity:.4}' +
'.hidden{display:none !important}' +
'.detail-body{padding:20px}' +
'.detail-title{' +
'  font-size:18px; font-weight:800;line-height:1.3;margin-bottom:12px;}' +
'.detail-meta{display:flex;gap:18px;font-size:13px;color:var(--muted);margin-bottom:4px;flex-wrap:wrap}' +
'@media(min-width:540px){ .grid{grid-template-columns:repeat(3,1fr);gap:12px} .card-title{font-size:12px} }' +
'@media(min-width:768px){ .grid{grid-template-columns:repeat(4,1fr);gap:14px} .page-wrap{padding:24px 24px 40px} .detail-body{padding:24px 28px} .big-play-btn{width:88px;height:88px} }' +
'@media(min-width:1024px){ .grid{grid-template-columns:repeat(5,1fr);gap:16px} .search-bar-wrap{display:none !important} .topnav-search{display:flex} .topnav-links{display:flex} .bnav{display:none !important} .main-content{padding-bottom:0} .detail-wrap{padding:28px 24px 56px} .detail-body{padding:28px 36px} .big-play-btn{width:96px;height:96px} }' +
'@media(min-width:1280px){ .grid{grid-template-columns:repeat(6,1fr)} }' +
'@media(max-width:1023px){ .topnav-search{display:none} .topnav-links{display:none} .search-bar-wrap{display:block} .bnav{display:flex} .main-content{padding-bottom:calc(var(--bnav-h) + var(--safe-b) + 8px)} }' +
'@media(max-width:500px) and (orientation:portrait){ .video-wrap{aspect-ratio:9/16;max-height:72vw;aspect-ratio:unset;height:56vw} }' +
'</style>' +
'</head>' +
'<body>' +
'<nav class="topnav">' +
'  <a href="/zh-CN/" class="logo">OTC<span>.</span>VIDEO</a>' +
'  <div class="topnav-links">' +
     navLinks +
'  </div>' +
'</nav>' +
'<main class="main-content">' +
   content +
'</main>' +
'<nav class="bnav">' +
   bottomNav +
'</nav>' +
'</body>' +
'</html>';
}

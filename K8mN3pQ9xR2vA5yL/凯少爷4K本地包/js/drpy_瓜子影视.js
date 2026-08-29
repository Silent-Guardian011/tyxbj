
globalThis.Encrypt = function (data) {
    let key = CryptoJS.enc.Utf8.parse('obr4oAnPZ8CKofg1');
    let iv = CryptoJS.enc.Utf8.parse('bgkpMvvThGlbz8Sj');
    let encrypted = CryptoJS.AES.encrypt(data, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    });

    let encryptedHex = encrypted.ciphertext.toString(CryptoJS.enc.Hex).toUpperCase();
    return encryptedHex
};

globalThis.Decrypt = function (data, key, iv) {
    let dataObj = {ciphertext: CryptoJS.enc.Hex.parse(data)};
    let decrypt = CryptoJS.AES.decrypt(dataObj, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    });

    let decryptedStr = decrypt.toString(CryptoJS.enc.Utf8);
    return decryptedStr;
};

globalThis.gethtml = function (url, rkey, rkeys) {
    const kheaders = {
            'code': 'GZ0611',
            'Cache-Control': 'no-cache',
            'Version': '2509018',
            'PackageName': 'com.ce1d9f0136.v75e82af9f.g1b3acdbb820250930',
            'Ver': '3.0.3.2',
            'api-ver': '3.0.3.0',
            'referer': 'https://api.w32z7vtd.com',
            'X-Customer-Client-Ip': '127.0.0.1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Host': 'api.w32z7vtd.com',
            'Connection': 'Keep-Alive',
            'user-agent': 'okhttp/3.12.0'
    };
    let enkey = Encrypt(rkey);
    let timestamp = new Date().getTime()/1000;
    let t = timestamp.toString().split('.')[0];
    let sign = `token_id=,token=a9bebd5714f6aa203c0db0d7a179bfa5.f0b0a547d53d1e7d589a1d79ed9b7cd728cac9d706d2d5a9ef2d4db160ed7e3f11add16cd1402615d8be023293571250d87568bc0bb932c5050c93eb5fb5db514f4b448f491b84b93dae1d6470a09de9e48b1c821fc4343e9ab1b8e7933929b91466247c8867fcff3c074a533954be23e25d262682a201673654e0a571ffc19d163f1c0e6d8c7e069e88ec46266a22ae.9bf0b78a32b5f2525bd234bdf0487393610405424feea17c89eb54363bd95f26,phone_type=1,request_key=${enkey},app_id=1,time=${t},keys=${rkeys}*&zvdvdvddbfikkkumtmdwqppp?|4Y!s!2br`;
    let signature = md5(sign);
    let kbody = `token_id=&token=a9bebd5714f6aa203c0db0d7a179bfa5.f0b0a547d53d1e7d589a1d79ed9b7cd728cac9d706d2d5a9ef2d4db160ed7e3f11add16cd1402615d8be023293571250d87568bc0bb932c5050c93eb5fb5db514f4b448f491b84b93dae1d6470a09de9e48b1c821fc4343e9ab1b8e7933929b91466247c8867fcff3c074a533954be23e25d262682a201673654e0a571ffc19d163f1c0e6d8c7e069e88ec46266a22ae.9bf0b78a32b5f2525bd234bdf0487393610405424feea17c89eb54363bd95f26&phone_type=1&request_key=${enkey}&app_id=1&time=${t}&keys=${encodeURIComponent(rkeys)}&signature=${signature}&phone_model=vivo-v2141a&ad_version=1`;
    let khtml = fetch(url, {
        headers: kheaders,
        body: kbody,
        method: 'POST',
        rejectCoding: true
    });
    let kdata = JSON.parse(khtml).data;
    let response_key = kdata.response_key; 
    let keys = kdata.keys;
    const bodykey = 'MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGAe6hKrWLi1zQmjTT1ozbE4QdFeJGNxubxld6GrFGximxfMsMB6BpJhpcTouAqywAFppiKetUBBbXwYsYU1wNr648XVmPmCMCy4rY8vdliFnbMUj086DU6Z+/oXBdWU3/b1G0DN3E9wULRSwcKZT3wj/cCI1vsCm3gj2R5SqkA9Y0CAwEAAQKBgAJH+4CxV0/zBVcLiBCHvSANm0l7HetybTh/j2p0Y1sTXro4ALwAaCTUeqdBjWiLSo9lNwDHFyq8zX90+gNxa7c5EqcWV9FmlVXr8VhfBzcZo1nXeNdXFT7tQ2yah/odtdcx+vRMSGJd1t/5k5bDd9wAvYdIDblMAg+wiKKZ5KcdAkEA1cCakEN4NexkF5tHPRrR6XOY/XHfkqXxEhMqmNbB9U34saTJnLWIHC8IXys6Qmzz30TtzCjuOqKRRy+FMM4TdwJBAJQZFPjsGC+RqcG5UvVMiMPhnwe/bXEehShK86yJK/g/UiKrO87h3aEu5gcJqBygTq3BBBoH2md3pr/W+hUMWBsCQQChfhTIrdDinKi6lRxrdBnn0Ohjg2cwuqK5zzU9p/N+S9x7Ck8wUI53DKm8jUJE8WAG7WLj/oCOWEh+ic6NIwTdAkEAj0X8nhx6AXsgCYRql1klbqtVmL8+95KZK7PnLWG/IfjQUy3pPGoSaZ7fdquG8bq8oyf5+dzjE/oTXcByS+6XRQJAP/5ciy1bL3NhUhsaOVy55MHXnPjdcTX0FaLi+ybXZIfIQ2P4rb19mVq1feMbCXhz+L1rG8oat5lYKfpe8k83ZA==';
    let bodykeyiv = JSON.parse(RSA.decode(keys, bodykey));
    let key = CryptoJS.enc.Utf8.parse(bodykeyiv.key);
    let iv = CryptoJS.enc.Utf8.parse(bodykeyiv.iv);
    khtml = Decrypt(response_key, key, iv);
    return khtml
};

var rule = {
author: '小可乐/2503/第一版',
title: '瓜子app',
类型: '影视',
host: 'https://api.w32z7vtd.com',
hostJs: '',
headers: {'User-Agent': 'MOBILE_UA'},
编码: 'utf-8',
timeout: 5000,

homeUrl: '/',
url: '/App/IndexList/indexList',
filter_url: '',
detailUrl: '',
searchUrl: '/App/Index/findMoreVod',
tab_rename:{'480':'🐾茶鱼┃标清','720':'🐾茶鱼┃高清','1080':'🐾茶鱼┃超清'},
limit: 9,
double: false,
class_name: '电影&剧集&综艺&动漫&短剧',
class_url: '1&2&3&4&64',
filter_def: {},
推荐: $js.toString(() => {
let rkey = JSON.stringify({
     "pageSize": 30,
     "sort": "d_id",
     "page": 1,
     "tid": 2
});
let rkeys = 'igkYlHLxws+ZnxiYPIq1FKCM9281bT0jgq1KmjFAF8OaQUKQ8mNMbRsng9wgTftu87SChLcwfb09n31hd4isthTLHvORUSqL8jfMc9dgEzLokH+ptbi4fHeh8bMVwlJCC8r1j8UCcn+sNGXP5HCZPy/mvpovL6YlQpIoqRS9rUM=';
let khtml = gethtml(`${HOST}/App/IndexList/indexList`, rkey, rkeys);
VODS = [];
let klist = JSON.parse(khtml).list;
klist.map((it) => {
    VODS.push({
        vod_name: it.vod_name,
        vod_pic: it.vod_pic,
        vod_remarks: it.vod_continu == 0 ? '电影' : '更新至'+it.vod_continu+'集',
        vod_id: `${it.vod_id}/${it.vod_continu}`
    })
})
}),
一级: $js.toString(() => {
let subs = {'1': '1', '2': '2', '3': '22', '4': '4', '64': ''};
let sub = subs[MY_CATE] || ''; 
let tid = MY_CATE;
let rkey = JSON.stringify({
    "tid": tid,
    "sub": (MY_FL.cateId || MY_CATE).toString(),
    "area": (MY_FL.area || "").toString(),
    "year": (MY_FL.year || "").toString(),
    "sort": (MY_FL.by || "d_id").toString(),
    "pageSize": "30",
    "page": MY_PAGE
});
let rkeys = 'igkYlHLxws+ZnxiYPIq1FKCM9281bT0jgq1KmjFAF8OaQUKQ8mNMbRsng9wgTftu87SChLcwfb09n31hd4isthTLHvORUSqL8jfMc9dgEzLokH+ptbi4fHeh8bMVwlJCC8r1j8UCcn+sNGXP5HCZPy/mvpovL6YlQpIoqRS9rUM=';
let khtml = gethtml(input, rkey, rkeys);
VODS = [];
let klist = JSON.parse(khtml).list;
klist.map((it) => {
    VODS.push({
        vod_name: it.vod_name,
        vod_pic: it.vod_pic,
        vod_remarks: it.vod_continu == 0 ? '电影' : '更新至'+it.vod_continu+'集',
        vod_id: `${it.vod_id}/${it.vod_continu}`
    })
})
}),
二级: $js.toString(() => {
let vod_id = input.split('/')[3];
let timestamp = new Date().getTime()/1000;
let t = timestamp.toString().split('.')[0];
let rkey = JSON.stringify({
    "token_id": "393668",
    "vod_id": vod_id,
    "mobile_time": t,
    "token": "a9bebd5714f6aa203c0db0d7a179bfa5.f0b0a547d53d1e7d589a1d79ed9b7cd728cac9d706d2d5a9ef2d4db160ed7e3f11add16cd1402615d8be023293571250d87568bc0bb932c5050c93eb5fb5db514f4b448f491b84b93dae1d6470a09de9e48b1c821fc4343e9ab1b8e7933929b91466247c8867fcff3c074a533954be23e25d262682a201673654e0a571ffc19d163f1c0e6d8c7e069e88ec46266a22ae.9bf0b78a32b5f2525bd234bdf0487393610405424feea17c89eb54363bd95f26"
});
let rkeys = 'igkYlHLxws+ZnxiYPIq1FKCM9281bT0jgq1KmjFAF8OaQUKQ8mNMbRsng9wgTftu87SChLcwfb09n31hd4isthTLHvORUSqL8jfMc9dgEzLokH+ptbi4fHeh8bMVwlJCC8r1j8UCcn+sNGXP5HCZPy/mvpovL6YlQpIoqRS9rUM=';
let khtml = gethtml(`${HOST}/App/IndexPlay/playInfo`, rkey, rkeys);
let kvod = JSON.parse(khtml).vodInfo;
let rkey2 = JSON.stringify({
    "vurl_cloud_id": "2",
    "vod_d_id": vod_id
});
let khtml2 = gethtml(`${HOST}/App/Resource/Vurl/show`, rkey2, rkeys);
let klist = JSON.parse(khtml2).list;

let lineNames = new Set();
klist.forEach(item => {
    Object.keys(item.play).forEach(resolution => {
        if (item.play[resolution].param) {
            lineNames.add(resolution);
        }
    });
});

let linePlayUrls = [];
let validLineNames = [];

lineNames.forEach(lineName => {
    let lineEpisodes = [];
    let hasValidEpisodes = false;
    
    klist.forEach(item => {
        const playData = item.play[lineName];
        if (playData && playData.param) {
            let vurlIdMatch = playData.param.match(/vurl_id=(\d+)/);
            let resolutionMatch = playData.param.match(/resolution=(\d+)/);
            if (vurlIdMatch) {
                let resolution = resolutionMatch ? resolutionMatch[1] : lineName;
                lineEpisodes.push(`${item.title}$${vod_id}/${vurlIdMatch[1]}?${resolution}`);
                hasValidEpisodes = true;
            }
        }
    });

    if (hasValidEpisodes && lineEpisodes.length > 0) {
        linePlayUrls.push(lineEpisodes.join('#'));
        validLineNames.push(lineName);
    }
});

VOD = {
    vod_id: vod_id,
    vod_name: kvod.vod_name,
    vod_pic: kvod.vod_pic,
    type_name: kvod.videoTag.toString(),
    vod_remarks: kvod.vod_remarks,
    vod_year: kvod.vod_year,
    vod_area: kvod.vod_area,
    vod_actor: kvod.vod_actor,
    vod_director: kvod.vod_director,
    vod_content: kvod.vod_use_content,
    vod_play_from: validLineNames.join('$$$'),
    vod_play_url: linePlayUrls.join('$$$')
}

}),
搜索: $js.toString(() => {
let url = input;
let rkey = JSON.stringify({
    'keywords': KEY,
    'order_val': 1
});
let rkeys = 'igkYlHLxws+ZnxiYPIq1FKCM9281bT0jgq1KmjFAF8OaQUKQ8mNMbRsng9wgTftu87SChLcwfb09n31hd4isthTLHvORUSqL8jfMc9dgEzLokH+ptbi4fHeh8bMVwlJCC8r1j8UCcn+sNGXP5HCZPy/mvpovL6YlQpIoqRS9rUM=';
let khtml = gethtml(url, rkey, rkeys);
VODS = [];
let klist = JSON.parse(khtml).list;
klist.map((it) => {
    VODS.push({
        vod_name: it.vod_name,
        vod_pic: it.vod_pic,
        vod_remarks: it.vod_continu == 0 ? '电影' : '更新至'+it.vod_continu+'集',
        vod_id: `${it.vod_id}/${it.vod_continu}`
    })
})
}),

play_parse: true,
lazy: $js.toString(() => {
let vod_id = input.split('/')[0];
let vurl_id = input.split('/')[1];
let resolution=input.split('?')[1];
let rkey = JSON.stringify({
    "domain_type": 8,
    "vod_id": vod_id,
    "type": "play",
    "resolution": resolution,
    "vurl_id": vurl_id
}); 
let rkeys = 'igkYlHLxws+ZnxiYPIq1FKCM9281bT0jgq1KmjFAF8OaQUKQ8mNMbRsng9wgTftu87SChLcwfb09n31hd4isthTLHvORUSqL8jfMc9dgEzLokH+ptbi4fHeh8bMVwlJCC8r1j8UCcn+sNGXP5HCZPy/mvpovL6YlQpIoqRS9rUM=';
let khtml = gethtml(`${HOST}/App/Resource/VurlDetail/showOne`, rkey, rkeys);
let kurl = JSON.parse(khtml).url;
input = { parse: 0, url: kurl, header: rule.headers }
}),

filter: 'H4sIAAAAAAAAA+1Xy07bQBTd5ysqr11p/Eom/EG/AaHKJVmgtlSitBJCkaA8moRCoCoJj9CHCiSBIIJKCzgk/IxnTP6ic4PtO3alqioLNl7kRvcc3zN3XifObErRlJHR1KzyPD+jjCjj9nT+SU5RlUn7ZV7k3lmXfV4R+Vv7xRsBjM4qkwJmS83BQhNgkWhKQfXhctPt1b3Se5+xQoa/a3vVDWT0LBZV66zUQCodMl7xjC8sIZNBprHBrrrIUBxofp3PVZGRxik1ImoawaLiluuUJCoyJe+TNJIhteccsd6mNCcU9Ob7g52+VIUNeuVTr3ckTVeMNVZQwx2wp/I2rj+rd9gH5+/rj73uNwbbyz7qJwE3ONzml6c+5ydhXaXDr/pB3V0SLk274fXXfM69WfR6NV49VVn5K1+5EWOorH/BdnsqX6yIjBVbKv+xOQSGhar4QHa7cjb8OrjxKideaRv1awe83vb1/STs+UtLFAU93yUB517W2WrNdXaCtlc7zDlUebUjWmN730QbHRhx0GrzvQMxLjwaTnjpl9utBpV3SWQTZvL2lLQJV+dut/ePm6AT3QoPhG7JuIm4KeMG4oaM64jrMq4hrsk4QZxIuJYNcS0r4xRxKuMZxDMynkYcb4FGHmuWWCHkLFUEE4IBQYegQcCmCBmu6fewiBDxAIGnCDxPoJKABgE1koaQgUAh4CyyUSEtmyWqCBoEHYIBwYRgQUhDyECgEFCIxoUoCFEQoiBEQYiCEAUhCkIUhCgIURTiu+e81gomFj1Wz2bwUPG1j8yp/HGovO41Wy/65bmnEzkUrs+J0x0ydi43PSGUJNpbOAnp1+OvppAcHG+x4nKcHCukxtSUaPKePwB4OMWNc52GcNpgGfWYAUmUEfMfiTJj9iNRVsw5JCodMw6JwmPMf16w/apEST8dQ8eQKGlTA1sJTDubmHZi2olpJ6b9UKZt/I9pD91FNHtbcoK54hkFd650oqwhX3lxmaNs3KajrJVYZGKRiUUmFvlQFmne973WlG7lCbwalpv8+jj4S09idz3K4gF+5L/DRmgjMcfEHBNzTMzxQcwxVfgNyDRXOfgVAAA='
}
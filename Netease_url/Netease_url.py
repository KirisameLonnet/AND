import json
import os
import urllib.parse
from hashlib import md5
from random import randrange
import requests
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import argparse

def HexDigest(data):
    return "".join([hex(d)[2:].zfill(2) for d in data])

def HashDigest(text):
    HASH = md5(text.encode("utf-8"))
    return HASH.digest()

def HashHexDigest(text):
    return HexDigest(HashDigest(text))

def parse_cookie(text: str):
    cookie_ = [item.strip().split('=', 1) for item in text.strip().split(';') if item]
    cookie_ = {k.strip(): v.strip() for k, v in cookie_}
    return cookie_

def read_cookie():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cookie_file = os.path.join(script_dir, 'cookie.txt')
    with open(cookie_file, 'r') as f:
        cookie_contents = f.read()
    return cookie_contents

def post(url, params, cookie):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154',
        'Referer': '',
    }
    cookies = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!"
    }
    cookies.update(cookie)
    response = requests.post(url, headers=headers, cookies=cookies, data={"params": params})
    return response.text

def ids(ids):
    if '163cn.tv' in ids:
        response = requests.get(ids, allow_redirects=False)
        ids = response.headers.get('Location')
    if 'music.163.com' in ids:
        index = ids.find('id=') + 3
        ids = ids[index:].split('&')[0]
    return ids

def size(value):
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    size = 1024.0
    for i in range(len(units)):
        if (value / size) < 1:
            return "%.2f%s" % (value, units[i])
        value = value / size
    return value

def music_level1(value):
    if value == 'standard':
        return "标准音质"
    elif value == 'exhigh':
        return "极高音质"
    elif value == 'lossless':
        return "无损音质"
    elif value == 'hires':
        return "Hires音质"
    elif value == 'sky':
        return "沉浸环绕声"
    elif value == 'jyeffect':
        return "高清环绕声"
    elif value == 'jymaster':
        return "超清母带"
    else:
        return "未知音质"

def url_v1(id, level, cookies):
    url = "https://interface3.music.163.com/eapi/song/enhance/player/url/v1"
    AES_KEY = b"e82ckenh8dichen8"
    config = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!",
        "requestId": str(randrange(20000000, 30000000))
    }

    payload = {
        'ids': [id],
        'level': level,
        'encodeType': 'flac',
        'header': json.dumps(config),
    }

    if level == 'sky':
        payload['immerseType'] = 'c51'
    
    url2 = urllib.parse.urlparse(url).path.replace("/eapi/", "/api/")
    digest = HashHexDigest(f"nobody{url2}use{json.dumps(payload)}md5forencrypt")
    params = f"{url2}-36cd479b6b5-{json.dumps(payload)}-36cd479b6b5-{digest}"
    padder = padding.PKCS7(algorithms.AES(AES_KEY).block_size).padder()
    padded_data = padder.update(params.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(AES_KEY), modes.ECB())
    encryptor = cipher.encryptor()
    enc = encryptor.update(padded_data) + encryptor.finalize()
    params = HexDigest(enc)
    response = post(url, params, cookies)
    return json.loads(response)

def name_v1(id):
    urls = "https://interface3.music.163.com/api/v3/song/detail"
    data = {'c': json.dumps([{"id":id,"v":0}])}
    response = requests.post(url=urls, data=data)
    return response.json()

def lyric_v1(id,cookies):
    url = "https://interface3.music.163.com/api/song/lyric"
    data = {'id' : id,'cp' : 'false','tv' : '0','lv' : '0','rv' : '0','kv' : '0','yv' : '0','ytv' : '0','yrv' : '0'}
    response = requests.post(url=url, data=data, cookies=cookies)
    return response.json()

def main(song_ids, level, type_):
    cookies = parse_cookie(read_cookie())
    urlv1 = url_v1(ids(song_ids), level, cookies)
    namev1 = name_v1(urlv1['data'][0]['id'])
    lyricv1 = lyric_v1(urlv1['data'][0]['id'], cookies)
    
    if urlv1['data'][0]['url'] is not None:
        song_url = urlv1['data'][0]['url']
        song_name = namev1['songs'][0]['name']
        song_picUrl = namev1['songs'][0]['al']['picUrl']
        song_alname = namev1['songs'][0]['al']['name']
        artist_names = []
        for song in namev1['songs']:
            ar_list = song['ar']
            if len(ar_list) > 0:
                artist_names.append('/'.join(ar['name'] for ar in ar_list))
            song_arname = ', '.join(artist_names)
    else:
        print("信息获取不完整！")
        return

    if type_ == 'text':
        data = f"歌曲名称：{song_name}\n歌曲图片：{song_picUrl}\n歌手：{song_arname}\n歌曲专辑：{song_alname}\n歌曲音质：{music_level1(urlv1['data'][0]['level'])}\n歌曲大小：{size(urlv1['data'][0]['size'])}\n音乐地址：{song_url}"
        print(data)
    elif type_ == 'down':
        print(f"下载地址：{song_url}")
    elif type_ == 'json':
        data = {
            "status": 200,
            "name": song_name,
            "pic": song_picUrl,
            "ar_name": song_arname,
            "al_name": song_alname,
            "level": music_level1(urlv1['data'][0]['level']),
            "size": size(urlv1['data'][0]['size']),
            "url": song_url.replace("http://", "https://", 1),
            "lyric": lyricv1.get('lrc', {}).get('lyric', '无歌词'),
            "tlyric": lyricv1.get('tlyric', {}).get('lyric', '无翻译歌词')
        }
        print(json.dumps(data, indent=4))
    else:
        print("解析失败！请检查参数是否完整！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="网易云音乐工具")
    parser.add_argument('ids', help="歌曲ID或URL")
    parser.add_argument('level', help="音质级别")
    parser.add_argument('type', help="输出类型 (text, down, json)")
    
    args = parser.parse_args()
    
    main(args.ids, args.level, args.type)

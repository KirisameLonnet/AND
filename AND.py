import csv
import requests
import subprocess
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC

# 网易云搜索API
def search_song(song_title, artist_name):
    search_url = f'https://music.163.com/api/search/get'

    params = {
        's': f"{song_title} {artist_name}",
        'type': 1,
        'limit': 1,
        'offset': 0,
        'csrf_token': ''
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    response = requests.get(search_url, params=params, headers=headers)
    response_data = response.json()

    if response_data.get('result') and response_data['result'].get('songs'):
        song = response_data['result']['songs'][0]
        song_id = song['id']
        song_name = song['name']
        artist_name = song['artists'][0]['name']
        return (song_id, song_name, artist_name)
    else:
        return None

# 下载歌曲
def download_song(song_id, level='lossless', type_='down'):
    netease_url_path = os.path.join(os.getcwd(), 'Netease_url', 'Netease_url.py')
    cmd = f"python {netease_url_path} {song_id} {level} {type_}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # 获取链接
    download_url = result.stdout.strip()
    
    if download_url.startswith("下载地址："):
        download_url = download_url.replace("下载地址：", "").strip()
    
    return download_url

# 保存歌曲
def save_song(song_url, song_name, artist_name, album_name):
    safe_song_name = song_name.replace('/', '_') 
    safe_artist_name = artist_name.replace('/', '_')
    song_filename = f"{safe_artist_name} - {safe_song_name}.mp3"
    song_path = os.path.join(os.getcwd(), "Downloads", song_filename)
    
    # 请求下载歌曲
    response = requests.get(song_url, stream=True)
    if response.status_code == 200:
        with open(song_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"下载完成: {song_filename}")
        # 更新元数据
        update_metadata(song_path, song_name, artist_name, album_name)
    else:
        print(f"下载失败: {song_filename}")

# 更新歌曲元数据
def update_metadata(file_path, title, artist, album):
    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=title))  # 标题
        audio.tags.add(TPE1(encoding=3, text=artist))  # 艺术家
        audio.tags.add(TALB(encoding=3, text=album))  # 专辑
        # 可以添加更多元数据，比如流派 (TCON)，年份 (TDRC)
        audio.save()
        print(f"元数据已更新: {file_path}")
    except Exception as e:
        print(f"更新元数据时出错: {e}")

# 读csv
def process_csv(csv_file, quality):
    not_found_songs = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            song_title = row['Track name']
            artist_name = row['Artist name']
            album_name = row.get('Album', 'Unknown Album')
            print(f"正在搜索: {song_title} - {artist_name}")
            song_info = search_song(song_title, artist_name)
            if song_info:
                song_id, song_name, artist_name = song_info
                print(f"找到歌曲: {song_name} - {artist_name}")
                
                # 获取下载链接
                download_url = download_song(song_id, quality)
                if download_url:
                    print(f"下载地址：{download_url}")
                    save_song(download_url, song_name, artist_name, album_name)  # 下载
                else:
                    print(f"未能获取到下载链接: {song_name}")
            else:
                print(f"未找到歌曲: {song_title} - {artist_name}")
                not_found_songs.append({
                    'Track name': song_title,
                    'Artist name': artist_name,
                    'Album': row['Album'],
                    'Playlist name': row['Playlist name'],
                    'Type': row['Type'],
                    'ISRC': row['ISRC']
                })
    
    # 没找到的歌导出csv
    if not_found_songs:
        with open('not_found_songs.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Track name', 'Artist name', 'Album', 'Playlist name', 'Type', 'ISRC', 'Apple - id']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(not_found_songs)
        print(f"未找到的歌曲已保存到 'not_found_songs.csv'")

if __name__ == "__main__":
    # 设置音质选择
    quality = 'hires'  # 默认音质选择，可以修改为其他音质
    csv_file = 'playlist.csv'  # csv文件路径，自己替换
    process_csv(csv_file, quality)

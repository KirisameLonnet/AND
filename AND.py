import csv
import requests
import subprocess
import os

# 检查歌曲是否已下载
def is_song_downloaded(song_name, artist_name):
    safe_song_name = song_name.replace('/', '_') 
    safe_artist_name = artist_name.replace('/', '_')
    song_filename = f"{safe_artist_name} - {safe_song_name}.mp3"
    song_path = os.path.join(os.getcwd(), "Downloads", song_filename)
    
    # 文件存在
    return os.path.exists(song_path)

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

# 下载
def download_song(song_id, level='lossless', type_='down'):
    netease_url_path = os.path.join(os.getcwd(), 'Netease_url', 'Netease_url.py')
    cmd = f"python {netease_url_path} {song_id} {level} {type_}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    # 获取下载链接
    download_url = result.stdout.strip()
    
    if download_url.startswith("下载地址："):
        download_url = download_url.replace("下载地址：", "").strip()

        # 检查下载链接是否有效
        if download_url.startswith('http') and '.' in download_url:
            return download_url
        else:
            print(f"无效下载地址: {download_url}")
            return None
    else:
        print("未能获取到下载地址！")
        return None


# 保存歌曲
def save_song(song_url, song_name, artist_name):
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
    else:
        print(f"下载失败: {song_filename}")

# 读取 CSV 并处理每一行
def process_csv(csv_file, quality):
    not_found_songs = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            song_title = row['Track name']
            artist_name = row['Artist name']
            print(f"正在搜索: {song_title} - {artist_name}")
            
            # 如果歌曲已经下载过，跳过
            if is_song_downloaded(song_title, artist_name):
                print(f"歌曲已下载，跳过: {song_title} - {artist_name}")
                continue

            song_info = search_song(song_title, artist_name)
            if song_info:
                song_id, song_name, artist_name = song_info
                print(f"找到歌曲: {song_name} - {artist_name}")
                
                # 获取下载链接
                download_url = download_song(song_id, quality)
                if download_url:
                    print(f"下载地址：{download_url}")
                    save_song(download_url, song_name, artist_name)  # 下载
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
                    'ISRC': row['ISRC'],
                    'Apple - id': row['Apple - id']
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
    # 设置音质选择，参考 https://github.com/Suxiaoqinx/Netease_url 的音质说明
    '''
    standard(标准音质), exhigh(极高音质), lossless(无损音质), hires(Hi-Res音质), jyeffect(高清环绕声), sky(沉浸环绕声), jymaster(超清母带)

    黑胶VIP音质选择 standard, exhigh, lossless, hires, jyeffect
    黑胶SVIP音质选择 sky, jymaster
    '''
    quality = 'hires'  # 默认音质选择，可以修改为其他音质
    csv_file = 'playlist.csv'  # csv文件路径，自己替换
    process_csv(csv_file, quality)

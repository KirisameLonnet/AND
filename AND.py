import csv
import requests
import subprocess
import os
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, TDRC

# 日志
def print_log(message, level="INFO"):
    print(f"[{level}] {message}")


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

    try:
        response = requests.get(search_url, params=params, headers=headers)
        response_data = response.json()
        if response_data.get('result') and response_data['result'].get('songs'):
            song = response_data['result']['songs'][0]
            song_id = song['id']
            song_name = song['name']
            artist_name = song['artists'][0]['name']
            return song_id, song_name, artist_name
        else:
            return None
    except Exception as e:
        print_log(f"搜索歌曲时出错: {e}", "ERROR")
        return None


# 下载歌曲
def download_song(song_id, level='lossless', type_='down'):
    netease_url_path = os.path.join(os.getcwd(), 'Netease_url', 'Netease_url.py')
    cmd = f"python {netease_url_path} {song_id} {level} {type_}"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        download_url = result.stdout.strip()
        if download_url.startswith("下载地址："):
            download_url = download_url.replace("下载地址：", "").strip()
        return download_url
    except subprocess.CalledProcessError as e:
        print_log(f"获取下载链接失败: {e}", "ERROR")
        return None


# 保存歌曲
def save_song(song_url, song_name, artist_name, album_name, not_found_songs, row):
    safe_song_name = song_name.replace('/', '_')
    safe_artist_name = artist_name.replace('/', '_')
    song_filename = f"{safe_artist_name} - {safe_song_name}.mp3"
    song_path = os.path.join(os.getcwd(), "Downloads", song_filename)

    # 检查是否已下载
    if os.path.exists(song_path):
        print_log(f"文件已存在，跳过下载: {song_path}", "WARNING")
        return

    try:
        response = requests.get(song_url, stream=True)
        if response.status_code == 200:
            with open(song_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print_log(f"下载完成: {song_filename}")

            # 检查音频时长
            audio = MP3(song_path)
            if audio.info.length < 60:  # 时长小于1分钟
                print_log(f"歌曲时长小于1分钟，删除: {song_filename}", "WARNING")
                os.remove(song_path)
                not_found_songs.append(row)
            else:
                update_metadata(song_path, song_name, artist_name, album_name)
        else:
            print_log(f"下载失败（状态码: {response.status_code}）: {song_filename}", "ERROR")
            not_found_songs.append(row)
    except Exception as e:
        print_log(f"下载过程中出错: {e}", "ERROR")
        not_found_songs.append(row)


# 更新歌曲元数据
def update_metadata(file_path, title, artist, album):
    try:
        audio = MP3(file_path, ID3=ID3)
        if audio.tags is None:
            audio.add_tags()
        audio.tags.add(TIT2(encoding=3, text=title))  # 标题
        audio.tags.add(TPE1(encoding=3, text=artist))  # 艺术家
        audio.tags.add(TALB(encoding=3, text=album))  # 专辑
        audio.save()
        print_log(f"元数据已更新: {file_path}")
    except Exception as e:
        print_log(f"更新元数据时出错: {e}", "ERROR")


# 处理CSV
def process_csv(csv_file, quality):
    not_found_songs = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            song_title = row['Track name']
            artist_name = row['Artist name']
            album_name = row.get('Album', 'Unknown Album')
            print_log(f"正在搜索: {song_title} - {artist_name}")
            song_info = search_song(song_title, artist_name)
            if song_info:
                song_id, song_name, artist_name = song_info
                print_log(f"找到歌曲: {song_name} - {artist_name}")
                download_url = download_song(song_id, quality)
                if download_url:
                    print_log(f"下载地址: {download_url}")
                    save_song(download_url, song_name, artist_name, album_name, not_found_songs, row)
                else:
                    print_log(f"未能获取到下载链接: {song_name}", "WARNING")
                    not_found_songs.append(row)
            else:
                print_log(f"未找到歌曲: {song_title} - {artist_name}", "WARNING")
                not_found_songs.append(row)

    # 导出未找到的歌曲
    if not_found_songs:
        with open('not_found_songs.csv', 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Track name', 'Artist name', 'Album', 'Playlist name', 'Type', 'ISRC', 'Apple - id']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(not_found_songs)
        print_log("未找到的歌曲已保存到 'not_found_songs.csv'")


if __name__ == "__main__":
    quality = 'hires'  # 音质设置
    csv_file = 'playlist.csv'
    process_csv(csv_file, quality)

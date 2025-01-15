# AND - AppleMusic 2 Netease Downloader

通过从TuneMyMusic导出的CSV文件批量下载网易云音乐中的歌曲。A tool to batch download music from Netease Cloud based on playlists exported from TuneMyMusic CSV files.

此脚本用于从 [www.tunemymusic.com](https://www.tunemymusic.com) 获取的音乐软件歌单 CSV 文件中下载对应的音乐，并且能够处理不同的音质选择，未找到的歌曲会被记录到一个新的 CSV 文件中。

> *或许也可以下载别的平台的，不是apple music专用，只是我的使用需求是apple music，只要是tunemymusic.com能导出csv的大概都可以*

## 使用方法

1. **获取歌单 CSV 文件**  
   请访问 [www.tunemymusic.com](https://www.tunemymusic.com)，将您的歌单导出为 CSV 文件。导出的文件会包含以下列信息：  
   `Track name`（歌曲名），`Artist name`（歌手名），`Album`（专辑名），`Playlist name`（歌单名），`Type`（类型），`ISRC`（国际标准录音代码），`Apple - id`（Apple Music ID）。  
   
2. **放置 CSV 文件**  
   将获取到的 CSV 文件命名为 `playlist.csv` 并放置在脚本目录中。

3. **激活虚拟环境**

    激活虚拟环境的方法取决于您使用的操作系统：

    *Windows*： 在命令行中执行：
    ```bash
    .\venv\Scripts\activate
    ```
    或者
    ```bash
    venv\Scripts\activate.bat
    ```
    *macOS / Linux*： 在终端中执行：
    ```bash
    source venv/bin/activate
    ```
    要退出虚拟环境，只需输入：
    ```bash
    deactivate
    ```
3. **运行脚本**
    ```bash
    python3 AND.py
    ```
    音乐文件会以 歌手名 - 歌曲名.mp3 的格式保存在 Downloads 目录下，未保存的音乐会在项目根目录生成 *not_found_songs.csv*
    # 说明
    这个项目修改了
    [Netease_url](https://github.com/Suxiaoqinx/Netease_url) ，其提供了一个可以通过网易云音乐的歌曲 ID 下载音乐的工具，在此项目中改为使用纯cmdline交互而非原项目中的网页交互

    > 请参考 [Netease_url](https://github.com/Suxiaoqinx/Netease_url) 的原始项目，了解详细的原始功能与用法。

import os
import yaml
import re
import requests
from flask import Flask, render_template, send_from_directory, jsonify
from utils.mcclient import QueryClient
import sqlite3
import time
from threading import Thread, Event
import schedule
import json
app = Flask(__name__)
app.template_folder = 'templates'

with open('config.yml', encoding='utf8') as f:
    conf = yaml.load(f.read(), Loader=yaml.FullLoader)

mc_show_info = conf['server']['show-info']
mc_host = conf['server']['host']
mc_port = conf['server']['port']
mc_query = conf['server']['query']
mc_name = conf['server']['name']
mc_logo = conf['server']['logo']
mc_preview_title = conf['server']['preview']['title']
mc_preview_descr = conf['server']['preview']['descr']
mc_preview_images = conf['server']['preview']['images']
join_content = conf['server']['contact']['content']

config_motd = conf['server']['motd']
config_external_host = conf['server']['external-host']
config_favicon = conf['server']['favicon']
page_footer_content = conf['server']['footer']['content']


host = conf['web']['host']
port = conf['web']['port']
# for Minecraft Java servers (needs to be enabled on the server)
query_client = QueryClient(mc_host, port=mc_query)

# 定义一个标志来控制后台任务
stop_event = Event()

@ app.route('/assets/<path:filename>')
def serve_static(filename):
    return send_from_directory('assets', filename)

# @ app.route('/images/<path:filename>')
# def serve_images(filename):
#     return send_from_directory('images', filename)

@ app.route('/')
def home():
    offline = False
    try:
        res = query_client.get_status()
    except TimeoutError:
        offline = True
    if not offline:
        if config_motd:
            cleaned_motd = config_motd
        else:
            cleaned_motd = re.sub(r'§[a-f0-9klmnor]', '', res.motd)
            cleaned_motd = re.sub(r'[^a-zA-Z0-9\s]', '', cleaned_motd)
        player_list = []
        for player in res.players.list:

            # try:
            #     data = requests.get(f'https://playerdb.co/api/player/minecraft/{player}', timeout=5).json()
            #     if data['success']:
            #         uuid = data['data']['player']['id']
            #         img = f'https://crafatar.com/renders/head/{uuid}'
            #     else:
            #         img = 'https://crafatar.com/renders/head/aaaaaaaa-cf6b-4485-bef9-3957e7b7f509'
            # except requests.exceptions.ReadTimeout:
            #     img = 'https://crafatar.com/renders/head/aaaaaaaa-cf6b-4485-bef9-3957e7b7f509'
            # 调接口也太慢了吧，上缓存
            img = get_player_head_pic(player)
            player_list.append({'name': player, 'img': img})

        return render_template('index.html',
                            name = mc_name,
                            favicon = config_favicon,
                            external_host = config_external_host,
                            show_info = mc_show_info,
                            motd = cleaned_motd,
                            current = len(res.players.list),
                            maxp = res.players.max,
                            logo = mc_logo,
                            preview_title = mc_preview_title,
                            preview_descr = mc_preview_descr,
                            preview_images = mc_preview_images,
                            join_content = join_content,
                            player_list = player_list,
                            offline = offline,
                            footer_content = page_footer_content)
    else:
        return render_template('index.html',
                            name = mc_name,
                            favicon = config_favicon,
                            external_host = config_external_host,
                            show_info = mc_show_info,
                            logo = mc_logo,
                            preview_title = mc_preview_title,
                            preview_descr = mc_preview_descr,
                            preview_images = mc_preview_images,
                            join_content = join_content,
                            offline = offline,
                            footer_content = page_footer_content)
        

    
# 获取玩家人数历史记录的接口
@app.route('/api/player_count_history', methods=['GET'])
def player_count_history():
    c.execute('SELECT * FROM server_population ORDER BY "timestamp" DESC LIMIT 0,2016')
    data = c.fetchall()

    data_dict = {item[0]: item[1] for item in data}
    return jsonify(data_dict)
@app.errorhandler(404)
def show_404_page(e):
    return render_template('404.html'), 404

def get_player_head_pic(name):
    cache_file = 'player_head_pic_cache.json'
    try:
        with open(cache_file, 'r') as file:
            cache = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {}
    
    # 检查缓存中是否已有该玩家的记录
    if name in cache:
        return cache[name]
    
    try:
        data = requests.get(f'https://playerdb.co/api/player/minecraft/{name}', timeout=5).json()
        if data['success']:
            uuid = data['data']['player']['id']
            img = f'https://crafatar.com/renders/head/{uuid}'
        else:
            img = 'https://crafatar.com/renders/head/aaaaaaaa-cf6b-4485-bef9-3957e7b7f509'
    except requests.exceptions.ReadTimeout:
        img = 'https://crafatar.com/renders/head/aaaaaaaa-cf6b-4485-bef9-3957e7b7f509'
    
    cache[name] = img
    with open(cache_file, 'w') as file:
        json.dump(cache, file)
    
    return img
# 获取 Minecraft 服务器的玩家人数
def get_player_count():
    offline = False
    try:
        res = query_client.get_status()
    except TimeoutError:
        offline = True
    if not offline:
        return len(res.players.list)
    else:
        return 0

# 将玩家人数保存到数据库
def save_player_count():
    player_count = get_player_count()
    print(f"玩家人数: {player_count}")
    c.execute("INSERT INTO server_population (timestamp, player_count) VALUES (CURRENT_TIMESTAMP, ?)", (player_count,))
    conn.commit()


# 后台任务，每分钟检查一次玩家人数
def background_task():
    schedule.every(5).minutes.do(save_player_count)
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # 初始化 SQLite 数据库
    conn = sqlite3.connect('minecraft_server_data.db', check_same_thread=False)
    c = conn.cursor()

    # 创建表
    c.execute('''CREATE TABLE IF NOT EXISTS server_population
                (timestamp DATETIME, player_count INTEGER)''')
    conn.commit()

    # 启动后台任务
    task = Thread(target=background_task, args=(stop_event,))
    task.start()

    try:
        app.run(host, port)
        pass
    finally:
        # 设置标志以停止后台任务
        stop_event.set()
        print('接受到停止命令，正在停止后台任务...')
        # 等待后台任务完成
        task.join()
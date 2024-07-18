async function updateChatHistoryData() {
    const response = await fetch('https://mcserver-api.757678.xyz/user/msg');
    let data = await response.json();
    data = data.slice(0, 20); // 只使用前20条数据
    const playerNames = new Set(data.map(item => item.playername));
    const playerHeadPics = await fetchPlayerHeadPics(playerNames);

    let chatHistoryHTML = '';
    data.forEach((item, index) => {
        const headPic = playerHeadPics[item.playername] || 'default_head_pic.jpg';
        chatHistoryHTML += `<p class="chat-item" style="${index >= 5 ? 'display: none;' : ''}"><img src="${headPic}" height="20px"> <strong>${item.playername}</strong>: ${item.msg} <span id="history_msg_info">(ID:${item.id} | time:${item.time})</span></p>`;
    });

    if (data.length > 5) {
        chatHistoryHTML += `<p id="watchmore">查看更多（${data.length - 5}）</p>`;
    }

    document.getElementById('chat_history').innerHTML = chatHistoryHTML;

    const watchMore = document.getElementById('watchmore');
    if (watchMore) {
        watchMore.addEventListener('click', () => {
            const hiddenItems = document.querySelectorAll('.chat-item[style*="display: none;"], .chat-item[style*="display: block;"]');
            hiddenItems.forEach(item => {
                item.style.display = item.style.display === 'none' ? 'block' : 'none';
            });
            watchMore.textContent = watchMore.textContent.includes('查看更多') ? '折叠' : `查看更多（${data.length - 5}）`;
        });
    }
}


async function fetchPlayerHeadPics(playerNames) {
    const results = {};

    for (const playerName of playerNames) {
        const response = await fetch(`/get/player_head_pic?playername=${playerName}`);
        const data = await response.json();
        results[playerName] = data['img'];
    }

    return results;
}


async function updateServerStatus() {
    const response = await fetch('https://mcserver-api.757678.xyz/get/tps');
    const data = await response.json();
    document.getElementById('server_now_cpu').textContent = `CPU：${data.cpu.process}%(系统：${data.cpu.system}%)`;
    document.getElementById('server_now_mem').textContent = `MEM：${data.ram.memory_process}M(系统剩余：${data.ram.memory_system}M)`;
    document.getElementById('server_now_tps').textContent = `TPS(1m)：${data.tps['1m']}`;
    document.getElementById('server_now_mspt').textContent = `MSPT(1m)：${data.mspt['1m']}`;
}












updateChatHistoryData();
updateServerStatus();

setInterval(updateChatHistoryData, 60000);  // 每60秒更新一次
setInterval(updateServerStatus, 60000);

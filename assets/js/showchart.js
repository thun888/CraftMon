// 获取数据
var timestamps = []
var player_counts = []
// 初始化图表
var chart = echarts.init(document.getElementById('player_count_history'));


async function updateData() {
    const response = await fetch('/api/player_count_history');
    const data_dict = await response.json();
    // 转换数据格式
    var timestamps = Object.keys(data_dict);
    var player_counts = Object.values(data_dict);
    // 设置图表选项
    option = {
        title: {
            text: '玩家人数历史记录（近7天）'
        },
        tooltip: {
            trigger: 'axis'
        },
        xAxis: {
            data: timestamps
        },
        yAxis: {},
        series: [{
            name: '玩家人数',
            type: 'line',
            data: player_counts
        }]
    };
    chart.setOption(option);
}


setInterval(updateData, 60000);  // 每60秒更新一次
updateData();

window.addEventListener('resize', function() {
    chart.resize();
});

const target = document.querySelector('#monitor');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      chart.resize();
    }
  });
}, {
  root: null,
  threshold: 0.1
});

observer.observe(target);

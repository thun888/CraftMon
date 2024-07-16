// 获取数据
var timestamps = []
var player_counts = []
// 初始化图表
var chart = echarts.init(document.getElementById('player_count_history'));


async function updateChartData() {
  const response = await fetch('/api/player_count_history');
  const data_dict = await response.json();
  // 转换为当地时间
  var timestamps = Object.keys(data_dict).map(ts => new Date(ts + 'Z').toLocaleString());
  console.log("使用" + Intl.DateTimeFormat().resolvedOptions().timeZone + "时区");
  var player_counts = Object.values(data_dict);
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

//页面渲染完成时执行
addEventListener("load",function(){
  updateChartData();
})

setInterval(updateChartData, 60000);  // 每60秒更新一次

window.addEventListener('resize', function() {
    chart.resize();
});

// 用于切换页面时使图表正常显示
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

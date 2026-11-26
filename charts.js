// Charts for the report, using Chart.js 4 (https://www.chartjs.org/docs/latest/)
// The numbers come from chart-data.js, which the notebook's export creates.

const TWITTER = '#2f6aa3';
const TRUTH_SOCIAL = '#b9472a';
const OTHER = '#8a8f98';
const HIGHLIGHT = '#1b1f24';

Chart.defaults.font.family = "'Public Sans', Arial, sans-serif";
// Smaller text on phone screens
Chart.defaults.font.size = window.innerWidth < 600 ? 12 : 14;
Chart.defaults.color = '#353a41';
Chart.defaults.maintainAspectRatio = false;
Chart.defaults.plugins.legend.labels.boxWidth = 14;

// No chart animation for people who have asked their device to reduce motion
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  Chart.defaults.animation = false;
}

function timesNormal(value) {
  return value.toFixed(2) + ' times his normal';
}

function drawCharts() {
  // Posts per month
  new Chart(document.getElementById('timelineChart'), {
    type: 'line',
    data: {
      labels: chartData.timeline.labels,
      datasets: [
        {
          label: 'Twitter, his own posts',
          data: chartData.timeline.twitter,
          borderColor: TWITTER,
          backgroundColor: TWITTER,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: 'Truth Social, his own posts',
          data: chartData.timeline.truthSocial,
          borderColor: TRUTH_SOCIAL,
          backgroundColor: TRUTH_SOCIAL,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: 'Reposts on either platform',
          data: chartData.timeline.reposts,
          borderColor: OTHER,
          backgroundColor: OTHER,
          borderDash: [5, 4],
          pointRadius: 0,
          borderWidth: 1.5
        }
      ]
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            autoSkip: false,
            maxRotation: 0,
            // Label every other January so the axis isn't crowded
            callback: function (value, index) {
              const month = chartData.timeline.labels[index];
              return month.endsWith('-01') && Number(month.slice(0, 4)) % 2 === 1 ? month.slice(0, 4) : '';
            }
          }
        },
        y: {
          beginAtZero: true,
          title: { display: true, text: 'Posts per month' }
        }
      }
    }
  });

  // Style features
  new Chart(document.getElementById('stylesChart'), {
    type: 'bar',
    data: {
      labels: chartData.styles.labels,
      datasets: [
        { label: 'Twitter', data: chartData.styles.twitter, backgroundColor: TWITTER },
        { label: 'Truth Social', data: chartData.styles.truthSocial, backgroundColor: TRUTH_SOCIAL }
      ]
    },
    options: {
      indexAxis: 'y',
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              const sign = context.raw > 0 ? '+' : '';
              return context.dataset.label + ': ' + sign + context.raw + '% compared with posts without it';
            }
          }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Change in median score' },
          ticks: {
            callback: function (value) {
              return (value > 0 ? '+' : '') + value + '%';
            }
          }
        },
        y: { grid: { display: false } }
      }
    }
  });

  // Post types
  new Chart(document.getElementById('typesChart'), {
    type: 'bar',
    data: {
      labels: chartData.postTypes.labels,
      datasets: [
        { label: 'Twitter', data: chartData.postTypes.twitter, backgroundColor: TWITTER },
        { label: 'Truth Social', data: chartData.postTypes.truthSocial, backgroundColor: TRUTH_SOCIAL }
      ]
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.dataset.label + ': ' + timesNormal(context.raw);
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: { beginAtZero: true, title: { display: true, text: 'Median score' } }
      }
    }
  });

  // Posts per day
  new Chart(document.getElementById('volumeChart'), {
    type: 'bar',
    data: {
      labels: chartData.volume.labels,
      datasets: [
        { label: 'Twitter', data: chartData.volume.twitter, backgroundColor: TWITTER },
        { label: 'Truth Social', data: chartData.volume.truthSocial, backgroundColor: TRUTH_SOCIAL }
      ]
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.dataset.label + ': ' + timesNormal(context.raw);
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, title: { display: true, text: 'His posts that day' } },
        y: { beginAtZero: true, title: { display: true, text: 'Median score' } }
      }
    }
  });

  // Hour of day
  new Chart(document.getElementById('timingChart'), {
    type: 'line',
    data: {
      labels: chartData.timing.labels,
      datasets: [
        { label: 'Twitter', data: chartData.timing.twitter, borderColor: TWITTER, backgroundColor: TWITTER, pointRadius: 2 },
        { label: 'Truth Social', data: chartData.timing.truthSocial, borderColor: TRUTH_SOCIAL, backgroundColor: TRUTH_SOCIAL, pointRadius: 2 }
      ]
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.dataset.label + ': ' + timesNormal(context.raw);
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } },
        y: { title: { display: true, text: 'Median score' } }
      }
    }
  });

  // Topics on Truth Social
  new Chart(document.getElementById('topicsChart'), {
    type: 'bar',
    data: {
      labels: chartData.topics.labels,
      datasets: [{
        label: 'Median score',
        data: chartData.topics.scores,
        backgroundColor: chartData.topics.highlight.map(isElections => isElections ? HIGHLIGHT : TRUTH_SOCIAL)
      }]
    },
    options: {
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (context) {
              return timesNormal(context.raw);
            }
          }
        }
      },
      scales: {
        x: { beginAtZero: true, title: { display: true, text: 'Median score' } },
        y: { grid: { display: false } }
      }
    }
  });

  // Tone on Truth Social
  new Chart(document.getElementById('tonesChart'), {
    type: 'bar',
    data: {
      labels: chartData.tones.labels,
      datasets: [{
        label: 'Median score',
        data: chartData.tones.scores,
        backgroundColor: chartData.tones.highlight.map(isPraise => isPraise ? HIGHLIGHT : TRUTH_SOCIAL)
      }]
    },
    options: {
      indexAxis: 'y',
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: function (context) {
              return timesNormal(context.raw);
            }
          }
        }
      },
      scales: {
        x: { beginAtZero: true, title: { display: true, text: 'Median score' } },
        y: { grid: { display: false } }
      }
    }
  });

  // Election posts by year
  new Chart(document.getElementById('electionsChart'), {
    type: 'line',
    data: {
      labels: chartData.elections.labels,
      datasets: [
        { label: 'Election posts', data: chartData.elections.elections, borderColor: TRUTH_SOCIAL, backgroundColor: TRUTH_SOCIAL, borderWidth: 3 },
        { label: 'All other posts', data: chartData.elections.other, borderColor: OTHER, backgroundColor: OTHER, borderDash: [5, 4] }
      ]
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      plugins: {
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.dataset.label + ': ' + timesNormal(context.raw);
            }
          }
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: { min: 0.6, max: 1.5, title: { display: true, text: 'Median score' } }
      }
    }
  });

  // Scorecard modelled on the Knox Index
  new Chart(document.getElementById('scorecardChart'), {
    type: 'radar',
    data: {
      labels: chartData.scorecard.labels,
      datasets: [
        {
          label: 'Twitter 2017 to 2020',
          data: chartData.scorecard.twitter,
          borderColor: TWITTER,
          backgroundColor: 'rgba(47, 106, 163, 0.15)'
        },
        {
          label: 'Truth Social 2025 to 2026',
          data: chartData.scorecard.truthSocial,
          borderColor: TRUTH_SOCIAL,
          backgroundColor: 'rgba(185, 71, 42, 0.15)'
        }
      ]
    },
    options: {
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { display: false },
          pointLabels: { font: { size: 14, weight: '600' } }
        }
      }
    }
  });
}

// The figures behind the scorecard, as a plain table
function fillScorecardTable() {
  const body = document.getElementById('scorecardTable');
  chartData.scorecardTable.forEach(function (row) {
    const tr = document.createElement('tr');
    row.forEach(function (cell, i) {
      const el = document.createElement(i === 0 ? 'th' : 'td');
      if (i === 0) el.scope = 'row';
      el.textContent = cell;
      tr.appendChild(el);
    });
    body.appendChild(tr);
  });
}

fillScorecardTable();

// Wait for the web fonts so the chart labels use them
document.fonts.ready.then(drawCharts);

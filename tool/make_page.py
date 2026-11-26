"""Turns report_data.json (exported by the notebook) into chart-data.js for the web page.

Run from the project folder:  python tool/make_page.py data/report_data.json chart-data.js
"""
import json
import sys

import pandas as pd

data_path, out_path = sys.argv[1], sys.argv[2]
with open(data_path) as f:
    d = json.load(f)


def lookup(rows, **match):
    """Return the first row whose fields match, or None."""
    for r in rows:
        if all(r[k] == v for k, v in match.items()):
            return r
    return None


# Timeline: every month from the first tweet to the last Truth Social post
timeline = pd.DataFrame(d['timeline'])
months = pd.period_range(timeline['month'].min(), timeline['month'].max(), freq='M').strftime('%Y-%m').tolist()
own = timeline.pivot_table(index='month', columns='platform', values='own_posts', aggfunc='sum')
reposts = timeline.groupby('month')['reposts'].sum()
own = own.reindex(months)
twitter_line = [None if m > '2021-01' else int(v or 0) for m, v in zip(months, own['Twitter'].fillna(0))]
truth_line = [None if m < '2022-02' else int(v or 0) for m, v in zip(months, own['Truth Social'].fillna(0))]

# Styles: % change in median score for posts with each feature vs without it
# Two-line labels (a list per label) so they fit on a phone screen
style_names = {
    'nickname': ['Nickname for', 'an opponent'], 'media_attack': ['Attacks', 'the media'], 'other_side': ['Mentions the', 'other side'],
    'heavy_caps': ['Lots of', 'capitals'], 'exclamation': ['Exclamation', 'mark'], 'question': ['Asks a', 'question'], 'has_link': ['Contains', 'a link'],
}
def uplift(tag, platform):
    with_tag = lookup(d['styles'], tag=tag, platform=platform, tagged=True)['median_score']
    without = lookup(d['styles'], tag=tag, platform=platform, tagged=False)['median_score']
    return round((with_tag / without - 1) * 100)

# Post types
type_names = {'text': 'His own words', 'media_only': 'Image or video only', 'link_only': 'Only a link'}
def type_score(platform, post_type):
    row = lookup(d['post_types'], platform=platform, post_type=post_type)
    return row['median_score'] if row else None

# Volume bands
bands = ['1-3', '4-7', '8-15', '16-30', '31+']
band_names = ['1 to 3', '4 to 7', '8 to 15', '16 to 30', '31 or more']

# Timing
def hour_label(h):
    if h == 0:
        return '12am'
    if h < 12:
        return f'{h}am'
    if h == 12:
        return '12pm'
    return f'{h - 12}pm'

def hour_score(platform, hour):
    row = lookup(d['timing'], platform=platform, hour=hour)
    return row['median_score'] if row else None

# Topics and tones, Truth Social only
topics = sorted([r for r in d['topics'] if r['platform'] == 'Truth Social' and r['topic_tag'] != 'Other/unclear'],
                key=lambda r: -r['median_score'])
tones = [r for r in d['devices'] if r['rhetorical_device'] != 'Other']

# Elections by year, Truth Social
elections = [r for r in d['elections'] if r['platform'] == 'Truth Social']

# Scorecard: each measure scaled so the higher period = 100, plus my own simple average
card = {r['period']: r for r in d['scorecard']}
tw, ts = card['Twitter 2017-20'], card['Truth Social 2025-26']
measures = [('Activity', 'posts_per_day'), ('Engagement %', 'engagement_pct'), ('Virality', 'shares_per_like'), ('Followers', 'followers')]
tw_scaled, ts_scaled = [], []
for _, col in measures:
    top = max(tw[col], ts[col])
    tw_scaled.append(round(tw[col] / top * 100))
    ts_scaled.append(round(ts[col] / top * 100))
tw_scaled.append(round(sum(tw_scaled) / 4))
ts_scaled.append(round(sum(ts_scaled) / 4))

chart_data = {
    'timeline': {'labels': months, 'twitter': twitter_line, 'truthSocial': truth_line,
                 'reposts': [int(reposts.get(m, 0)) for m in months]},
    'styles': {'labels': list(style_names.values()),
               'twitter': [uplift(t, 'Twitter') for t in style_names],
               'truthSocial': [uplift(t, 'Truth Social') for t in style_names]},
    'postTypes': {'labels': list(type_names.values()),
                  'twitter': [type_score('Twitter', t) for t in type_names],
                  'truthSocial': [type_score('Truth Social', t) for t in type_names]},
    'volume': {'labels': band_names,
               'twitter': [lookup(d['volume'], platform='Twitter', posts_per_day=b)['median_score'] for b in bands],
               'truthSocial': [lookup(d['volume'], platform='Truth Social', posts_per_day=b)['median_score'] for b in bands]},
    'timing': {'labels': [hour_label(h) for h in range(24)],
               'twitter': [hour_score('Twitter', h) for h in range(24)],
               'truthSocial': [hour_score('Truth Social', h) for h in range(24)]},
    'topics': {'labels': [[r['topic_tag'], f"{r['pct_of_posts']:.0f}% of posts"] for r in topics],
               'scores': [r['median_score'] for r in topics],
               'highlight': [r['topic_tag'] == 'Elections' for r in topics]},
    'tones': {'labels': [r['rhetorical_device'].capitalize() for r in tones],
              'scores': [r['median_score'] for r in tones],
              'highlight': [r['rhetorical_device'] == 'Praise' for r in tones]},
    'elections': {'labels': [str(r['year']) if r['year'] < 2026 else '2026 so far' for r in elections],
                  'elections': [r['election_score'] for r in elections],
                  'other': [r['other_score'] for r in elections]},
    'scorecard': {'labels': [m for m, _ in measures] + ['Overall (my own average)'],
                  'twitter': tw_scaled, 'truthSocial': ts_scaled},
    'scorecardTable': [
        ['Own posts per active day', f"{tw['posts_per_day']:.1f}", f"{ts['posts_per_day']:.1f}"],
        ['Median likes per post', f"{tw['median_likes']:,.0f}", f"{ts['median_likes']:,.0f}"],
        ['Followers', '88.7 million', 'about 10 million'],
        ['Engagement (median likes as % of followers)', f"{tw['engagement_pct']:.3f}%", f"{ts['engagement_pct']:.3f}%"],
        ['Virality (shares per like)', f"{tw['shares_per_like']:.2f}", f"{ts['shares_per_like']:.2f}"],
        ['Overall (my own average, out of 100)', str(tw_scaled[-1]), str(ts_scaled[-1])],
    ],
}

with open(out_path, 'w') as f:
    f.write('// Made by tool/make_page.py from the numbers the notebook exported. Do not edit by hand.\n')
    f.write('const chartData = ' + json.dumps(chart_data, indent=1) + ';\n')
print('Saved', out_path)

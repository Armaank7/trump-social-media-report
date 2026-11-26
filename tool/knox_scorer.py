"""
Post scorer: scores any politician's social media posts against their own normal.

It works on a CSV export of posts and runs four steps:
  1. Clean      read dates, fix HTML codes, separate reposts, sort posts into types
  2. Tag        style tags by fixed rules (nicknames, media attacks, capitals, links...)
  3. Score      each post's likes divided by that account's median likes that month
  4. Scorecard  activity, engagement, virality and followers, modelled on the Knox Index

Example, using the Truth Social file from this project:
  python knox_scorer.py trump_posts_full.csv --date created_at --likes like_count \
      --shares retruth_count --followers 10000000 --out results_truth_social

Example, using the Twitter archive:
  python knox_scorer.py trump_tweets.csv --date date --date-format "%m/%d/%Y %H:%M" \
      --likes favorites --shares retweets --followers 88700000 --start 2015-07 --out results_twitter
"""
import argparse
import html
import json
import os

import numpy as np
import pandas as pd

# Word lists for the style tags. Edit these for a different politician or country.
NICKNAME_WORDS = (r"\b(?:crooked|sleepy|lyin'?|crazy|cryin'?|pocahontas|shifty|mini mike|low energy|little marco|sloppy|"
                  r"nervous nancy|tampon tim|comrade kamala|laffin'?|newscum|deranged|birdbrain|meatball ron|desanctimonious|rino)\b")
MEDIA_WORDS = r"fake news|enemy of the people|lamestream|failing new york times|corrupt media|fake media"
OTHER_SIDE_WORDS = r"\b(?:democrats?|radical left|the left|liberals?|leftists?|communists?|marxists?|socialists?|dems)\b"

STYLE_TAGS = ['heavy_caps', 'exclamation', 'question', 'has_link', 'nickname', 'media_attack', 'other_side']


def clean(df, date_col, text_col, likes_col, shares_col, date_format, timezone):
    """Step 1: one row per post with a time, text, post type and like count."""
    posts = df.copy()
    posts = posts.drop_duplicates([date_col, text_col]).reset_index(drop=True)

    # Dates are read as UTC and converted to the audience's time zone
    if date_format:
        posts['posted_at'] = pd.to_datetime(posts[date_col], format=date_format, utc=True)
    else:
        posts['posted_at'] = pd.to_datetime(posts[date_col], format='mixed', utc=True)
    posts['posted_at'] = posts['posted_at'].dt.tz_convert(timezone)

    posts['text'] = posts[text_col].fillna('').astype(str).map(html.unescape)

    # Reposts are other people's words, so they are kept but not scored
    posts['is_repost'] = posts['text'].str.match(r'^RT[: ]')

    link_only = posts['text'].str.fullmatch(r'\s*https?://\S+\s*')
    no_text = posts['text'].str.strip() == ''
    posts['post_type'] = np.select([posts['is_repost'], no_text, link_only],
                                   ['repost', 'media_only', 'link_only'], default='text')

    posts['likes'] = pd.to_numeric(posts[likes_col], errors='coerce')
    posts.loc[posts['is_repost'], 'likes'] = np.nan
    posts['shares'] = pd.to_numeric(posts[shares_col], errors='coerce') if shares_col else np.nan

    posts['month'] = posts['posted_at'].dt.strftime('%Y-%m')
    posts['day'] = posts['posted_at'].dt.strftime('%Y-%m-%d')
    posts['hour'] = posts['posted_at'].dt.hour
    return posts


def tag(posts):
    """Step 2: style tags by fixed rules, so different years and platforms are compared fairly."""
    text = posts['text']
    posts['heavy_caps'] = text.str.count(r'\b[A-Z]{3,}\b') >= 3
    posts['exclamation'] = text.str.contains('!', regex=False)
    posts['question'] = text.str.contains('?', regex=False)
    posts['has_link'] = text.str.contains('http', regex=False)
    posts['nickname'] = text.str.contains(NICKNAME_WORDS, case=False)
    posts['media_attack'] = text.str.contains(MEDIA_WORDS, case=False)
    posts['other_side'] = text.str.contains(OTHER_SIDE_WORDS, case=False)
    return posts


def score(posts, start=None, end=None):
    """Step 3: each post's likes against the account's median likes that month."""
    own = posts[~posts['is_repost']].copy()
    own['typical_likes'] = own.groupby('month')['likes'].transform('median')
    own['score'] = own['likes'] / own['typical_likes']
    if start:
        own.loc[own['month'] < start, 'score'] = np.nan
    if end:
        own.loc[own['month'] > end, 'score'] = np.nan
    own['share_rate'] = own['shares'] / own['likes']
    return own


def summarise(own):
    """Tables that answer 'what works': post type, style, posts per day and hour."""
    scored = own[own['score'].notna()]
    text_posts = scored[scored['post_type'] == 'text']

    post_types = scored.groupby('post_type')['score'].agg(posts='count', median_score='median').round(2)

    style_rows = []
    for tag_name in STYLE_TAGS:
        with_tag = text_posts.loc[text_posts[tag_name], 'score'].median()
        without = text_posts.loc[~text_posts[tag_name], 'score'].median()
        style_rows.append({'tag': tag_name, 'posts_with_tag': int(text_posts[tag_name].sum()),
                           'median_with': round(with_tag, 2), 'median_without': round(without, 2),
                           'change_pct': round((with_tag / without - 1) * 100)})
    styles = pd.DataFrame(style_rows)

    per_day = scored.groupby('day')['score'].transform('count')
    bands = pd.cut(per_day, [0, 3, 7, 15, 30, np.inf], labels=['1-3', '4-7', '8-15', '16-30', '31+'])
    bands = bands.rename('posts_that_day')
    volume = scored.groupby(bands, observed=True)['score'].agg(posts='count', median_score='median').round(2)

    by_hour = scored.groupby('hour')['score'].agg(posts='count', median_score='median').round(2)
    by_hour = by_hour[by_hour['posts'] >= 100]

    return {'post_types': post_types, 'styles': styles, 'volume': volume, 'by_hour': by_hour}


def scorecard(own, followers):
    """Step 4: four measures modelled on the Knox Index."""
    has_likes = own[own['likes'].notna()]
    median_likes = has_likes['likes'].median()
    card = {
        'own_posts_per_active_day': round(len(own) / own['day'].nunique(), 1),
        'median_likes': float(median_likes),
        'shares_per_like': round(float(own['share_rate'].median()), 3),
        'followers': followers,
        'engagement_pct': round(median_likes / followers * 100, 3) if followers else None,
    }
    return card


def main():
    parser = argparse.ArgumentParser(description='Score social media posts against the account\'s own normal.')
    parser.add_argument('csv', help='CSV file of posts')
    parser.add_argument('--date', required=True, help='column with the post time (UTC)')
    parser.add_argument('--text', default='text', help='column with the post text')
    parser.add_argument('--likes', required=True, help='column with like counts')
    parser.add_argument('--shares', help='column with share or repost counts')
    parser.add_argument('--date-format', help='date format, e.g. "%%m/%%d/%%Y %%H:%%M" (default: worked out per row)')
    parser.add_argument('--timezone', default='America/New_York', help='time zone of the audience')
    parser.add_argument('--followers', type=float, help='follower count, for the engagement rate')
    parser.add_argument('--start', help='first month to score, e.g. 2015-07')
    parser.add_argument('--end', help='last month to score, e.g. 2020-12')
    parser.add_argument('--out', default='results', help='folder for the results')
    args = parser.parse_args()

    raw = pd.read_csv(args.csv, low_memory=False)
    posts = clean(raw, args.date, args.text, args.likes, args.shares, args.date_format, args.timezone)
    posts = tag(posts)
    own = score(posts, args.start, args.end)
    tables = summarise(own)
    card = scorecard(own[own['score'].notna()], args.followers)

    os.makedirs(args.out, exist_ok=True)
    own.to_csv(os.path.join(args.out, 'scored_posts.csv'), index=False)
    for name, table in tables.items():
        table.to_csv(os.path.join(args.out, f'{name}.csv'))
    with open(os.path.join(args.out, 'scorecard.json'), 'w') as f:
        json.dump(card, f, indent=2)

    print(f"{len(raw):,} rows read, {len(own):,} own posts, {own['score'].notna().sum():,} scored")
    print('\nScore by post type\n', tables['post_types'])
    print('\nStyle tags (posts in their own words)\n', tables['styles'].to_string(index=False))
    print('\nPosts per day\n', tables['volume'])
    print('\nScorecard\n', json.dumps(card, indent=2))
    print(f'\nSaved to {args.out}/')


if __name__ == '__main__':
    main()

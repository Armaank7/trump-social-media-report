# How Trump wins online

A data task for Knox: a public briefing for the Atlantic Data Institute on how Donald Trump uses social media, what works with his base, and what other politicians can learn in 2026.

**Read the report:** https://armaank7.github.io/trump-social-media-report/

## What's in this repository

| Path | What it is |
|---|---|
| `index.html`, `style.css`, `charts.js` | The web report. Static HTML and CSS, with charts drawn by Chart.js |
| `chart-data.js` | The numbers behind the charts, made by `tool/make_page.py`. Don't edit it by hand |
| `notebook/knox_trump_analysis.ipynb` | The analysis: loading, cleaning, scoring, tagging, SQL queries and checks, in order |
| `tool/knox_scorer.py` | The reusable post scorer. Runs on any account's posts, not only Trump's |
| `tool/make_page.py` | Turns the notebook's export into `chart-data.js` |
| `data/report_data.json` | Every number the report uses, exported by the notebook |
| `data/hand_check_results.xlsx` | 80 labels checked by hand (Y right, N wrong, ? unsure). The notebook reads it in section 6 |
| `method_note.pdf` | One-page method note |
| `js/`, `fonts/` | Chart.js 4.4.1 and the two typefaces (Newsreader and Public Sans), hosted here so the page has no outside dependencies |

The two raw data files (`trump_tweets.csv` and `trump_posts_full.csv`) were supplied by Knox, so they aren't included here.

## How the analysis works

1. **Clean.** Both files are read, deduplicated and converted to US Eastern time. Reposts are separated, because they are other people's words. Problems found in the raw data (rounded IDs, a repost column that was wrong on every row, missing like counts, likes counted years after posting) are listed in the notebook and the report.
2. **Tag.** Each post gets style tags by fixed rules (nicknames, media attacks, mentions of the other side, capitals, exclamation marks, questions, links). Truth Social posts came with topic labels. A text model trained on those labels gives the tweets topics too, and only the topics it gets right reliably are used.
3. **Score.** Each post's likes are divided by his median likes that month on the same platform. 1 is a normal post for him at the time, 2 is double, 0.5 is half.
4. **Analyse.** SQL queries (DuckDB) compare scores by post type, style, topic, tone, posting volume and hour. A regression checks that the style effects hold when tested together.

## Running it

### The notebook
Open `notebook/knox_trump_analysis.ipynb` in Google Colab, put the two raw CSVs in `My Drive/Knox`, and run all cells. To run it locally instead, skip the Google Drive cell and set `DATA_DIR` to the folder with the CSVs.

Python packages: pandas, numpy, duckdb, scikit-learn, statsmodels.

### The post scorer
```
pip install pandas numpy

# Truth Social, 2025 onwards
python tool/knox_scorer.py trump_posts_full.csv --date created_at --likes like_count \
    --shares retruth_count --followers 10000000 --start 2025-01 --out results_truth_social

# Twitter, first term
python tool/knox_scorer.py trump_tweets.csv --date date --date-format "%m/%d/%Y %H:%M" \
    --likes favorites --shares retweets --followers 88700000 --start 2017-01 --end 2020-12 --out results_twitter
```
It saves every scored post, the summary tables and a scorecard to the `--out` folder, and prints the main results.

The tool only needs a time, the text and a like count, so it works on any export. It does less archive-specific cleaning than the notebook (it doesn't know about deleted tweets, for example), so its Twitter figures differ slightly from the report's. The word lists for nicknames and the other side are at the top of the file and can be changed for a different politician or country.

### Rebuilding the page
After running the notebook, copy `report_data.json` into `data/` and run:
```
python tool/make_page.py data/report_data.json chart-data.js
```

## Author
Armaan Khan

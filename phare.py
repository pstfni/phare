# /// script
# dependencies = [
#   "feedparser>=6.0.11",
# ]
# ///

""" Phare: Vibecoded RSS feed tracker and wathclist generator."""

import feedparser
import urllib.request
from datetime import datetime
from typing import List, Dict
import json

# Category colors
CATEGORY_COLORS = {
    "EM": "#0066cc",      # Blue
    "AI": "#f4b400",      # Yellow
    "Dev": "#333333",     # Black
    "Ops": "#dc3545",      # Red
    "HN": "#ff8c00"     # Orange
}

FEEDS = {
    "Alex Ellis": ("https://blog.alexellis.io/rss/", "Ops"),
    "Julia Evans": ("https://jvns.ca/atom.xml", "Dev"),
    "Dan Luu": ("https://danluu.com/atom.xml", "EM"),
    "Will Larson": ("https://lethain.com/feeds/", "EM"),
    "Hamel Husain": ("https://hamel.dev/feed.xml", "AI"),
    "Vicki Boykis": ("https://vickiboykis.com/feed/", "Dev"),
    "Camille Fournier": ("https://www.elidedbranches.com/feeds/posts/default", "EM"),
    "Charity Majors": ("https://charity.wtf/feed/", "EM"),
    "Pragmatic Engineer": ("https://blog.pragmaticengineer.com/rss/", "Ops"),
    "Martin Fowler": ("https://martinfowler.com/feed.atom", "Dev"),
    "Chip Huyen": ("https://huyenchip.com/feed.xml", "AI"),
    "Eugene Yan": ("https://eugeneyan.com/feed.xml", "AI"),
    "Simon Willison": ("https://simonwillison.net/atom/everything/", "AI"),
    "Stéphane Robert": ("https://blog.stephane-robert.info/index.xml", "Ops")
}
HN_MIN_SCORE = 400  # Minimum score for HN stories to be included

def fetch_hn_top_stories(min_score: int, days: int = 7) -> List[Dict]:
    """Fetch HN stories above score threshold."""
    posts = []
    cutoff = datetime.now().timestamp() - (days * 86400)

    try:
        with urllib.request.urlopen("https://hacker-news.firebaseio.com/v0/topstories.json") as response:
            story_ids = json.loads(response.read())[:64]  # Top 64

        for story_id in story_ids:
            with urllib.request.urlopen(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json") as response:
                story = json.loads(response.read())

            if story.get('score', 0) >= min_score and story.get('time', 0) > cutoff:
                posts.append({
                    'author': 'Hacker News',
                    'title': f"{story['title']} ({story.get('score', 0)} pts)",
                    'link': story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                    'published': datetime.fromtimestamp(story['time']).isoformat(),
                    'category': 'HN'
                })
    except Exception as e:
        print(f"Error fetching HN: {e}")

    return posts

def fetch_recent_posts(feeds: Dict[str, tuple], days: int = 7) -> List[Dict]:
    """Fetch recent posts from RSS feeds."""
    posts = []
    cutoff = datetime.now().timestamp() - (days * 86400)

    for name, (url, category) in feeds.items():
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                pub_date = entry.get('published_parsed') or entry.get('updated_parsed')
                if pub_date and datetime(*pub_date[:6]).timestamp() > cutoff:
                    posts.append({
                        'author': name,
                        'title': entry.title,
                        'link': entry.link,
                        'published': datetime(*pub_date[:6]).isoformat(),
                        'category': category
                    })
        except Exception as e:
            print(f"Error fetching {name}: {e}")

    return sorted(posts, key=lambda x: x['published'], reverse=True)

def generate_html(posts: List[Dict], output_file: str = "watchlist.html"):
    """Generate HTML file with posts."""
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Phare: Veille personnelle</title>
    <style>
        body { font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; }
        h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .post { margin: 20px 0; padding: 15px; border-left: 3px solid; background: #f5f5f5; }
        .post a { color: #0066cc; text-decoration: none; font-weight: 500; }
        .post a:hover { text-decoration: underline; }
        .meta { color: #666; font-size: 0.9em; margin-top: 5px; }
        .source { font-weight: 600; color: #333; }
        .category { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.85em; margin-left: 8px; }
    </style>
</head>
<body>
    <h1>Phare- Posts</h1>
"""

    for post in posts:
        color = CATEGORY_COLORS.get(post['category'], '#999')
        html += f"""    <div class="post" style="border-left-color: {color};">
        <a href="{post['link']}" target="_blank">{post['title']}</a>
        <div class="meta">
            <span class="source">{post['author']}</span>
            <span class="category" style="background-color: {color}; color: white;">{post['category']}</span>
            • {post['published'][:10]}
        </div>
    </div>
"""

    html += """</body>
</html>"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated {output_file}")

if __name__ == "__main__":
    posts = fetch_recent_posts(FEEDS, days=7)
    hn_posts = fetch_hn_top_stories(HN_MIN_SCORE, days=7)
    all_posts = sorted(posts + hn_posts, key=lambda x: x['published'], reverse=True)
    generate_html(all_posts)
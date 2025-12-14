from flask import Flask, render_template, abort
import requests
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

app = Flask(__name__)

RSS_FEEDS = {
    "BBC": "https://feeds.bbci.co.uk/news/rss.xml",
    "NYT": "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
}

def fetch_all_articles():

    articles = []
    article_id = 1

    for source_name, url in RSS_FEEDS.items():
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
        except Exception:
            continue

        try:
            root = ET.fromstring(resp.content)
        except ET.ParseError:
            continue

        channel = root.find("channel")
        if channel is None:
            continue

        for item in channel.findall("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()
            pub_date_raw = (item.findtext("pubDate") or "").strip()

            pub_date = None
            if pub_date_raw:
                try:
                    dt = parsedate_to_datetime(pub_date_raw)
                    pub_date = dt.date().isoformat()
                except Exception:
                    pub_date = None

            articles.append({
                "id": article_id,
                "source": source_name,
                "title": title,
                "link": link,
                "pubDate": pub_date,
                "description": description,
            })
            article_id += 1

    return articles


def get_article_by_id(articles, article_id):
    for a in articles:
        if a["id"] == article_id:
            return a
    return None

@app.route("/")
def index():
    all_articles = fetch_all_articles()
    return render_template("index.html", articles=all_articles)

@app.route("/article/<int:article_id>")
def article(article_id):
    all_articles = fetch_all_articles()
    a = get_article_by_id(all_articles, article_id)
    if a is None:
        abort(404)
    return render_template("article.html", article=a)

if __name__ == "__main__":
    app.run(debug=True)

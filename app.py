from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

app = Flask(__name__)

def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def search_google_news(keyword):
    results = []
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')
        for item in items[:20]:
            title = clean_text(item.find('title').text if item.find('title') else '')
            link = item.find('link').text if item.find('link') else ''
            description = clean_text(item.find('description').text if item.find('description') else '')
            pub_date = item.find('pubDate').text if item.find('pubDate') else ''
            source = item.find('source').text if item.find('source') else '출처 불명'
            if title:
                results.append({
                    'title': title,
                    'link': link,
                    'description': description[:200],
                    'pub_date': pub_date,
                    'source': source,
                    'score': title.lower().count(keyword.lower()) * 10 + description.lower().count(keyword.lower()) * 3
                })
    except Exception as e:
        print(f"오류: {e}")
    return results

def search_daum_news(keyword):
    results = []
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://search.daum.net/search?w=news&q={encoded_keyword}&sort=accuracy"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.select('div.item-title')
        for item in items[:10]:
            a_tag = item.select_one('a')
            if a_tag:
                title = a_tag.text.strip()
                link = a_tag.get('href', '')
                if title:
                    results.append({
                        'title': title,
                        'link': link,
                        'description': '',
                        'pub_date': '',
                        'source': '다음뉴스',
                        'score': title.lower().count(keyword.lower()) * 10
                    })
    except Exception as e:
        print(f"다음 오류: {e}")
    return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    if not keyword:
        return jsonify({'error': '검색어를 입력해주세요.', 'results': []})
    if len(keyword) < 2:
        return jsonify({'error': '검색어는 2글자 이상 입력해주세요.', 'results': []})

    google_results = search_google_news(keyword)
    daum_results = search_daum_news(keyword)
    all_results = google_results + daum_results

    seen = set()
    unique = []
    for item in all_results:
        key = item['title'][:15]
        if key not in seen:
            seen.add(key)
            unique.append(item)

    unique.sort(key=lambda x: x['score'], reverse=True)
    print(f"검색어: {keyword}, 결과: {len(unique)}건")

    return jsonify({
        'keyword': keyword,
        'total': len(unique),
        'results': unique[:15]
    })

if __name__ == '__main__':
    print("뉴스 검색 서버 시작!")
    print("브라우저에서 http://localhost:5000 으로 접속하세요")
    app.run(debug=True, port=5000)
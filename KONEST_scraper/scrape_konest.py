import requests
# pip install requests beautifulsoup4　を実行
from bs4 import BeautifulSoup
import csv
import time
import random

output_file = f"todays_korean.csv"
base_list_url = "https://www.konest.com/contents/todays_korean_list.html"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
}

def del_empty_line(str):
    lines = str.split('\n')
    ret = [line for line in lines if line != "\r"]
    return '\n'.join(ret)

def scrape_konest():
    print(f"スクレイピングを開始します。\n")

    # 文字化けしないようにutf-8-sigでファイルを開く
    with open(output_file, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        # ヘッダー行を書き込み
        writer.writerow(["見出し語", "意味", "解説", "例文", "id"])

        page = 1
        while True:
            list_url = base_list_url + f"?cp={page}"
            print(f"=== ページ {page} の一覧ページを取得中 ===")
            
            try:
                res = requests.get(list_url, headers=headers)
                res.raise_for_status()
            except Exception as e:
                print(f"一覧ページの取得に失敗しました (Page {page}): {e}")
                continue

            # 待機
            time.sleep(10.0)
            
            soup = BeautifulSoup(res.text, "html.parser")

            # 個別の見出し語ページへのリンクを抽出
            word_links = []

            for a_tag in soup.find_all('a', class_='c-card__link c-card__link--sp-horizonal'):
                href = a_tag.get("href")
                if href.startswith("http"):
                    word_links.append(href)
                else:
                    word_links.append("https://www.konest.com" + href)

            # 取得した個別のページへ順番にアクセス
            for link in word_links:
                rand_sleep = random.uniform(5.0, 15.0)
                try:
                    word_res = requests.get(link, headers=headers)
                    word_res.raise_for_status()
                except Exception as e:
                    print(f"  単語ページの取得に失敗しました ({link}): {e}")
                    continue

                # 待機
                time.sleep(rand_sleep)
                
                word_soup = BeautifulSoup(word_res.text, "html.parser")

                try:
                    title = word_soup.find('div', id='korean_title')
                    word = title.text.strip() if title else "見出し語なし"

                    meaning_tag = word_soup.find('div', class_='c-hangul__content-main--translate')
                    meaning = meaning_tag.text.strip() if meaning_tag else ""

                    descriptions = word_soup.find_all('div', class_='c-hangul__content-description--item')
                    explanation = ""
                    example = ""

                    if len(descriptions) > 0:
                        # リンクの書き換え等
                        other_links = descriptions[0].find_all('a')
                        for ol in other_links:
                            if ol.get('href') and not ol['href'].startswith('http'):
                                ol['href'] = "https://www.konest.com" + ol['href']
                        explanation = del_empty_line(descriptions[0].text.strip())

                    if len(descriptions) >= 2:
                        example = del_empty_line(descriptions[1].text.strip())

                except Exception as e:
                    print(f"  データの抽出中にエラーが発生しました ({link}): {e}")
                    continue  # この単語をスキップして次へ進む

                # idの抽出
                konest_id = link.split('=')[-1]

                # 取得したデータをCSVに1行書き込み
                writer.writerow([word, meaning, explanation, example, konest_id])
                
                print(f"\r  取得完了: {word} {' ' * 50}", end="", flush=True)
            print()

            next = soup.find(class_='c-pagination__link is-disabled')
            if next and next.text == "次へ":
                break

            page += 1

    print(f"\nすべてのスクレイピングが完了し、'{output_file}' が作成されました。")

if __name__ == "__main__":
    scrape_konest()
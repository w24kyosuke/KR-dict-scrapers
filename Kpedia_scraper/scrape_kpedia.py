import requests
# pip install requests beautifulsoup4　を実行
from bs4 import BeautifulSoup
import csv
import time
import sys
import re

# スクレイピング対象の基本URL(Kpediaのホームページから各カテゴリにアクセスし、そのURLを引数で指定する)
args = None

# アクセス間隔(※注意 サーバへの負荷軽減のための設定なので0.3~2.0を推奨)
time_sleep = 0.3


def scrape_kpedia():
    args = sys.argv
    base_list_url = args[1]
    print(base_list_url)

    # 1ページ目にアクセスして最大ページ数を取得
    print("=== 最大ページ数を取得しています ===")
    try:
        res_first = requests.get(base_list_url.format(1))
        res_first.raise_for_status()
    except Exception as e:
        print(f"ページ数取得のためのアクセスに失敗しました: {e}")
        return
        
    soup_first = BeautifulSoup(res_first.text, "html.parser")
    max_pages = 1 # デフォルト値（取得失敗時のフォールバック用、失敗時は大抵1ページだけの時なので1）
    span_list = soup_first.find("span", class_="list")
    if span_list:
        # spanタグのテキストは "(1/20)" のようになるため、"/"と")"で挟まれた数字を抽出
        text_content = span_list.text.strip()
        if "/" in text_content and ")" in text_content:
            max_page_str = text_content.split("/")[1].replace(")", "")
            if max_page_str.isdigit():
                max_pages = int(max_page_str)
                
    print(f"全 {max_pages} ページをスクレイピングします。\n")
    # カテゴリ名と収録単語数を取得
    category_name = ""
    word_count = ""
    # font-size:20px と font-weight:bold を含むdivタグを探す
    header_div = soup_first.find("div", style=lambda s: s and "font-size:20px" in s and "font-weight:bold" in s)
    if header_div:
        span_tag = header_div.find("span")
        if span_tag and "単語数" in span_tag.text:
            # 「（単語数：3882）」から数字のみを抽出
            word_count = re.sub(r'\D', '', span_tag.text)
            total_words = int(word_count) if word_count.isdigit() else 0
            span_tag.decompose()  # spanタグを除去
            category_name = header_div.text.strip()  # 残ったテキストがカテゴリ名
            
    print(f"カテゴリ名: {category_name} (収録単語数: {word_count})")
    print(f"全 {max_pages} ページをスクレイピングします。\n")
    time.sleep(time_sleep) # 待機

    output_file = f"{category_name}_{word_count}words.csv"
    # 文字化けしないようにutf-8-sigでファイルを開く
    with open(output_file, mode="w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        # ヘッダー行を書き込み
        writer.writerow(["見出し語", "意味", "読み方", "類義語", "解説", "タグ", "id"])

        # 取得完了した単語のカウント用変数
        processed_count = 0

        for page in range(1, max_pages + 1):
            list_url = base_list_url + f"?nCP={page}"
            print(f"=== ページ {page}/{max_pages} の一覧ページを取得中 ===")
            
            try:
                res = requests.get(list_url)
                res.raise_for_status()
            except Exception as e:
                print(f"一覧ページの取得に失敗しました (Page {page}): {e}")
                continue

            # 待機
            time.sleep(time_sleep)
            
            soup = BeautifulSoup(res.text, "html.parser")

            # 個別の単語ページへのリンクを抽出
            # <tr>内の<td>内にある<a>タグを探し、hrefに "/w/" が含まれるものを単語リンクとみなす
            word_links = []
            for a_tag in soup.select("tr td a"):
                href = a_tag.get("href")
                if href and "/w/" in href:
                    if href.startswith("http"):
                        word_links.append(href)
                    else:
                        word_links.append("https://www.kpedia.jp" + href)

            # 取得した個別の単語ページへ順番にアクセス
            for link in word_links:
                try:
                    word_res = requests.get(link)
                    word_res.raise_for_status()
                except Exception as e:
                    print(f"  単語ページの取得に失敗しました ({link}): {e}")
                    continue

                # 待機
                time.sleep(time_sleep)
                
                word_soup = BeautifulSoup(word_res.text, "html.parser")

                # --- 見出し語の抽出 ---
                word = ""
                # "とは" というspanタグを持つaタグを探す
                for a in word_soup.find_all('a'):
                    span = a.find('span')
                    if span and 'とは' in span.text:
                        span.decompose() # "とは" のspanタグを除去
                        word = a.text.strip() # 残ったテキスト（見出し語）を取得
                        break

                # --- 各種データ抽出 ---
                meaning = ""
                reading = ""
                tags = ""
                synonyms = ""
                # 幅650のtableを探す
                tables = word_soup.find_all('table', width="650")
                for table in tables:
                    tds = table.find_all('td')
                    if len(tds) >= 3:
                        header_text = tds[0].text.strip()
                        if '意味' in header_text:
                            # 最後のtd要素のテキストを取得し、余分な改行や空白を削除
                            meaning = tds[-1].text.strip().replace('\r', '').replace('\n', '')
                        elif '読み方' in header_text:
                            reading = tds[-1].text.strip().replace('\r', '').replace('\n', '')
                        elif 'カテゴリー' in header_text:
                            category_text = tds[-1].text.strip()
                            # 「ホーム ＞ 自然 ＞ 資源、名詞」のような文字列から最下層を取得
                            if '＞' in category_text:
                                last_part = category_text.split('＞')[-1]
                            else:
                                last_part = category_text
                            # 「資源、名詞」を「、」で分割し、前後の空白を削除して半角スペースで結合
                            tags = " ".join([t.strip() for t in last_part.split('、')])
                        elif '類義語' in header_text:
                            # 最後のtd要素内にあるすべてのaタグからテキストを取得
                            synonym_list = [a.text.strip() for a in tds[-1].find_all('a')]
                            synonyms = "、".join(synonym_list)

                # --- 解説の抽出 ---
                explanation = ""
                exp_div = word_soup.find('div', class_='article_part')
                if exp_div:
                    explanation = exp_div.text.strip().replace('\r', '').replace('\n', '')

                # idの抽出
                kpedia_id = link.split("/")[-1]

                # 取得したデータをCSVに1行書き込み
                writer.writerow([word, meaning, reading, synonyms, explanation, tags, kpedia_id])
                
                processed_count += 1
                percentage = (processed_count / total_words) * 100 if total_words > 0 else 0
                print(f"\r  取得完了: {word} - 進捗: {percentage:.1f}% ({processed_count}/{total_words}){' ' * 50}", end="", flush=True)
            print()

    print(f"\nすべてのスクレイピングが完了し、'{output_file}' が作成されました。")

if __name__ == "__main__":
    scrape_kpedia()
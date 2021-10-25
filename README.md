# NHK for School Pro

- [NHKハッカソン- 教育×シビックテック×ニュース](https://nhk-hackathon.peatix.com/)での成果物です
- [NHK for School](https://www.nhk.or.jp/school/) で閲覧した動画クリップについて、[NHK NEWS WEB](https://www3.nhk.or.jp/news/)の関連記事を表示します

## Development

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
streamlit run nhk_hackathon/app.py
```

### Env

`.env` ファイルは、下記の情報を含みます。

```
WEBURL=https://XXXXXXXXXXXXXXX
WEBKEY=XXXXXXXXXXXXXXX
SCHURL=https://XXXXXXXXXXXXXXX
SCHKEY=XXXXXXXXXXXXXXX
```

### Flow

1. ユーザから検索語を受け取る
1. 検索語を含む「NHK for School」の動画クリップを一つ表示
1. 表示した動画クリップのタイトルや説明文を形態素解析ツール「MeCab」で処理し、名詞部分を「キーワード」として抽出（各キーワードは「TF-IDF」で重要度を計算しておく）
1. それぞれの名詞で「NHK NEWS WEB」の記事を検索し、重複を排除した記事群を「関連記事」とする
1. 関連記事は、各記事に含まれるキーワードを用いてスコア付けし、降順で表示

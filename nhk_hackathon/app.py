import os

# from transformers import pipeline
import fugashi
import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from streamlit_player import st_player


@st.cache(allow_output_mutation=True)
def get_sch_df_by_title(title: str):

    load_dotenv()
    SCHURL = os.getenv("SCHURL")
    SCHKEY = os.getenv("SCHKEY")

    result = requests.get(
        SCHURL, params={"key": SCHKEY, "kw": title, "cat": "c", "limit": 100}
    )

    df = pd.DataFrame(result.json()["result"])
    return df


@st.cache(allow_output_mutation=True)
def get_web_df_by_keyword(keyword: str):

    load_dotenv()
    WEBURL = os.getenv("WEBURL")
    WEBKEY = os.getenv("WEBKEY")

    result = requests.get(
        WEBURL,
        params={
            "key": WEBKEY,
            "keyword": keyword,
            "format": "json",
        },
    )

    df = pd.DataFrame(result.json()["record"])
    return df


def display_web_news(df: pd.DataFrame, news_idx: int):
    web_data = df.copy()
    web_title = web_data.loc[news_idx, "title"]
    web_pub_date = web_data.loc[news_idx, "pubDate"]
    web_url = web_data.loc[news_idx, "link"]
    web_image = web_data.loc[news_idx, "image"]
    web_description = web_data.loc[news_idx, "description"]
    web_detail2 = web_data.loc[news_idx, "detail2"]

    st.write(f"**[{web_title}](https://www3.nhk.or.jp/news/{web_url})**")
    st.write(f"{web_pub_date}")
    st.image(web_image, width=200)
    with st.expander(web_description):
        try:
            for detail2Paragraph in web_detail2["detail2Paragraph"]:
                detail2Title = detail2Paragraph["detail2Title"]
                detail2Article = detail2Paragraph["detail2Article"]
                detail2Img = detail2Paragraph["detail2Img"]
                st.subheader(detail2Title)
                if detail2Img:
                    st.image(detail2Img, width=200)
                st.write(detail2Article)
        except TypeError:
            pass


# def sentiment_analysis(df: pd.DataFrame):
#     sentiment_analyzer = pipeline(
#         "sentiment-analysis",
#         model="daigo/bert-base-japanese-sentiment",
#         tokenizer="daigo/bert-base-japanese-sentiment",
#     )
#     df["pos_score"] = [
#         d[0]["score"] for d in list(map(sentiment_analyzer, df["title"]))
#     ]
#     return df


def display_page(df: pd.DataFrame):
    web_data = df.copy()
    NUM_DEFAULT_DISPLAY = min(3, len(web_data))
    for news_idx in range(NUM_DEFAULT_DISPLAY):
        display_web_news(web_data, news_idx)

    if st.button("もっと読む"):
        for news_idx in range(NUM_DEFAULT_DISPLAY, min(100, len(web_data))):
            display_web_news(web_data, news_idx)


# ひらがなだけの文字列ならTrue
def ishira(strj):
    hiragana = "ぁあぃいぅうぇえぉおかがきぎくぐけげこご\
                さざしじすずせぜそぞただちぢっつづてでと\
                どなにぬねのはばぱひびぴふぶぷへべぺほぼ\
                ぽまみむめもゃやゅゆょよらりるれろゎわゐ\
                ゑをん0123456789０１２３４５６７８９月日時"

    return all([ch in hiragana for ch in strj])


st.set_page_config(layout="wide")
st.title("NHK for School Pro")


if __name__ == "__main__":

    user_input_title = st.sidebar.text_input("クリップを検索", "火山灰")

    sch_data = get_sch_df_by_title(user_input_title)

    if len(sch_data) == 0:
        st.info("クリップが見つかりませんでした")
        st.markdown("違うキーワードでクリップを探してみてください")
    else:
        sch_title = sch_data.loc[0, "title"]
        sch_desc = sch_data.loc[0, "description"]
        sch_clip_summary = sch_data.loc[0, "clipSummary"]
        sch_video = sch_data.loc[0, "video"]

        st.sidebar.subheader(sch_title)
        st.sidebar.markdown(sch_desc)

        with st.sidebar:
            st_player(sch_video, height=200)

        st.sidebar.write("**ねらい**")
        st.sidebar.markdown(sch_clip_summary)

        # Higuchiさんロジックで特定
        tagger = fugashi.GenericTagger()
        sch_data["nouns"] = [
            list(
                set(
                    line.split()[0]
                    for line in tagger.parse(text).splitlines()
                    if "名詞" in line.split()[-1]
                )
            )
            for text in (
                sch_data["title"] + sch_data["description"] + sch_data["clipSummary"]
            )
        ]
        sch_data["nouns"] = [
            " ".join(
                [word for word in row if len(word) != 1 and ishira(word) is not True]
            )
            for row in sch_data["nouns"]
        ]
        vectorizer = TfidfVectorizer()
        X = vectorizer.fit_transform(sch_data["nouns"])

        tfidf_df = (
            pd.DataFrame(
                {"word": vectorizer.get_feature_names(), "score": X.toarray()[0]}
            )
            .query("score > 0")
            .sort_values("score", ascending=False)
            .reset_index(drop=True)
        )
        sch_keywords = " ".join(tfidf_df["word"].to_list())

        st.sidebar.write("**このクリップのキーワード**")
        st.sidebar.markdown(sch_keywords)

        st.subheader("このクリップの関連記事")
        web_data = []
        for search_word in sch_keywords.split():
            _web_data = get_web_df_by_keyword(search_word)
            if len(_web_data) > 0:
                web_data.append(_web_data)
        web_data = pd.concat(web_data).reset_index(drop=True)

        # ロジックでデータをソート
        web_data = web_data.drop_duplicates(subset=["title"])
        web_data["cnt"] = 0
        for search_word in sch_keywords.split():
            print(tfidf_df.query(f"word=='{search_word}'"))
            web_data["cnt"] += (
                web_data["detail"].str.contains(search_word).astype(int)
                * 1
                / (tfidf_df.query(f"word=='{search_word}'")["score"].values[0])
            )
        web_data = web_data.sort_values("cnt", ascending=False).reset_index(drop=True)

        display_page(web_data)
        # web_data = sentiment_analysis(web_data)

import streamlit as st
import pandas as pd
from vietlott.config.products import get_config
from vietlott.model.strategy.random import RandomModel
from datetime import datetime, timedelta
import google.generativeai as genai
import os
# Đọc API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("API key for Gemini AI is not set. Please configure the GEMINI_API_KEY environment variable.")

# Cấu hình API key cho Gemini AI
genai.configure(api_key=API_KEY)

def _balance_long_df(df_: pd.DataFrame, n_splits: int = 20):
    """Chuyển đổi DataFrame dạng dài thành nhiều cột"""
    df_ = df_.reset_index()
    df_["result"] = df_["result"].astype(str)

    # Kiểm tra và tạo cột 'count' nếu chưa có
    if 'count' not in df_.columns:
        df_['count'] = df_.groupby('result')['result'].transform('count')

    df_["count"] = df_["count"].astype(str)

    final = None
    for i in range(len(df_) // n_splits + 1):
        dd = df_.iloc[i * n_splits: (i + 1) * n_splits]
        if final is None:
            final = dd
        else:
            final = pd.concat(
                [final.reset_index(drop=True), pd.DataFrame([None] * len(dd), columns=["-"]),
                 dd.reset_index(drop=True)],
                axis="columns",
            )
    final = final.fillna("")
    return final


def fn_stats(df):
    """Thống kê tần suất kết quả"""
    df_explode = df.explode("result")
    stats = df_explode.groupby("result").agg(count=("id", "count"))
    stats["%"] = (stats["count"] / len(df_explode) * 100).round(2)
    return stats


def analyze_with_gemini(prompt):
    """Gửi yêu cầu phân tích tới Gemini AI và trả về kết quả"""
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Đã có lỗi xảy ra khi gửi yêu cầu đến Gemini AI: {str(e)}"


def main():
    # Đọc dữ liệu từ nguồn
    df = pd.read_json(get_config("power_655").raw_path, lines=True, dtype=object, convert_dates=False)
    df["date"] = pd.to_datetime(df["date"]).dt.date

    # Lọc dữ liệu trong 30 ngày gần nhất
    today = datetime.today().date()
    thirty_days_ago = today - timedelta(days=30)
    df_30d = df[df["date"] >= thirty_days_ago]

    # Tính toán thống kê cho dữ liệu trong 30 ngày
    stats_30d = fn_stats(df_30d)

    # Gửi yêu cầu phân tích với Gemini AI
    stats_30d_markdown = stats_30d.to_string(index=False)
    prompt = f"""Dữ liệu phân tích kết quả kinh doanh từ xổ số Vietlot (30 ngày gần nhất):

        {stats_30d_markdown}

          Dưạ vào số phần trăm và count hãy cho 1 dãy  6 số có khả năng tiếp theo"""

    analysis_result = analyze_with_gemini(prompt)

    # Streamlit display
    st.title('Vietlot Data Analysis')

    st.subheader('Stats 6/55 Last 30 Days')
    st.dataframe(stats_30d, use_container_width=True)  # Hiển thị bảng với chiều rộng container

    st.subheader('Analysis from Gemini AI')
    st.write(analysis_result)


if __name__ == "__main__":
    main()

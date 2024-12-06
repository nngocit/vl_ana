# /usr/bin/env python
"""
this script is used to render the README.md that shows in repo's Github
"""
import streamlit as st
import google.generativeai as genai
import pandas as pd
from vnstock3 import Vnstock
import os
from datetime import datetime, timedelta
from io import StringIO
from loguru import logger
from pathlib import Path

from vietlott.config.products import get_config
from vietlott.model.strategy.random import RandomModel

# Đọc API key từ biến môi trường
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("API key for Gemini AI is not set. Please configure the GEMINI_API_KEY environment variable.")

# Cấu hình API key cho Gemini AI
genai.configure(api_key=API_KEY)
import pandas as pd


def _balance_long_df(df_: pd.DataFrame, n_splits: int = 20):
    """Convert long dataframe to multiple columns."""
    # Reset index một lần, không cần nhiều lần
    df_ = df_.reset_index(drop=True)
    df_["result"] = df_["result"].astype(str)

    # Kiểm tra và tạo cột 'count' nếu chưa có
    if 'count' not in df_.columns:
        df_['count'] = df_.groupby('result')['result'].transform('count')

    df_["count"] = df_["count"].astype(str)

    # Chia DataFrame thành các phần nhỏ và xây dựng kết quả
    result_parts = []
    for i in range(0, len(df_), n_splits):
        # Lấy phần nhỏ của DataFrame
        dd = df_.iloc[i:i + n_splits]

        # Thêm phần đã chia vào danh sách kết quả, thêm dòng trống giữa các nhóm
        if result_parts:
            result_parts.append(pd.DataFrame([None] * len(dd), columns=["-"]))
        result_parts.append(dd)

    # Nối tất cả các phần lại với nhau theo chiều ngang
    final = pd.concat(result_parts, axis="columns").fillna("")

    return final


def read_data(data_dir: Path):
    df_files = [
        pd.read_json(str(file), dtype=False, convert_dates=False, lines=True) for file in data_dir.glob("*.jsonl")
    ]
    logger.info("df_files: %d", len(df_files))
    logger.info(df_files[0])
    df = pd.concat(df_files, axis="rows")
    return df


def read_data_str(data_dir: Path):
    string = ""
    for file in data_dir.glob("*.jsonl"):
        string += file.open("r").read()
    df = pd.read_json(StringIO(string), lines=True, dtype=object, convert_dates=False)
    return df


def analyze_with_gemini(prompt):
    """Gửi yêu cầu phân tích tới Gemini AI và trả về kết quả."""
    try:
        # Kết nối đến mô hình Gemini AI
        model = genai.GenerativeModel("gemini-1.5-flash")
        print('xxx', prompt)

        # Gửi prompt phân tích
        response = model.generate_content(prompt)

        # Trả về nội dung phản hồi
        print(response.text)
    except Exception as e:
        error_message = f"Đã có lỗi xảy ra khi gửi yêu cầu đến Gemini AI: {str(e)}"
        return error_message


def main():
    df = pd.read_json(get_config("power_655").raw_path, lines=True, dtype=object, convert_dates=False)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df = df.sort_values(by=["date", "id"], ascending=False)

    def fn_stats(df_):
        df_explode = df_.explode("result")
        stats = df_explode.groupby("result").agg(count=("id", "count"))
        stats["%"] = (stats["count"] / len(df_explode) * 100).round(2)
        return stats

    stats = _balance_long_df(fn_stats(df))

    # stats n months
    # stats_15d = _balance_long_df(fn_stats(df[df["date"] >= (datetime.now().date() - timedelta(days=15))]))
    stats_30d = _balance_long_df(fn_stats(df[df["date"] >= (datetime.now().date() - timedelta(days=30))]))
    stats_60d = _balance_long_df(fn_stats(df[df["date"] >= (datetime.now().date() - timedelta(days=60))]))
    stats_90d = _balance_long_df(fn_stats(df[df["date"] >= (datetime.now().date() - timedelta(days=90))]))

    # predictions
    ticket_per_days = 20
    random_model = RandomModel(df, ticket_per_days)
    random_model.backtest()
    random_model.evaluate()
    df_random_correct = random_model.df_backtest_evaluate[random_model.df_backtest_evaluate["correct_num"] >= 5][
        ["date", "result", "predicted"]
    ]
    stats_markdown = stats_30d.to_string(index=False)

    prompt = f"""Dữ liệu phân tích kết quả kinh doanh từ xổ số Vietlot:

        {stats_markdown}

        Dưạ vào số phần trăm và count hãy cho 1 dãy  6 số có khả năng tiếp theo"""


    output_str = f"""# Vietlot data


### random strategy
predicted: {ticket_per_days} / day ({ticket_per_days} tickets perday or {10000 * ticket_per_days:,d} vnd)
predicted corrected:
{df_random_correct.to_markdown()} 

# ## raw details 6/55 last 10 days
# {df.head(10).to_markdown(index=False)}
## stats 6/55 all time
{stats.to_markdown(index=False)}
# ## stats 6/55 -15d
# {stats_30d.to_markdown(index=False)}
# ## stats 6/55 -30d
# {stats_30d.to_markdown(index=False)}
# ## stats 6/55 -60d
# {stats_60d.to_markdown(index=False)}
# ## stats 6/55 -90d
# {stats_90d.to_markdown(index=False)}

"""
    path_output = Path("./readme.md")
    with path_output.open("w") as ofile:
        logger.info(f"cwd: {Path.cwd()}")
        logger.info(f"writing to {path_output.absolute()}")
        ofile.write(output_str)

 # Gửi yêu cầu phân tích với Gemini AI
    analyze_with_gemini(prompt)

if __name__ == "__main__":
    main()

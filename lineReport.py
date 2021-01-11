from typing import List

import requests
import pandas
import sqlite3 as lite
import os
import time
import logging

from bs4 import BeautifulSoup
from selenium import webdriver


class Comics:
    def __init__(self, url, tableId, db, token):
        self.url = url
        self.tableId = tableId
        self.db = db
        self.token = token

    def run(self):
        maxSeries = self.get_max_series()
        maxSeriesDb = self.get_max_series_db()
        print("maxSeries = ", maxSeries)
        print("maxSeriesDb = ", maxSeriesDb)
        if maxSeries > maxSeriesDb:
            print("get new series")
            # 推播line
            # 存入DB
        else:
            print("just fun")

    # 目前還差的集數
    def check_comics(self):
        max_series_db = self.get_max_series_db()
        max_series = self.get_max_series()
        left_comics = []
        print("max_series_db = ", max_series_db)
        print("max_series = ", max_series)

        for i in range(max_series_db, max(max_series)):
            left_comics.append(i + 1)
        self.change_type_pandas(max_series)
        return left_comics

    # 利用網路爬蟲檢查網路上最新的集數
    def get_max_series(self):
        res = requests.get(self.url)
        res.encoding = "cp950"
        soup = BeautifulSoup(res.text, "html.parser")
        comics = []
        for rec in soup.select(self.tableId):
            comics.append(int(rec.get("id").strip("c")))
        return comics

    def change_type_pandas(self, comics):
        comic_df = pandas.DataFrame(comics)
        comic_df.columns = ['series']
        print("change success")
        self.save_db(comic_df)

    # 將抓取到的集數，寫到DB中
    def save_db(self, comic_df):
        with lite.connect(self.db) as db:
            comic_df.to_sql("comics", con=db, if_exists="replace")
        print("success input db")

    # 檢查資料庫中最新的集數
    def get_max_series_db(self):
        with lite.connect(self.db) as db:
            df2 = pandas.read_sql_query("select max(series) as max_series from comics", con=db)
        return df2["max_series"][0]

    def get_comic(self, series):
        driver = webdriver.Edge(executable_path="msedgedriver.exe")
        for ser in series:
            if not os.path.exists(str(ser)):
                # 創建資料夾 EX:960
                os.mkdir(str(ser))

            pageUrl = "https://comicbus.live/online/a-103.html?ch={}-{}"
            driver.get(pageUrl.format(ser, 1))
            time.sleep(0.1)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            pageNum = int(soup.select_one("#pagenum").text.split("/")[1].strip("頁"))
            print(f"第{ser}集，共{pageNum}頁")
            for i in range(1, pageNum + 1):
                driver.get(pageUrl.format(ser, i + 1))
                soup = BeautifulSoup(driver.page_source, "html.parser")
                imgUrl = "https:" + soup.select_one("#TheImg").get("src")
                res = requests.get(imgUrl)
                with open("{0}/{1:02d}.jpg".format(ser, i), "wb") as f:
                    f.write(res.content)
                time.sleep(0.2)
                print(f"目前第{i}頁")
        driver.close()

    def image_file(self, series):
        list = []
        for dir in series:
            for item in os.listdir(r"./" + str(dir)):
                list.append(open(str(dir) + "/" + item, "rb"))
        return list

    def send_line(self, series: List[int]):
        headers = {
            "Authorization": "Bearer " + self.token
        }

        payload = {
            "message": "最新一期漫畫"
        }

        files = self.image_file(series)

        logging.info(f"files: {files}")
        res = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload)
        for file in files:
            files = {
                "imageFile": file
            }
            res = requests.post("https://notify-api.line.me/api/notify", headers=headers, files=files)
        return res.status_code


if __name__ == "__main__":
    url = "https://www.comicbus.com/html/103.html"
    tableId = "#rp_ctl05_0_dl_0 td a"
    db = "comics.sqlite"
    token = "BNd97897iKbRHpC8LDvc0bFzdjxc3VHnfhbUCeAqysl"
    # token = "MVQrVuDuszSdkd7ZYyCNXVZOZi00dCtH6R76lIrODCM"
    comics = Comics(url=url, tableId=tableId, db=db, token=token)

    comics.send_line([960])
    # left_comic = Comics.check_comics()
    # print(left_comic)
    # left_comic = [962]
    # Comics.get_comic(left_comic)
    # print(Comics.send_line(left_comic))

    # client_id = "1653409578"
    # client_secret = "7c97bed9561b49b335895778a9c71380"
    # access_token = "cBww7Ih93+0MGE7x7DJw1Fx9THAzvqXnZzzwY5CQ+ewI405qF94SJrwoUomTOxNbiEqOlDazjdpFzLOwdkboiK69aT9O3t7a9epgbTQ5e7/1RWeapmdT4bOMduBHmIPgA0w7SxPG8okkBRciuLtPvwdB04t89/1O/w1cDnyilFU="
    # headers = {
    #     "Authorization": "Bearer " + token,
    #     "Content-Type": "application/x-www-form-urlencoded"
    # }


    # payload = {"message": "123"}
    # r = requests.post(url="https://notify-api.line.me/api/notify", headers=headers, params=payload)
    # print(r.status_code)

    # files = {
    #     "imageFile": open("960/01.jpg", "rb")
    # }
    #
    # res = requests.post("https://imgur.com/a/test", headers=headers, files=files)
    # print(res.status_code)

# res = requests.get("https://www.comicbus.com/html/103.html")
# # 當python 輸出字串到terminal時，會檢查終端機上使用的編碼，並將unicode字串轉換成terminal支援的編碼
# # linux -> utf-8
# # window -> cp950
# res.encoding = 'cp950'
# # print(res.text)
#
# soup = BeautifulSoup(res.text, 'html.parser')
# comics = []
#
# for rec in soup.select("#rp_ctl05_0_dl_0 td a"):
#     comics.append(int(rec.get("id").strip("c")))
#
# print(max(comics))
#
# comic_df = pandas.DataFrame(comics)
# comic_df.columns = ['series']
# print(comic_df)
#
# with lite.connect("comics.sqlite") as db:
#     comic_df.to_sql("comics", con=db, if_exists="replace")
#
# with lite.connect("comics.sqlite") as db:
#     df2 = pandas.read_sql_query("select max(series) as max_series from comics", con=db)
# max_series = df2["max_series"][0]
# print(max_series)

from typing import List

import argparse
import requests
import pandas
import sqlite3 as lite
import os
import time
import logging

from bs4 import BeautifulSoup
from selenium import webdriver


def default_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("--url", default="https://www.comicbus.com/html/103.html",
                        help="Listening comic url")
    parser.add_argument("--db_name", default="comics.sqlite",
                        help="Set DB name")
    parser.add_argument("--executable_path", default="msedgedriver.exe",
                        help="Set webdriver executable_path")
    args = parser.parse_args()
    return args


class Response:
    def __init__(self):
        self._status_code = 400
        self._error_msg = "error"

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, i_status_code):
        self._status_code = i_status_code

    @property
    def error_msg(self):
        return self._error_msg

    @error_msg.setter
    def error_msg(self, i_error_msg):
        self._error_msg = i_error_msg


class Comics:
    def __init__(self):
        args = default_args()
        logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING)
        self.url = args.url
        self.page_url = "https://comicbus.live/online/a-103.html?ch={}-{}"
        self.tableId = "#rp_ctl05_0_dl_0 td a"
        self.db_name = args.db_name
        self.token = "BNd97897iKbRHpC8LDvc0bFzdjxc3VHnfhbUCeAqysl"
        self.executable_path = args.executable_path
        self.driver = None
        self.check_sqlite()

    def check_sqlite(self):
        """check sqlite is exists?"""
        sql = f"create table if not exists comics (series integer)"
        with lite.connect(self.db_name) as db:
            c = db.cursor()
            c.execute(sql)

    def run(self):
        last_comics: List[int] = self.check_comics()
        try:
            self.driver = webdriver.Edge(executable_path=self.executable_path)
            if last_comics:
                logging.info("get new series")
                # 推播line
                for comic in last_comics:
                    if not os.path.exists(str(comic)):
                        os.mkdir(str(comic))  # 創建資料夾 EX:960

                    self.driver.get(self.page_url.format(comic, 1))
                    time.sleep(0.1)
                    soup = BeautifulSoup(self.driver.page_source, "html.parser")
                    page_num = int(soup.select_one("#pagenum").text.split("/")[1].strip("頁"))
                    logging.info(f"第{comic}集，共{page_num}頁")
                    self.catch_comics_picture(comic=comic, page_num=page_num)
                return self.send_line(last_comics)
            else:
                logging.info("just fun")
        except Exception as e:
            logging.error(f"error.. : {e}")
        finally:
            logging.info("close driver")
            self.driver.close()

    def check_comics(self) -> List[int]:
        """目前還差的集數"""
        max_series_db = self.get_max_series_db()
        max_series = self.get_max_series()
        max_series_db = max_series_db if max_series_db else max_series[0]
        last_comics = []
        logging.info(f"max_series_db = {max_series_db}")
        logging.info(f"max_series size = {len(max_series)}\nmax_series = {max_series}")

        for i in range(max_series_db, max(max_series)):
            last_comics.append(i + 1)
        self.change_type_pandas(max_series)
        return last_comics

    def get_max_series(self) -> List[int]:
        """利用網路爬蟲檢查網路上最新的集數"""
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
        logging.info("change success")
        self.save_db(comic_df)

    def save_db(self, comic_df):
        """將抓取到的集數，寫到DB中"""
        with lite.connect(self.db_name) as db:
            comic_df.to_sql("comics", con=db, if_exists="replace")
        logging.info("success input db")

    def get_max_series_db(self):
        """檢查資料庫中最新的集數"""
        with lite.connect(self.db_name) as db:
            df2 = pandas.read_sql_query("select max(series) as max_series from comics", con=db)
        return df2["max_series"][0]

    def catch_comics_picture(self, comic: int, page_num: int):
        """抓取漫畫圖片"""
        for i in range(1, page_num + 1):
            self.driver.get(self.page_url.format(comic, i + 1))
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            imgUrl = "https:" + soup.select_one("#TheImg").get("src")
            res = requests.get(imgUrl)
            with open("{0}/{1:02d}.jpg".format(comic, i), "wb") as f:
                f.write(res.content)
            time.sleep(0.5)
            logging.info(f"目前第{i}頁")

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
        # res = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload)
        res = Response()
        for file in files:
            files = {
                "imageFile": file
            }

            payload["message"] = file.name
            req = requests.post("https://notify-api.line.me/api/notify", headers=headers, data=payload, files=files)
            time.sleep(0.1)
            if req.status_code != 200:
                res.status_code = req.status_code
                res.error_msg = req.text
                break
        return res.status_code, res.error_msg


if __name__ == "__main__":
    comics = Comics()
    print(comics.run())

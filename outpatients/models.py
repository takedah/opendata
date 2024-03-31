import csv
import json
import logging
import os
import re
import unicodedata
import urllib.parse
from abc import ABCMeta, abstractmethod
from io import BytesIO, StringIO
from typing import Union

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from dotenv import load_dotenv
from markupsafe import escape

load_dotenv()
YOLP_APP_ID = os.environ.get("YOLP_APP_ID")


class OutpatientManager(models.Manager):
    def upsert(self, source: dict, user: User) -> bool:
        outpatient, created = self.update_or_create(
            medical_institution_name=source["medical_institution_name"],
            created_by=user,
            defaults=source,
        )
        return created

    def delete(self, medical_institution_name: str) -> bool:
        if self.filter(medical_institution_name=medical_institution_name).exists():
            self.filter(medical_institution_name=medical_institution_name).delete()
            return True
        else:
            return False

    def medical_institution_names_list(self) -> list:
        return list(self.values_list("medical_institution_name", flat=True))


class Outpatient(models.Model):
    is_outpatient = models.BooleanField("外来対応医療機関", default=False)
    is_positive_patients = models.BooleanField(
        "陽性者の治療に関与する医療機関", default=False
    )
    public_health_care_center = models.TextField("保健所", blank=True, null=True)
    medical_institution_name = models.CharField("医療機関名", max_length=256)
    city = models.TextField("市町村", blank=True, null=True)
    address = models.TextField("住所", blank=True, null=True)
    phone_number = models.TextField("電話番号", blank=True, null=True)
    is_target_not_family = models.BooleanField(
        "かかりつけ患者以外の診療", default=False
    )
    is_pediatrics = models.BooleanField("小児対応の可否", default=False)
    mon = models.TextField("月", blank=True, null=True)
    tue = models.TextField("火", blank=True, null=True)
    wed = models.TextField("水", blank=True, null=True)
    thu = models.TextField("木", blank=True, null=True)
    fri = models.TextField("金", blank=True, null=True)
    sat = models.TextField("土", blank=True, null=True)
    sun = models.TextField("日", blank=True, null=True)
    is_face_to_face_for_positive_patients = models.BooleanField(
        "外来対応", default=False
    )
    is_online_for_positive_patients = models.BooleanField(
        "オンライン診療", default=False
    )
    is_home_visitation_for_positive_patients = models.BooleanField(
        "訪問診療", default=False
    )
    memo = models.TextField("備考", blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="作成者", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("作成日", auto_now_add=True)
    update_at = models.DateTimeField("更新日", auto_now=True)
    objects = OutpatientManager()

    def __str__(self):
        return self.medical_institution_name


class LocationManager(models.Manager):
    def upsert(self, source: dict, user: User) -> bool:
        outpatient, created = self.update_or_create(
            medical_institution_name=source["medical_institution_name"],
            created_by=user,
            defaults=source,
        )
        return created

    def delete(self, medical_institution_name: str) -> bool:
        if self.filter(medical_institution_name=medical_institution_name).exists():
            self.filter(medical_institution_name=medical_institution_name).delete()
            return True
        else:
            return False


class Location(models.Model):
    medical_institution_name = models.CharField("医療機関名", max_length=256)
    latitude = models.FloatField("緯度", default=0)
    longitude = models.FloatField("経度", default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="作成者", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("作成日", auto_now_add=True)
    update_at = models.DateTimeField("更新日", auto_now=True)
    objects = LocationManager()

    def __str__(self):
        return self.medical_institution_name


class Downloader(metaclass=ABCMeta):
    def __init__(self):
        @property
        @abstractmethod
        def content(self):
            pass


class DownloadCSV(Downloader):
    """CSV ファイルの StringIO データの取得

    Web サイトから CSV ファイルをダウンロードして内容を StringIO で返す。

    Attributes:
        content (:obj:`StringIO`): ダウンロードした CSV ファイルの StringIO データ

    """

    def __init__(self, url: str, encoding: str = "utf-8"):
        """
        Args:
            url (str): Web サイトの CSV ファイルの URL
            encoding (str): CSV ファイルの文字コード

        """
        Downloader.__init__(self)
        self.__content = self._get_csv_content(url, encoding=encoding)

    @property
    def content(self) -> StringIO:
        return self.__content

    def _get_csv_content(self, url: str, encoding: str) -> StringIO:
        """Web サイトから CSV ファイルの StringIO データを取得

        Args:
            url (str): CSV ファイルの URL
            encoding (str): CSV ファイルの文字コード

        Returns:
            content (:obj:`StringIO`): ダウンロードした CSV ファイルの StringIO データ

        """
        logger = logging.getLogger(__name__)
        response = requests.get(url)
        csv_io = StringIO(response.content.decode(encoding))
        logger.info("CSV ファイルのダウンロードに成功しました。")
        return csv_io


class DownloadJSON(Downloader):
    """Web API から JSON データの取得

    Web サイトから JSON ファイルをダウンロードして辞書データに変換する。

    Attributes:
        content (:obj:`StringIO`): ダウンロードした JSON ファイルのデータ

    """

    def __init__(self, url: str):
        """
        Args:
            url (str): Web サイトの JSON ファイルの URL

        """
        Downloader.__init__(self)
        self.__content = self._get_json_content(url)

    @property
    def content(self) -> StringIO:
        return self.__content

    def _get_json_content(self, url: str) -> StringIO:
        """Web サイトから JSON ファイルのデータを取得

        Args:
            url (str): JSON ファイルの URL

        Returns:
            content (:obj:`StringIO`): ダウンロードした JSON ファイルのデータ

        """
        logger = logging.getLogger(__name__)
        response = requests.get(url)
        logger.info("JSON ファイルのダウンロードに成功しました。")
        return response.content


class DownloadExcel(Downloader):
    """Excel ファイルの BytesIO データの取得

    Web サイトから Excel ファイルをダウンロードして BytesIO で返す。

    Attributes:
        content (BytesIO): ダウンロードした Excel ファイルの BytesIO データ
        url (str): ダウンロードした Excel ファイルの URL

    """

    def __init__(self, url: str):
        """
        Args:
            url (str): Web サイトの Excel ファイルの URL

        """
        Downloader.__init__(self)
        self.__content = self._get_excel_content(url)

    @property
    def content(self) -> BytesIO:
        return self.__content

    def _get_excel_content(self, url: str) -> BytesIO:
        """Web サイトから Excel ファイルの BytesIO データを取得

        Args:
            url (str): Excel ファイルの URL

        Returns:
            excel_io (BytesIO): 発熱外来一覧 Excel データから抽出したデータ

        """
        logger = logging.getLogger(__name__)
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        logger.info("Excel ファイルのダウンロードに成功しました。")
        return BytesIO(response.content)


class DownloadHTML(Downloader):
    """HTMLファイルのbytesデータの取得

    WebサイトからHTMLファイルをダウンロードしてbytesデータに変換する。

    Attributes:
        content (bytes): ダウンロードしたHTMLファイルのbytesデータ
        url (str): HTMLファイルのURL

    """

    def __init__(self, url: str):
        """
        Args:
            url (str): WebサイトのHTMLファイルのURL

        """
        Downloader.__init__(self)
        self.__url = url
        self.__content = self._get_html_content(self.__url)

    @property
    def content(self) -> bytes:
        return self.__content

    @property
    def url(self) -> str:
        return self.__url

    def _get_html_content(self, url: str) -> bytes:
        """WebサイトからHTMLファイルのbytesデータを取得

        Args:
            url (str): HTMLファイルのURL

        Returns:
            content (bytes): ダウンロードしたHTMLファイルのbytesデータ

        """
        logger = logging.getLogger(__name__)
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response = requests.get(url)
        logger.info("HTMLファイルのダウンロードに成功しました。")
        return response.content


class Scraper:
    def normalize(self, text: str) -> str:
        """文字列から余計な空白等を取り除き、全角数字等を正規化して返す

        Args:
            text (str): 正規化したい文字列

        Returns:
            nomalized_text (str): 正規化後の文字列

        """
        if not isinstance(text, str):
            return ""

        if text == "0":
            return ""

        return unicodedata.normalize("NFKC", self._format_string(text))

    def _format_string(self, text: str) -> str:
        """改行を半角スペースに置換し、文字列から連続する半角スペースを除去する

        Args:
            text (str): 整形前の文字列

        Returns:
            formatted_str (str): 整形後の文字列

        """
        if isinstance(text, str):
            return re.sub(
                "( +)",
                " ",
                text.replace("　", " ").replace("\r", " ").replace("\n", " ").strip(),
            )
        else:
            return ""


class ScrapeOutpatientSourceURL:
    """旭川市新型コロナウイルス発熱外来データ Excel ファイルのリンクの抽出

    北海道公式ホームページから旭川市の新型コロナウイルス発熱外来データ Excel ファイルの
    リンクを抽出する。

    """

    @classmethod
    def get(self, html_url: str) -> str:
        """スクレイピングの元 Excel ファイルの URL を抽出して返す

        Args:
            html_url (str): HTML ファイルの URL

        Returns:
            url (str): 発熱外来一覧 Excel ファイルの URL

        """
        url = ""
        downloaded_html = DownloadHTML(html_url)
        soup = BeautifulSoup(downloaded_html.content, "html.parser")
        for article in soup.find_all("article"):
            # id 属性などで対象を絞れないため div 要素を全てなめる。
            # 子要素に a 要素があれば href 属性を取得し、それが Excel ファイルへのリンクか判断。
            # 更に a 要素の子要素に img 要素がありalt属性の値に「旭川」を含んでいればリンク文字列を取得。
            for div in soup.find_all("div"):
                a = div.find("a")
                if a:
                    href = a.get("href")
                    if href:
                        if re.match(r"^.*.xlsx$", href):
                            img = div.find("img")
                            if img:
                                alt = img.get("alt")
                                if alt:
                                    if re.match("^.*旭川.*$", alt):
                                        url = "https://www.pref.hokkaido.lg.jp" + href

        return url


class ScrapeOutpatient(Scraper):
    """旭川市新型コロナウイルス発熱外来データの抽出

    北海道公式ホームページからダウンロードした Excel ファイルのデータから、
    旭川市の新型コロナウイルス発熱外来データを抽出し、リストに変換する。

    Attributes:
        outpatient_data (list of dict): 旭川市の発熱外来データ
            旭川市の新型コロナウイルス発熱外来データを表す辞書のリスト

    """

    def __init__(self, excel_url: str):
        """
        Args:
            excel_url (str): 北海道公式ホームページ発熱外来一覧表 Excel ファイルの URL

        """
        excel_lists = self._get_excel_lists(excel_url)
        self.__lists = list()
        for excel_row in excel_lists:
            if excel_row:
                self.__lists.append(self._get_outpatient(excel_row))

    @property
    def lists(self) -> list:
        return self.__lists

    def _get_excel_lists(self, excel_url: str) -> list:
        """
        Args:
            excel_url (str): 北海道公式ホームページ発熱外来一覧表 Excel ファイルの URL

        Returns:
            excel_lists (list of list): 北海道の発熱外来 Excel データ
                北海道の新型コロナウイルス発熱外来一覧表 Excel データから抽出した表データを、
                二次元配列のリストで返す。

        """
        excel_file = DownloadExcel(excel_url)
        df = pd.read_excel(
            excel_file.content,
            sheet_name="Sheet1",
            header=None,
            index_col=None,
            skiprows=[0, 1, 2],
            dtype=str,
        )
        df.replace(np.nan, "", inplace=True)
        return df.values.tolist()

    def _get_outpatient(self, excel_row: list) -> dict:
        """
        Args:
            row (list): Excel ファイルから抽出した二次元配列データ

        Returns:
            outpatient_data (dict): 発熱外来データ
                Excel ファイルから抽出した発熱外来データの辞書

        """
        if excel_row is None:
            return None

        excel_row = list(map(lambda x: self.normalize(x), excel_row))
        outpatient: dict[str, Union[str, bool]] = dict()
        is_target_not_family = False
        if excel_row[7] == "かかりつけ患者以外の診療も可":
            is_target_not_family = True

        is_positive_patients = self._get_available(excel_row[1])
        is_face_to_face_for_positive_patients = False
        is_online_for_positive_patients = False
        is_home_visitation_for_positive_patients = False
        if is_positive_patients:
            is_face_to_face_for_positive_patients = self._get_available(excel_row[51])
            is_online_for_positive_patients = self._get_available(excel_row[52])
            is_home_visitation_for_positive_patients = self._get_available(
                excel_row[53]
            )

        address = excel_row[5].replace("北海道", "")
        outpatient = {
            "is_outpatient": self._get_available(excel_row[0]),
            "is_positive_patients": is_positive_patients,
            "public_health_care_center": excel_row[2],
            "medical_institution_name": excel_row[3].replace(" ", ""),
            "city": excel_row[4],
            "address": address,
            "phone_number": excel_row[6],
            "is_target_not_family": is_target_not_family,
            "is_pediatrics": self._get_available(excel_row[8]),
            "mon": self._get_opening_hours(excel_row[9:15]),
            "tue": self._get_opening_hours(excel_row[15:21]),
            "wed": self._get_opening_hours(excel_row[21:27]),
            "thu": self._get_opening_hours(excel_row[27:33]),
            "fri": self._get_opening_hours(excel_row[33:39]),
            "sat": self._get_opening_hours(excel_row[39:45]),
            "sun": self._get_opening_hours(excel_row[45:51]),
            "is_face_to_face_for_positive_patients": is_face_to_face_for_positive_patients,
            "is_online_for_positive_patients": is_online_for_positive_patients,
            "is_home_visitation_for_positive_patients": is_home_visitation_for_positive_patients,
            "memo": excel_row[57],
        }
        return outpatient

    def _get_available(self, text: str) -> bool:
        """文字列がマルなら真を、そうでなければ偽を返す

        Args:
            text (str): 判定したい文字列

        Returns:
            result (bool): 文字列がマルなら真を、そうでなければ偽

        """
        result = False
        ok_match = re.search("^(.*)[○|〇](.*)$", text)
        if ok_match:
            result = True

        return result

    def _get_opening_hours(self, target_list: list) -> str:
        """診療時間を表すリストを結合して文字列で返す

        Args:
            target_list (list): Excel から抽出した診療時間を表す文字列のリスト

        Returns:
            opening_hours (str): リストが診療時間を表していたら文字列を結合して返す

        """
        am = ""
        pm = ""
        am_start = self._strip_if_time_format(target_list[0])
        am_end = self._strip_if_time_format(target_list[2])
        pm_start = self._strip_if_time_format(target_list[3])
        pm_end = self._strip_if_time_format(target_list[5])
        if am_start != "00:00" or am_end != "00:00":
            am = am_start + "～" + am_end

        if pm_start != "00:00" or pm_end != "00:00":
            pm = pm_start + "～" + pm_end

        if am == "":
            return pm
        else:
            if pm == "":
                return am
            else:
                return (am + "、" + pm).replace("～00:00、00:00～", "～")

    def _strip_if_time_format(self, target_text: str) -> str:
        """文字列が Excel の時刻表記文字列なら整形し、そうでないならそのまま文字列を返す

        Args:
            text (str): 判定したい文字列

        Returns:
            stripped_text (str):
                Excel の時刻表記文字列なら秒の部分を削除し、そうでないならそのまま文字列を返す

        """
        if not isinstance(target_text, str):
            return None

        time_format_match = re.search(
            "^.*([0-9]{2}):([0-9]{2}):([0-9]{2})$", target_text
        )
        if time_format_match:
            return time_format_match.group(1) + ":" + time_format_match.group(2)
        else:
            return target_text


class ScrapeOpendataLocation(Scraper):
    """北海道オープンデータポータルの CSV ファイルから医療機関の緯度経度情報を取得

    Attributes:
        lists (list of dict): 緯度経度データを表す辞書のリスト

    """

    def __init__(self, csv_url: str):
        """
        Args:
            csv_url (str): 北海道オープンデータポータルの CSV ファイルの URL

        """
        self.__lists = list()
        download_csv = DownloadCSV(url=csv_url, encoding="cp932")
        for row in self._get_table_values(download_csv):
            location_data = self._extract_location_data(row)
            if location_data:
                self.__lists.append(location_data)

    @property
    def lists(self) -> list:
        return self.__lists

    def _get_table_values(self, download_csv: DownloadCSV) -> list:
        """CSV から内容を抽出してリストに格納

        Args:
            downloaded_csv (:obj:`DownloadedCSV`): CSV ファイルのデータ
                ダウンロードした CSV ファイルの StringIO データを要素に持つオブジェクト

        Returns:
            table_values (list of list): CSV の内容で構成される二次元配列

        """
        table_values = list()
        reader = csv.reader(download_csv.content)
        next(reader)
        for row in reader:
            table_values.append(row)

        return table_values

    def _extract_location_data(self, row: list) -> dict:
        """北海道オープンデータポータルの CSV データから緯度経度情報を抽出

        Args:
            row (list): 北海道オープンデータポータルの CSV から抽出した行データ

        Returns:
            location_data (dict): 緯度経度の辞書データ

        """
        if len(row) != 37:
            return None

        row = list(map(lambda x: self.normalize(x), row))
        city = row[4]
        if city != "旭川市":
            return None

        try:
            location_data = {
                "medical_institution_name": row[5].replace(" ", ""),
                "longitude": float(row[12]),
                "latitude": float(row[11]),
            }
        except ValueError:
            return None

        return location_data


class ScrapeYOLPLocation:
    """Yahoo! Open Local Platform (YOLP) Web API から指定した施設の緯度経度情報を取得

    Attributes:
        lists (list of dict): 緯度経度データを表す辞書のリスト

    """

    def __init__(self, facility_name: str):
        """
        Args:
            facility_name (str): 緯度経度情報を取得したい施設の名称

        """
        self.__lists = list()
        if isinstance(facility_name, str):
            facility_name = urllib.parse.quote(escape(facility_name))
        else:
            raise TypeError("施設名の指定が正しくありません。")

        city_code = "01204"
        industry_code = "0401"
        if YOLP_APP_ID:
            app_id = YOLP_APP_ID
        else:
            raise RuntimeError("YOLP アプリケーション ID の指定が正しくありません。")

        json_url = (
            "https://map.yahooapis.jp/search/local/V1/localSearch"
            + "?appid="
            + app_id
            + "&query="
            + facility_name
            + "&ac="
            + city_code
            + "&gc="
            + industry_code
            + "&sort=-match&detail=simple&output=json"
        )
        download_json = DownloadJSON(json_url)
        for search_result in self._get_search_results(download_json):
            location_data = self._extract_location_data(search_result)
            location_data["medical_institution_name"] = urllib.parse.unquote(
                facility_name
            )
            self.__lists.append(location_data)

    @property
    def lists(self) -> list:
        return self.__lists

    def _get_search_results(self, download_json: DownloadJSON) -> list:
        """YOLP Web API の返す JSON データから検索結果データを抽出

        Args:
            download_json (:obj:`DownloadJSON`): JSON データを要素に持つオブジェクト

        Returns:
            search_results (list of dict): 検索結果辞書データリスト
                JSON データから検索結果の部分を辞書データで抽出したリスト

        """
        json_res = json.loads(download_json.content)
        try:
            if json_res["ResultInfo"]["Count"] == 0:
                # 検索結果が0件の場合、緯度経度にダミーの値をセットして返す
                search_results = [
                    {
                        "Geometry": {
                            "Coordinates": "0,0",
                        },
                    },
                ]
            else:
                search_results = json_res["Feature"]
            return search_results
        except KeyError:
            raise RuntimeError("期待した JSON レスポンスが得られていません。")

    def _extract_location_data(self, search_result: dict) -> dict:
        """YOLP Web API の返す JSON データから緯度経度情報を抽出

        Args:
            yolp_json (dict): YOLP Web API の返す JSON データ

        Returns:
            location_data (dict): 緯度経度の辞書データ

        """
        location_data = dict()
        coordinates = search_result["Geometry"]["Coordinates"].split(",")
        location_data["longitude"] = float(coordinates[0])
        location_data["latitude"] = float(coordinates[1])
        return location_data

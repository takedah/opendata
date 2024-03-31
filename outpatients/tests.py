from io import BytesIO

import pytest
import requests
from django.contrib.auth import get_user_model
from django.test import Client

from outpatients.models import (DownloadCSV, DownloadExcel, DownloadJSON,
                                Location, Outpatient, ScrapeOpendataLocation,
                                ScrapeOutpatient, ScrapeOutpatientSourceURL,
                                ScrapeYOLPLocation)


@pytest.mark.django_db
class TestOutpatient:
    @pytest.fixture()
    def user(self):
        UserModel = get_user_model()
        user = UserModel.objects.create(
            username="test_user",
            email="test@example.com",
            password="top_secret_pass0001",
        )
        return user

    @pytest.fixture()
    def client(self, user):
        client = Client()
        client.force_login(user)
        return client

    @pytest.fixture()
    def test_data(self):
        return {
            "市立旭川病院": {
                "is_outpatient": True,
                "is_positive_patients": True,
                "public_health_care_center": "旭川",
                "medical_institution_name": "市立旭川病院",
                "city": "旭川市",
                "address": "旭川市金星町1丁目1番65号",
                "phone_number": "0166-24-3181",
                "is_target_not_family": False,
                "is_pediatrics": True,
                "mon": "08:30～17:00",
                "tue": "08:30～17:00",
                "wed": "08:30～17:00",
                "thu": "08:30～17:00",
                "fri": "08:30～17:00",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": True,
                "is_online_for_positive_patients": True,
                "is_home_visitation_for_positive_patients": False,
                "memo": "かかりつけ患者及び保健所からの紹介患者に限ります。 https://www.city.asahikawa.hokkaido.jp/hospital/3100/d075882.html",
            },
            "JA北海道厚生連旭川厚生病院": {
                "is_outpatient": True,
                "is_positive_patients": False,
                "public_health_care_center": "旭川",
                "medical_institution_name": "JA北海道厚生連旭川厚生病院",
                "city": "旭川市",
                "address": "旭川市1条通24丁目111番地",
                "phone_number": "0166-33-7171",
                "is_target_not_family": True,
                "is_pediatrics": False,
                "mon": "08:30～11:30",
                "tue": "08:30～11:30",
                "wed": "08:30～11:30",
                "thu": "08:30～11:30",
                "fri": "08:30～11:30",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": False,
                "is_online_for_positive_patients": False,
                "is_home_visitation_for_positive_patients": False,
                "memo": "",
            },
            "旭川赤十字病院": {
                "is_outpatient": True,
                "is_positive_patients": True,
                "public_health_care_center": "旭川",
                "medical_institution_name": "旭川赤十字病院",
                "city": "旭川市",
                "address": "旭川市曙1条1丁目1番1号",
                "phone_number": "0166-22-8111",
                "is_target_not_family": False,
                "is_pediatrics": False,
                "mon": "",
                "tue": "",
                "wed": "",
                "thu": "",
                "fri": "",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": True,
                "is_online_for_positive_patients": False,
                "is_home_visitation_for_positive_patients": False,
                "memo": "「受診・相談センター」または保健所等の指示によら ず 受診した場合,初診時選定療養費を申し受けます。 当番制のため、不定期となっています。詳細はお問い合わせください。",
            },
            "おうみや内科クリニック": {
                "is_outpatient": False,
                "is_positive_patients": True,
                "public_health_care_center": "旭川",
                "medical_institution_name": "おうみや内科クリニック",
                "city": "旭川市",
                "address": "旭川市東光14条5丁目6番6号",
                "phone_number": "0166-39-3636",
                "is_target_not_family": True,
                "is_pediatrics": False,
                "mon": "",
                "tue": "",
                "wed": "",
                "thu": "",
                "fri": "",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": False,
                "is_online_for_positive_patients": False,
                "is_home_visitation_for_positive_patients": False,
                "memo": "",
            },
        }

    def test_create_outpatient_by_form(self, client, test_data):
        client.post("/outpatients/new/", test_data["市立旭川病院"])
        outpatient = Outpatient.objects.get(medical_institution_name="市立旭川病院")
        assert (
            outpatient.memo
            == "かかりつけ患者及び保健所からの紹介患者に限ります。 https://www.city.asahikawa.hokkaido.jp/hospital/3100/d075882.html"
        )

    def test_upsert_create_outpatient(self, test_data, user):
        create_result = Outpatient.objects.upsert(
            source=test_data["市立旭川病院"], user=user
        )
        assert create_result

    def test_upsert_update_outpatient(self, test_data, user):
        test_update_data = {
            "is_outpatient": True,
            "is_positive_patients": True,
            "public_health_care_center": "旭川",
            "medical_institution_name": "市立旭川病院",
            "city": "旭川市",
            "address": "旭川市金星町1丁目1番65号",
            "phone_number": "0166-24-3181",
            "is_target_not_family": False,
            "is_pediatrics": True,
            "mon": "08:30～17:00",
            "tue": "08:30～17:00",
            "wed": "08:30～17:00",
            "thu": "08:30～17:00",
            "fri": "08:30～17:00",
            "sat": "",
            "sun": "",
            "is_face_to_face_for_positive_patients": True,
            "is_online_for_positive_patients": True,
            "is_home_visitation_for_positive_patients": False,
            "memo": "アップデートのテスト",
        }
        Outpatient.objects.upsert(source=test_data["市立旭川病院"], user=user)
        create_result = Outpatient.objects.upsert(source=test_update_data, user=user)
        assert create_result is False
        outpatient = Outpatient.objects.get(medical_institution_name="市立旭川病院")
        assert outpatient.memo == "アップデートのテスト"

    def test_delete_outpatient(self, test_data, user):
        Outpatient.objects.upsert(source=test_data["市立旭川病院"], user=user)
        result = Outpatient.objects.delete("市立旭川病院")
        assert result

    def test_delete_not_exist_outpatient(self, test_data, user):
        Outpatient.objects.upsert(source=test_data["市立旭川病院"], user=user)
        result = Outpatient.objects.delete("旭川赤十字病院")
        assert result is False

    def test_medical_institution_names_list(self, test_data, user):
        for value in test_data.values():
            Outpatient.objects.upsert(source=value, user=user)

        medical_institution_names_list = (
            Outpatient.objects.medical_institution_names_list()
        )
        expect = [
            "市立旭川病院",
            "JA北海道厚生連旭川厚生病院",
            "旭川赤十字病院",
            "おうみや内科クリニック",
        ]
        assert medical_institution_names_list == expect


@pytest.mark.django_db
class TestLocation:
    @pytest.fixture()
    def user(self):
        UserModel = get_user_model()
        user = UserModel.objects.create(
            username="test_user",
            email="test@example.com",
            password="top_secret_pass0001",
        )
        return user

    @pytest.fixture()
    def test_data(self):
        return {
            "旭川赤十字病院": {
                "medical_institution_name": "旭川赤十字病院",
                "longitude": 142.348303888889,
                "latitude": 43.769628888889,
            },
            "市立旭川病院": {
                "medical_institution_name": "市立旭川病院",
                "longitude": 142.365976388889,
                "latitude": 43.778422777778,
            },
            "独立行政法人国立病院機構旭川医療センター": {
                "medical_institution_name": "独立行政法人国立病院機構旭川医療センター",
                "longitude": 142.3815237271935,
                "latitude": 43.798826491523464,
            },
            "森山病院": {
                "medical_institution_name": "森山病院",
                "longitude": 142.362565555556,
                "latitude": 43.781208333333,
            },
        }

    def test_upsert_create_outpatient(self, test_data, user):
        create_result = Location.objects.upsert(
            source=test_data["市立旭川病院"], user=user
        )
        assert create_result

    def test_upsert_update_outpatient(self, test_data, user):
        test_update_data = {
            "medical_institution_name": "市立旭川病院",
            "longitude": 143,
            "latitude": 44,
        }
        Location.objects.upsert(source=test_data["市立旭川病院"], user=user)
        create_result = Location.objects.upsert(source=test_update_data, user=user)
        assert create_result is False
        outpatient = Location.objects.get(medical_institution_name="市立旭川病院")
        assert outpatient.longitude == 143

    def test_delete_outpatient(self, test_data, user):
        Location.objects.upsert(source=test_data["市立旭川病院"], user=user)
        result = Location.objects.delete("市立旭川病院")
        assert result

    def test_delete_not_exist_outpatient(self, test_data, user):
        Location.objects.upsert(source=test_data["市立旭川病院"], user=user)
        result = Location.objects.delete("旭川赤十字病院")
        assert result is False


class TestDownloadCSV:
    @pytest.fixture()
    def csv_content(self):
        csv_content = """
No,全国地方公共団体コード,都道府県名,市区町村名,公表_年月日,発症_年月日,患者_居住地,患者_年代,患者_性別,患者_職業,患者_状態,患者_症状,患者_渡航歴の有無フラグ,患者_再陽性フラグ,患者_退院済フラグ,備考
1,10006,北海道,,2020-01-28,2020-01-21,中国武漢市,40代,女性,−,−,発熱,1,0,,海外渡航先：中国武漢
2,10006,北海道,,2020-02-14,2020-01-31,石狩振興局管内,50代,男性,自営業,−,発熱;咳;倦怠感,0,0,,
3,10006,北海道,,2020-02-19,2020-02-08,石狩振興局管内,40代,男性,会社員,−,倦怠感;筋肉痛;関節痛;発熱;咳,0,0,,
    """
        return csv_content.encode("cp932")

    def test_content(self, csv_content, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.content = csv_content
        responce_mock.headers = {"content-type": "text/csv"}
        mocker.patch.object(requests, "get", return_value=responce_mock)
        csv_file = DownloadCSV(url="http://dummy.local", encoding="cp932")
        assert csv_file.content.getvalue() == csv_content.decode("cp932")


class TestDownloadJSON:
    @pytest.fixture()
    def json_content(self):
        return """
{
    "ResultInfo": {
        "Count": 1,
        "Total": 1,
        "Start": 1,
        "Status": 200,
        "Description": "",
        "Copyright": "",
        "Latency": 0.017
    },
    "Feature": [
        {
            "Id": "20130710667",
            "Gid": "",
            "Name": "\u5e02\u7acb\u65ed\u5ddd\u75c5\u9662",
            "Geometry": {
                "Type": "point",
                "Coordinates": "142.365976388889,43.778422777778"
            },
            "Category": []
        }
    ]
}
        """

    def test_content(self, json_content, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.content = json_content
        responce_mock.headers = {"content-type": "application/json"}
        mocker.patch.object(requests, "get", return_value=responce_mock)
        json_file = DownloadJSON("http://dummy.local")
        assert json_file.content == json_content


class TestDownloadExcel:
    @pytest.fixture()
    def excel_content(self):
        return bytes()

    def test_content(self, excel_content, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.content = excel_content
        responce_mock.headers = {
            "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        mocker.patch.object(requests, "get", return_value=responce_mock)
        excel_file = DownloadExcel("http://dummy.local")
        assert isinstance(excel_file.content, BytesIO)


class TestScrapeOutpatient:
    @pytest.fixture()
    def excel_lists(self):
        return [
            [
                "○",
                "○",
                "旭川",
                "市立旭川病院",
                "旭川市",
                "旭川市金星町１丁目１番６５号",
                "0166-24-3181",
                "かかりつけ患者の診療に限る",
                "○",
                "08:30:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "17:00:00",
                "08:30:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "17:00:00",
                "08:30:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "17:00:00",
                "08:30:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "17:00:00",
                "08:30:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "17:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "○",
                "○",
                "0",
                "○",
                "○",
                "○",
                "かかりつけ患者及び保健所からの紹介患者に限ります。\u3000https://www.city.asahikawa.hokkaido.jp/hospital/3100/d075882.html",
            ],
            [
                "○",
                "0",
                "旭川",
                "ＪＡ北海道厚生連\u3000旭川厚生病院",
                "旭川市",
                "旭川市１条通24丁目111番地",
                "0166-33-7171",
                "かかりつけ患者以外の診療も可",
                "0",
                "08:30:00",
                "～",
                "11:30:00",
                "00:00:00",
                "～",
                "00:00:00",
                "08:30:00",
                "～",
                "11:30:00",
                "00:00:00",
                "～",
                "00:00:00",
                "08:30:00",
                "～",
                "11:30:00",
                "00:00:00",
                "～",
                "00:00:00",
                "08:30:00",
                "～",
                "11:30:00",
                "00:00:00",
                "～",
                "00:00:00",
                "08:30:00",
                "～",
                "11:30:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            [
                "○",
                "○",
                "旭川",
                "旭川赤十字病院",
                "旭川市",
                "旭川市曙１条１丁目1番１号",
                "0166-22-8111",
                "かかりつけ患者の診療に限る",
                "0",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "00:00:00",
                "～",
                "00:00:00",
                "○",
                "0",
                "0",
                "○",
                "○",
                "○",
                "「受診・相談センター」または保健所等の指示によら ず\n受診した場合，初診時選定療養費を申し受けます。\n当番制のため、不定期となっています。詳細はお問い合わせください。",
            ],
        ]

    def test_lists(self, excel_lists, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.headers = {
            "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        mocker.patch.object(requests, "get", return_value=responce_mock)
        mocker.patch.object(
            ScrapeOutpatient, "_get_excel_lists", return_value=excel_lists
        )
        scraper = ScrapeOutpatient(excel_url="http://dummy.local")
        expect = [
            {
                "is_outpatient": True,
                "is_positive_patients": True,
                "public_health_care_center": "旭川",
                "medical_institution_name": "市立旭川病院",
                "city": "旭川市",
                "address": "旭川市金星町1丁目1番65号",
                "phone_number": "0166-24-3181",
                "is_target_not_family": False,
                "is_pediatrics": True,
                "mon": "08:30～17:00",
                "tue": "08:30～17:00",
                "wed": "08:30～17:00",
                "thu": "08:30～17:00",
                "fri": "08:30～17:00",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": True,
                "is_online_for_positive_patients": True,
                "is_home_visitation_for_positive_patients": False,
                "memo": "かかりつけ患者及び保健所からの紹介患者に限ります。 https://www.city.asahikawa.hokkaido.jp/hospital/3100/d075882.html",
            },
            {
                "is_outpatient": True,
                "is_positive_patients": False,
                "public_health_care_center": "旭川",
                "medical_institution_name": "JA北海道厚生連旭川厚生病院",
                "city": "旭川市",
                "address": "旭川市1条通24丁目111番地",
                "phone_number": "0166-33-7171",
                "is_target_not_family": True,
                "is_pediatrics": False,
                "mon": "08:30～11:30",
                "tue": "08:30～11:30",
                "wed": "08:30～11:30",
                "thu": "08:30～11:30",
                "fri": "08:30～11:30",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": False,
                "is_online_for_positive_patients": False,
                "is_home_visitation_for_positive_patients": False,
                "memo": "",
            },
            {
                "is_outpatient": True,
                "is_positive_patients": True,
                "public_health_care_center": "旭川",
                "medical_institution_name": "旭川赤十字病院",
                "city": "旭川市",
                "address": "旭川市曙1条1丁目1番1号",
                "phone_number": "0166-22-8111",
                "is_target_not_family": False,
                "is_pediatrics": False,
                "mon": "",
                "tue": "",
                "wed": "",
                "thu": "",
                "fri": "",
                "sat": "",
                "sun": "",
                "is_face_to_face_for_positive_patients": True,
                "is_online_for_positive_patients": False,
                "is_home_visitation_for_positive_patients": False,
                "memo": "「受診・相談センター」または保健所等の指示によら ず 受診した場合,初診時選定療養費を申し受けます。 当番制のため、不定期となっています。詳細はお問い合わせください。",
            },
        ]
        assert scraper.lists == expect


class TestScrapeOpendataLocation:
    @pytest.fixture()
    def csv_content(self):
        csv_content = """
都道府県コード又は市区町村コード,No,都道府県名,振興局,市町村,名称,名称_カナ,医療機関の種類,郵便番号,所在地,方書,緯度,経度,電話番号,内線番号,FAX番号,法人番号,開設者氏名,管理者氏名,指定年月日,登録理由,指定期間開始,医療機関コード,診療曜日,診療開始時間,診療終了時間,診療日時特記事項,時間外における対応,診療科目,病床数,療養病床,特定機能,現存・休止,URL,備考,緯度経度出典,データ作成日
010006,287,北海道,上川総合振興局,旭川市,市立旭川病院,,病院,070-0029,旭川市金星町１丁目１番６５号,,43.778144,142.365952,0166-24-3181,,,,旭川市,石井　良直,昭32. 7. 1,新規,平29. 7. 1,2910997,,,,,,内;外;耳い;産婦;小;皮;眼;整外;精;放;ひ;麻;神内;呼;消;循;心外;呼外;病理;歯外,481,,,現存,,,地理院地図,2022-11-23
010006,19,北海道,石狩振興局,札幌市,市立札幌病院,,病院,060-8604,札幌市中央区北１１条西１３丁目１番１号,,43.07099935,141.3346474,011-726-2211,,,,札幌市,西川　秀司,平7. 10. 5,移動,令4. 10. 5,0116381,,,,,,呼内;消化器内科;循環器内科;腎臓内科;糖尿病・内分泌内科;血液内科;新生児内科;感染症内科;緩和ケア内科;リウマチ・免疫内科;脳内;小;外科;乳腺外科;腎臓移植外科;整外;形外;脳外;呼外;心外;皮;ひ;産婦;眼;耳鼻咽喉科・甲状腺外科;リハ;放射線治療科;放射線診断科;麻;歯外;精;病理;救急科,672,,,現存,,,地理院地図,2022-11-23
010006,286,北海道,上川総合振興局,旭川市,旭川赤十字病院,,病院,070-8530,旭川市曙１条１丁目１番１号,,43.769637,142.348394,0166-22-8111,,,,日本赤十字社,牧野　憲一,昭32. 8. 14,新規,平29. 8. 14,2910062,,,,,,内;呼内;消;循;救命;病理;精;小;脳内;産婦;外;整外;脳外;心外;呼外;眼;耳い;ひ;形外;皮;リハ;麻;放;歯外,520,,,現存,,,地理院地図,2022-11-23
010006,298,北海道,上川総合振興局,旭川市,ＪＡ北海道厚生連　旭川厚生病院,,病院,078-8211,旭川市１条通２４丁目１１１番地３,,43.758732,142.384931,0166-33-7171,,,,北海道厚生農業協同組合連合会,森　逹也,昭63. 3. 30,移動,平30. 3. 30,2914577,,,,,,内;精;消;循;小;外;整外;形外;呼外;皮;ひ;産婦;眼;耳い;リハ;放;麻;神内;呼;病理,460,,,現存,,,地理院地図,2022-11-23
"""
        return csv_content.encode("shift_jis")

    def test_lists(self, csv_content, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.content = csv_content
        responce_mock.headers = {"content-type": "text/csv"}
        mocker.patch.object(requests, "get", return_value=responce_mock)
        location_data = ScrapeOpendataLocation("http://dummy.local")
        result = location_data.lists
        expect = [
            {
                "medical_institution_name": "市立旭川病院",
                "longitude": 142.365952,
                "latitude": 43.778144,
            },
            {
                "medical_institution_name": "旭川赤十字病院",
                "longitude": 142.348394,
                "latitude": 43.769637,
            },
            {
                "medical_institution_name": "JA北海道厚生連旭川厚生病院",
                "longitude": 142.384931,
                "latitude": 43.758732,
            },
        ]
        assert expect == result


class TestScrapeYOLPLocation:
    @pytest.fixture()
    def json_content(self):
        return """
{
"ResultInfo": {
    "Count": 1,
    "Total": 1,
    "Start": 1,
    "Status": 200,
    "Description": "",
    "Copyright": "",
    "Latency": 0.017
},
"Feature": [
    {
        "Id": "20130710667",
        "Gid": "",
        "Name": "\u5e02\u7acb\u65ed\u5ddd\u75c5\u9662",
        "Geometry": {
            "Type": "point",
            "Coordinates": "142.365976388889,43.778422777778"
        },
        "Category": []
    }
]
}
"""

    def test_lists(self, json_content, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.content = json_content
        responce_mock.headers = {"content-type": "application/json"}
        mocker.patch.object(requests, "get", return_value=responce_mock)
        location_data = ScrapeYOLPLocation("市立旭川病院")
        result = location_data.lists[0]
        assert result["medical_institution_name"] == "市立旭川病院"
        assert result["longitude"] == 142.365976388889
        assert result["latitude"] == 43.778422777778


class TestScrapeOutpatientSourceURL:
    @pytest.fixture()
    def html_content(self):
        return """
<article class="body">
    <div class="ss-alignment ss-alignment-flow">
        <h3>「外来対応医療機関（発熱外来）」及び「陽性者（療養者）の治療に関与する医療機関」</h3>
    </div>
    <div class="ss-alignment ss-alignment-flow">
        <script src="https://www.pref.hokkaido.lg.jp/js/float.js"></script>
        <link rel="stylesheet" href="https://www.pref.hokkaido.lg.jp/css/float.css" />
    </div>
    <div class="ss-alignment ss-alignment-float">
        <p><a href="/fs/8/6/1/1/8/9/3/_/%E3%80%90%E6%9C%AD%E5%B9%8C%E5%B8%82%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).pdf"
                target="_blank"><img alt="01P_札幌.jpg" src="/fs/8/4/9/5/8/5/2/_/01P_%E6%9C%AD%E5%B9%8C.jpg" /></a>
        </p>
    </div>
    <div class="ss-alignment ss-alignment-child">
        <p><a href="/fs/8/6/1/0/4/0/9/_/%E3%80%90%E6%9C%AD%E5%B9%8C%E5%B8%82%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).xlsx"
                target="_blank"><img alt="01E_札幌市.jpg"
                    src="/fs/8/4/9/5/8/5/5/_/01E_%E6%9C%AD%E5%B9%8C%E5%B8%82.jpg" /></a></p>
    </div>
    <div class="ss-alignment ss-alignment-child">
        <p><a href="/fs/8/6/1/1/8/9/2/_/%E3%80%90%E9%81%93%E5%A4%AE%E5%9C%B0%E5%9F%9F%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).pdf"
                target="_blank"><img alt="05P_道央地域.jpg"
                    src="/fs/8/4/9/5/8/5/8/_/05P_%E9%81%93%E5%A4%AE%E5%9C%B0%E5%9F%9F.jpg" /></a>
        </p>
    </div>
    <div class="ss-alignment ss-alignment-child">
        <p><a href="/fs/8/6/1/0/4/1/1/_/%E3%80%90%E9%81%93%E5%A4%AE%E5%9C%B0%E5%9F%9F%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).xlsx"
                target="_blank"><img alt="05E_道央地域.jpg"
                    src="/fs/8/4/9/5/8/6/1/_/05E_%E9%81%93%E5%A4%AE%E5%9C%B0%E5%9F%9F.jpg" /></a>
        </p>
    </div>
    <div class="ss-alignment ss-alignment-child">
        <p><a href="https://www.google.com/maps/d/edit?mid=1dsFPoVjnGg-65yqbtHEqDwjmogNWMN0&amp;usp=sharing"><img
                    alt="外来対応医療機関（いわゆる発熱外来）のマップはこちらをご覧ください。" src="/fs/8/4/9/5/8/6/4/_/%E5%9B%B31-2.png" /></a></p>
    </div>
    <div class="ss-alignment ss-alignment-float">
        <p><a href="/fs/8/6/1/1/8/9/1/_/%E3%80%90%E6%97%AD%E5%B7%9D%E5%B8%82%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).pdf"
                target="_blank"><img alt="02P_旭川.jpg" src="/fs/8/4/9/5/8/6/6/_/02P_%E6%97%AD%E5%B7%9D.jpg" /></a>
        </p>
    </div>
    <div class="ss-alignment ss-alignment-child">
        <p><a href="/fs/8/6/1/1/7/8/8/_/%E3%80%90%E6%97%AD%E5%B7%9D%E5%B8%82%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).xlsx"
                target="_blank"><img alt="02E_旭川.jpg" src="/fs/8/4/9/5/8/6/9/_/02E_%E6%97%AD%E5%B7%9D.jpg" /></a>
        </p>
    </div>
    <div class="ss-alignment ss-alignment-child">
        <p><a href="/fs/8/6/1/1/8/9/0/_/%E3%80%90%E9%81%93%E5%8D%97%E5%9C%B0%E5%9F%9F%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).pdf"
                target="_blank"><img alt="06P_道南地域.jpg"
                    src="/fs/8/4/9/5/8/7/2/_/06P_%E9%81%93%E5%8D%97%E5%9C%B0%E5%9F%9F.jpg" /></a>
        </p>
    </div>
</article>
"""

    def test_get(self, html_content, mocker):
        responce_mock = mocker.Mock()
        responce_mock.status_code = 200
        responce_mock.headers = {
            "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        responce_mock.content = html_content
        mocker.patch.object(requests, "get", return_value=responce_mock)
        url = ScrapeOutpatientSourceURL.get("http://dummy.local")
        expect = (
            "https://www.pref.hokkaido.lg.jp/"
            + "fs/8/6/1/1/7/8/8/_/%E3%80%90%E6%97%AD%E5%B7%9D%E5%B8%82%E3%80%91%E5%A4%96%E6%9D%A5%E5%AF%BE%E5%BF%9C%E5%8C%BB%E7%99%82%E6%A9%9F%E9%96%A2(R5.6.7).xlsx"
        )
        assert url == expect

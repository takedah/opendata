from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from outpatients.models import (Location, Outpatient, ScrapeOpendataLocation,
                                ScrapeOutpatient, ScrapeOutpatientSourceURL)

OUTPATIENTS_URL = "https://www.pref.hokkaido.lg.jp/hf/kst/youkou.html"
HOSPITAL_OPENDATA_URL = (
    "https://www.harp.lg.jp/opendata/dataset/1243/resource/4967/"
    + "01_%E7%97%85%E9%99%A2_%E5%8C%97%E6%B5%B7%E9%81%93_%E7%B7%AF%E5%BA%A6%E7%B5%8C%E5%BA%A6%E4%BB%98%E3%81%8D.csv"
)
CLINIC_OPENDATA_URL = (
    "https://www.harp.lg.jp/opendata/dataset/1243/resource/4968/"
    + "02_%E8%A8%BA%E7%99%82%E6%89%80_%E5%8C%97%E6%B5%B7%E9%81%93_%E7%B7%AF%E5%BA%A6%E7%B5%8C%E5%BA%A6%E4%BB%98%E3%81%8D.csv"
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        admin_user = User.objects.get(username="admin")

        # 後で比較するため現在の発熱外来の医療機関名の一覧を取得しておく
        current_medical_institutions_list = (
            Outpatient.objects.medical_institution_names_list()
        )

        # 発熱外来情報を更新
        source_url = ScrapeOutpatientSourceURL.get(OUTPATIENTS_URL)
        outpatients_scraper = ScrapeOutpatient(source_url)
        new_medical_institutions_list = list()
        for outpatient in outpatients_scraper.lists:
            new_medical_institutions_list.append(outpatient["medical_institution_name"])
            Outpatient.objects.upsert(source=outpatient, user=admin_user)

        # 存在しなくなった発熱外来情報を削除
        deleted_medical_institutions_list = list(
            set(current_medical_institutions_list) - set(new_medical_institutions_list)
        )
        with transaction.atomic():
            for medical_institution in deleted_medical_institutions_list:
                Outpatient.objects.delete(medical_institution)

        # 病院の位置情報を更新
        hospital_location_scraper = ScrapeOpendataLocation(HOSPITAL_OPENDATA_URL)
        with transaction.atomic():
            for location in hospital_location_scraper.lists:
                Location.objects.upsert(source=location, user=admin_user)

        # クリニックの位置情報を更新
        clinic_location_scraper = ScrapeOpendataLocation(CLINIC_OPENDATA_URL)
        with transaction.atomic():
            for location in clinic_location_scraper.lists:
                Location.objects.upsert(source=location, user=admin_user)

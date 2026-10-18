from django.core.management.base import BaseCommand

from courses.ntub_data import DATA_FILE, load_rows
from courses.store import get_store


class Command(BaseCommand):
    help = "把 data/ntub_115-1.txt 的課程寫進 Firestore 的 courses 集合"

    def add_arguments(self, parser):
        parser.add_argument("--file", default=str(DATA_FILE), help="課程資料檔路徑")
        parser.add_argument("--reset-counts", action="store_true", help="把每門課的 registered（本系統登記人數）歸零")

    def handle(self, *args, **opts):
        rows = load_rows(opts["file"])
        n = get_store().seed_courses(rows, reset_counts=opts["reset_counts"])
        self.stdout.write(self.style.SUCCESS(f"已寫入 {n} 門課程"))

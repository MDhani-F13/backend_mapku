from asgiref.sync import sync_to_async

async def save_pipeline_results_to_db(json_path: str):
    import django
    import os
    import sys

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(BASE_DIR)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend_mapku.settings")
    django.setup()

    from traffic.models import TrafficReport, TrafficSegment

    import json
    from django.db import transaction

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    def upsert_report(tweet):
        report, created = TrafficReport.objects.update_or_create(
            tweet_id=tweet.get('tweet_id', ''),
            defaults={
                'query': tweet.get('query', ''),
                'text': tweet.get('text', ''),
                'time': tweet.get('step1_info', {}).get('time', ''),
            }
        )
        if not created:
            report.segments.all().delete()
        return report

    def build_segments(report, segments, singles):
        new_segments = []

        for seg in segments:
            new_segments.append(TrafficSegment(
                report=report,
                from_location=seg.get('from'),
                to_location=seg.get('to'),
                sentence=seg.get('sentence'),
                reason=seg.get('reason'),
                from_lat=seg.get('from_lat'),
                from_lng=seg.get('from_lng'),
                to_lat=seg.get('to_lat'),
                to_lng=seg.get('to_lng'),
                route_polyline=seg.get('route_polyline')
            ))

        for single in singles:
            new_segments.append(TrafficSegment(
                report=report,
                single_location=single.get('location'),
                sentence=single.get('sentence'),
                reason=single.get('reason'),
                single_lat=single.get('lat'),
                single_lng=single.get('lng')
            ))

        return new_segments

    @sync_to_async
    def save_all_sync():
        with transaction.atomic():
            for tweet in data:
                report = upsert_report(tweet)
                segments = build_segments(
                    report,
                    tweet['step3_info'].get('segments', []),
                    tweet['step3_info'].get('single_locations', [])
                )
                TrafficSegment.objects.bulk_create(segments)

        print(f"[DB] ✅ Sukses menyimpan {len(data)} laporan ke database.")

    await save_all_sync()
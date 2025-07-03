from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView
from .models import TrafficReport, TrafficSegment
from .serializers import TrafficReportSerializer,  TrafficSegmentSerializer
import json
from scraper_location.rule_engine import get_or_cache_directions_polyline
from rest_framework.decorators import api_view

class UploadTrafficData(APIView):
    def post(self, request):
        data = request.data
        for tweet in data:
            report = TrafficReport.objects.create(
                query=tweet.get('query', ''),
                text=tweet.get('text', ''),
                time=tweet.get('step1_info', {}).get('time', '')
            )

            for seg in tweet['step3_info'].get('segments', []):
                TrafficSegment.objects.create(
                    report=report,
                    from_location=seg.get('from'),
                    to_location=seg.get('to'),
                    sentence=seg.get('sentence'),
                    reason=seg.get('reason'),
                    from_lat=seg.get('from_lat'),
                    from_lng=seg.get('from_lng'),
                    to_lat=seg.get('to_lat'),
                    to_lng=seg.get('to_lng')
                )

            for single in tweet['step3_info'].get('single_locations', []):
                TrafficSegment.objects.create(
                    report=report,
                    single_location=single.get('location'),
                    sentence=single.get('sentence'),
                    reason=single.get('reason'),
                    single_lat=single.get('lat'),
                    single_lng=single.get('lng')
                )
        return Response({"status": "success"}, status=status.HTTP_201_CREATED)


class TrafficReportList(ListAPIView):
    """
    Endpoint GET semua traffic report + segments
    """
    queryset = TrafficReport.objects.all().order_by('-created_at')
    serializer_class = TrafficReportSerializer

    def get_queryset(self):
        qs = TrafficReport.objects.all()
        time = self.request.GET.get("time")
        recent = self.request.GET.get("recent")

        if time:
            qs = qs.filter(time=time)
        if recent:
            try:
                recent = int(recent)
                qs = qs.order_by("-created_at")[:recent]
            except ValueError:
                pass  # Abaikan kalau bukan angka

        return qs

class TrafficSegmentList(ListAPIView):
    queryset = TrafficSegment.objects.all()
    serializer_class = TrafficSegmentSerializer

    def get_queryset(self):
        qs = TrafficSegment.objects.select_related('report').all()

        # Misal mau filter by recent?
        recent = self.request.GET.get("recent")
        if recent:
            try:
                recent = int(recent)
                qs = qs.order_by("-created_at")[:recent]
            except ValueError:
                pass

        return qs
    
@api_view(['GET'])
def get_segment_polyline(request, pk):
    try:
        segment = TrafficSegment.objects.get(pk=pk)
    except TrafficSegment.DoesNotExist:
        return Response({"error": "Segment not found"}, status=404)

    polyline = get_or_cache_directions_polyline(segment)
    if polyline:
        return Response({"route_polyline": polyline})
    return Response({"error": "Could not generate polyline"}, status=500)
from django.urls import path
from .views import UploadTrafficData, TrafficReportList,TrafficSegmentList, get_segment_polyline

urlpatterns = [
    path('upload-traffic/', UploadTrafficData.as_view(), name='upload_traffic'),
    path('traffic-reports/', TrafficReportList.as_view(), name='traffic_reports'),
    path('traffic-segments/', TrafficSegmentList.as_view(), name='traffic_segments'),
    path('segment/<int:pk>/get_polyline/', get_segment_polyline),
]
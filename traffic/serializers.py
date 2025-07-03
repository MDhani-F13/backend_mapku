from rest_framework import serializers
from .models import TrafficReport, TrafficSegment
from scraper_location.rule_engine import get_or_cache_directions_polyline

class TrafficSegmentSerializer(serializers.ModelSerializer):
    tweet_text = serializers.CharField(source='report.text', read_only=True)
    route_polyline = serializers.SerializerMethodField()
    time = serializers.DateTimeField(source='report.time')
    class Meta:
        model = TrafficSegment
        fields = '__all__'  

    def get_route_polyline(self, obj):
        # Cek kalau segment ini pakai FROM-TO
        if obj.from_lat and obj.from_lng and obj.to_lat and obj.to_lng:
            return get_or_cache_directions_polyline(obj)
        return None
    
class TrafficReportSerializer(serializers.ModelSerializer):
    segments = TrafficSegmentSerializer(many=True, read_only=True)

    class Meta:
        model = TrafficReport
        fields = ['id', 'query', 'text', 'time', 'created_at', 'segments']

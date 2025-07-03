from django.db import models

class TrafficReport(models.Model):
    query = models.TextField(blank=True, null=True)
    text = models.TextField()
    time = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)
    tweet_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    def __str__(self):
        return f"TrafficReport {self.id} - {self.time}"

class TrafficSegment(models.Model):
    report = models.ForeignKey(TrafficReport, on_delete=models.CASCADE, related_name="segments")
    from_location = models.CharField(max_length=255, null=True, blank=True)
    to_location = models.CharField(max_length=255, null=True, blank=True)
    sentence = models.TextField()
    reason = models.CharField(max_length=255)
    from_lat = models.FloatField(null=True, blank=True)
    from_lng = models.FloatField(null=True, blank=True)
    to_lat = models.FloatField(null=True, blank=True)
    to_lng = models.FloatField(null=True, blank=True)
    single_location = models.CharField(max_length=255, null=True, blank=True)
    single_lat = models.FloatField(null=True, blank=True)
    single_lng = models.FloatField(null=True, blank=True)
    route_polyline = models.TextField(blank=True, null=True) 

    def __str__(self):
        return f"Segment: {self.from_location} -> {self.to_location} | {self.single_location}"
    
class APICallQuota(models.Model):
    name = models.CharField(max_length=100, unique=True)
    count = models.IntegerField(default=0)
    reset_month = models.DateField(auto_now_add=True)

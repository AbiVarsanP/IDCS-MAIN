from django.db import models

class BusRoute(models.Model):
    name = models.CharField(max_length=100)
    bus_no = models.CharField(max_length=20)
    total_seat = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.bus_no})"

class BoardingPoint(models.Model):
    route = models.ForeignKey('BusRoute', related_name='boarding_points', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.route.name}"

class Driver(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    route = models.OneToOneField('BusRoute', related_name='driver', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.number})"

class BusApplication(models.Model):
    name = models.CharField(max_length=100)
    register_no = models.CharField(max_length=30)
    mobile_number = models.CharField(max_length=15)
    route = models.ForeignKey('BusRoute', on_delete=models.CASCADE)
    boarding_point = models.ForeignKey('BoardingPoint', on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.route.name}"

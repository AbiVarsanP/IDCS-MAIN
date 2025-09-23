from django.db import models

class BusRoute(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name}"

class Bus(models.Model):
    route = models.ForeignKey('BusRoute', related_name='buses', on_delete=models.CASCADE)
    bus_no = models.CharField(max_length=20)
    total_seat = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.bus_no} - {self.route.name}"


class BoardingPoint(models.Model):
    bus = models.ForeignKey('Bus', related_name='boarding_points', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    timing = models.CharField(max_length=100, blank=True, null=True)
    fee = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {getattr(self.bus, 'bus_no', '')}"

class Driver(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=20)
    bus = models.OneToOneField('Bus', related_name='driver', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.number})"

class BusApplication(models.Model):
    name = models.CharField(max_length=100)
    register_no = models.CharField(max_length=30)
    mobile_number = models.CharField(max_length=15)
    route = models.ForeignKey('BusRoute', on_delete=models.CASCADE)
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE)
    boarding_point = models.ForeignKey('BoardingPoint', on_delete=models.CASCADE)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.route.name} - {getattr(self.bus, 'bus_no', '')}"

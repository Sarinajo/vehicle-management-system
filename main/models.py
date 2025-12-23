from django.db import models
from django.contrib.auth.models import User

VEHICLES_TYPE_CHOICES = [
    ('Electric', 'Electric'),
    ('Petrol', 'Petrol'),
    ('Diesel', 'Diesel'),
]

class Driver(models.Model):
    driver_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.driver_id})"

class VehicleRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLES_TYPE_CHOICES)
    maintenance_cost = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)


    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, default=None)

    paid_to_company = models.CharField(max_length=50)
    bill_number = models.CharField(max_length=50)
    bill_date = models.DateField()
    distance_traveled = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason_for_maintenance = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        self.total_cost = (self.maintenance_cost or 0) + (self.fuel_cost or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle_number} - {self.date}"

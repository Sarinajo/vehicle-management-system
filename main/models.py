from django.db import models
from django.contrib.auth.models import User

VEHICLES_TYPE_CHOICES = [
    ('Electric','Electric'),
    ('Petrol','Petrol'),
    ('Diesel','Diesel'),
]

class VehicleRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    date = models.DateField()
    vehicle_number = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=10, choices=VEHICLES_TYPE_CHOICES)
    maintenance_cost = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_cost = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    driver_name = models.CharField(max_length=50)
    paid_to_company = models.CharField(max_length=50)
    bill_number = models.CharField(max_length=50)
    bill_date = models.DateField()
    remarks = models.CharField(max_length=200, blank=True)

    def save(self, *args, **kwargs):
        self.total_cost = (self.maintenance_cost or 0) + (self.fuel_cost or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle_number} - {self.date}"

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.db.models import Sum
from nepali_datetime import date as nepali_date
import csv

from .forms import VehicleRecordForm, DriverForm
from .models import VehicleRecord, Driver

# -----------------------------
# User login/logout/register
# -----------------------------
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'main/login.html', {'error': 'Invalid username or password'})
    return render(request, 'main/login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})

# -----------------------------
# Home / Vehicle Records
# -----------------------------
@login_required(login_url='login')
def home(request):
    submitted_record = None
    if request.method == 'POST':
        form = VehicleRecordForm(request.POST)
        if form.is_valid():
            submitted_record = form.save(commit=False)
            submitted_record.user = request.user

            # Convert BS dates to AD
            bs_date_str = request.POST.get('date')
            bs_bill_str = request.POST.get('bill_date')

            if bs_date_str:
                year, month, day = map(int, bs_date_str.split('-'))
                submitted_record.date = nepali_date(year, month, day).to_datetime_date()

            if bs_bill_str:
                year, month, day = map(int, bs_bill_str.split('-'))
                submitted_record.bill_date = nepali_date(year, month, day).to_datetime_date()

            # Set defaults
            submitted_record.fuel_cost = submitted_record.fuel_cost or 0
            submitted_record.distance_traveled = submitted_record.distance_traveled or 0

            submitted_record.save()
            return redirect('success', record_id=submitted_record.id)
    else:
        form = VehicleRecordForm()
        today_bs = nepali_date.today()
        form.fields['date'].initial = today_bs.strftime("%Y-%m-%d")
        form.fields['bill_date'].initial = today_bs.strftime("%Y-%m-%d")

    # Fetch user records
    user_records = VehicleRecord.objects.filter(user=request.user).order_by('-date')
    for record in user_records:
        record.bs_date = nepali_date.from_datetime_date(record.date) if record.date else None
        record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date) if record.bill_date else None

    return render(request, 'main/home.html', {
        'form': form,
        'submitted_record': submitted_record,
        'user_records': user_records
    })



@login_required(login_url='login')
def success(request, record_id):
    record = get_object_or_404(VehicleRecord, id=record_id, user=request.user)
    record.bs_date = nepali_date.from_datetime_date(record.date) if record.date else None
    record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date) if record.bill_date else None
    return render(request, 'main/success.html', {'record': record})



@login_required(login_url='login')
def my_records(request):
    # 🔴 FIX: admin should see all records
    if request.user.is_superuser:
        user_records = VehicleRecord.objects.all().order_by('-date', '-id')
    else:
        user_records = VehicleRecord.objects.filter(user=request.user).order_by('-date', '-id')

    for record in user_records:
        record.bs_date = nepali_date.from_datetime_date(record.date) if record.date else None
        record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date) if record.bill_date else None

    return render(request, 'main/my_records.html', {'user_records': user_records})

# -----------------------------
# Admin: Manage Drivers
# -----------------------------
@user_passes_test(lambda u: u.is_superuser)
def manage_drivers(request):
    if request.method == 'POST':
        form = DriverForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_drivers')
    else:
        form = DriverForm()
    drivers = Driver.objects.all().order_by('name')
    return render(request, 'main/drivers.html', {'form': form, 'drivers': drivers})

# -----------------------------
# Admin: Reports
# -----------------------------
def bs_string_to_ad(bs_str):
    parts = bs_str.split('-')
    if len(parts) != 3:
        raise ValueError("Invalid BS date format")
    year, month, day = map(int, parts)
    return nepali_date(year, month, day).to_datetime_date()

@user_passes_test(lambda u: u.is_superuser)
def reports(request):
    drivers = Driver.objects.all().order_by('name')
    records = VehicleRecord.objects.all().order_by('-date', '-id')


    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    driver_id = request.GET.get('driver')
    action = request.GET.get('action')  # 'csv' or 'summary'

    # Filter dates
    if from_date:
        try:
            ad_from = bs_string_to_ad(from_date)
            records = records.filter(date__gte=ad_from)
        except ValueError:
            pass
    if to_date:
        try:
            ad_to = bs_string_to_ad(to_date)
            records = records.filter(date__lte=ad_to)
        except ValueError:
            pass

    # Filter driver
    if driver_id:
        records = records.filter(driver_id=driver_id)

    # Add BS dates for display
    for record in records:
        record.bs_date = nepali_date.from_datetime_date(record.date) if record.date else None
        record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date) if record.bill_date else None

    # CSV download
    if action == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vehicle_records.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Date (BS)', 'Vehicle Number', 'Type', 'Maintenance Cost',
            'Fuel Cost', 'Total Cost', 'Driver', 'Paid To', 'Bill Number',
            'Bill Date (BS)', 'Reason for Maintenance', 'Distance Traveled', 'User'
        ])
        for record in records:
            writer.writerow([
                f"{record.bs_date.year}-{record.bs_date.month:02}-{record.bs_date.day:02}" if record.bs_date else '',
                record.vehicle_number,
                record.vehicle_type,
                f"{float(record.maintenance_cost):.2f}",
                f"{float(record.fuel_cost):.2f}",
                f"{float(record.total_cost):.2f}",
                record.driver.name if record.driver else '',
                record.paid_to_company,
                record.bill_number,
                f"{record.bs_bill_date.year}-{record.bs_bill_date.month:02}-{record.bs_bill_date.day:02}" if record.bs_bill_date else '',
                record.reason_for_maintenance,
                record.distance_traveled,
                record.user.username if hasattr(record, 'user') else ''
            ])
        return response

    # Summary
    summary = []
    if action in ['summary', 'summary_csv']:
        summary = (
            records
            .values('driver__name')
            .annotate(
                total_maintenance=Sum('maintenance_cost'),
                total_fuel=Sum('fuel_cost'),
                total_cost=Sum('total_cost')
            )
            .order_by('driver__name')
        )
    # -----------------------------
    # Summary CSV download
    # -----------------------------
    if action == 'summary_csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="summary_report.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'From Date (BS)',
            'To Date (BS)',
            'Driver',
            'Total Maintenance Cost',
            'Total Fuel Cost',
            'Total Cost'
        ])

        for row in summary:
            writer.writerow([
                from_date or '',
                to_date or '',
                row['driver__name'] or '',
                f"{row['total_maintenance'] or 0:.2f}",
                f"{row['total_fuel'] or 0:.2f}",
                f"{row['total_cost'] or 0:.2f}",
            ])

        return response

    return render(request, 'main/reports.html', {
        'drivers': drivers,
        'records': records,
        'from_date': from_date,
        'to_date': to_date,
        'selected_driver': int(driver_id) if driver_id else None,
        'summary': summary
    })

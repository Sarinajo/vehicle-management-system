from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.db.models import Sum
from nepali_datetime import date as nepali_date

from .forms import VehicleRecordForm
from .models import VehicleRecord
import csv

# -----------------------------
# User login, logout, register
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

            # Get BS date strings from form
            bs_date_str = request.POST.get('date')       # e.g., '2082-08-05'
            bs_bill_str = request.POST.get('bill_date')  # e.g., '2082-08-05'

            # Convert BS to AD using nepali_date
            if bs_date_str:
                year, month, day = map(int, bs_date_str.split('-'))
                ad_date = nepali_date(year, month, day).to_datetime_date()
                submitted_record.date = ad_date

            if bs_bill_str:
                year, month, day = map(int, bs_bill_str.split('-'))
                ad_bill = nepali_date(year, month, day).to_datetime_date()
                submitted_record.bill_date = ad_bill

            submitted_record.save()
            return redirect('success', record_id=submitted_record.id)
    else:
        form = VehicleRecordForm()
        # pre-fill today in BS
        today_bs = nepali_date.today()
        form.fields['date'].initial = today_bs.strftime("%Y-%m-%d")
        form.fields['bill_date'].initial = today_bs.strftime("%Y-%m-%d")

    # Fetch user records and attach BS dates for display
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
    user_records = VehicleRecord.objects.filter(user=request.user).order_by('-date')
    for record in user_records:
        record.bs_date = nepali_date.from_datetime_date(record.date) if record.date else None
        record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date) if record.bill_date else None
    return render(request, 'main/my_records.html', {'user_records': user_records})


# -----------------------------
# Admin Reports
# -----------------------------
# Helper to convert BS string (YYYY-MM-DD) to AD date
def bs_string_to_ad(bs_str):
    """
    Convert BS string with English digits 'YYYY-MM-DD' to AD date.
    """
    parts = bs_str.split('-')
    if len(parts) != 3:
        raise ValueError("Invalid BS date format")
    year, month, day = map(int, parts)
    return nepali_date(year, month, day).to_datetime_date()


@user_passes_test(lambda u: u.is_superuser)
def reports(request):
    drivers = VehicleRecord.objects.values_list('driver_name', flat=True).distinct()
    records = VehicleRecord.objects.all().order_by('-date')

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    driver = request.GET.get('driver')
    action = request.GET.get('action')  # 'csv' or 'summary'

    # Filter by BS dates (converted to AD)
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

    if driver:
        records = records.filter(driver_name=driver)

    # Attach BS dates for display
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
            'Bill Date (BS)', 'Remarks', 'User'
        ])
        for record in records:
            writer.writerow([
                f"{record.bs_date.year}-{record.bs_date.month:02}-{record.bs_date.day:02}" if record.bs_date else '',
                record.vehicle_number,
                record.vehicle_type,
                f"{float(record.maintenance_cost):.2f}",
                f"{float(record.fuel_cost):.2f}",
                f"{float(record.total_cost):.2f}",
                record.driver_name,
                record.paid_to_company,
                record.bill_number,
                f"{record.bs_bill_date.year}-{record.bs_bill_date.month:02}-{record.bs_bill_date.day:02}" if record.bs_bill_date else '',
                record.remarks,
                record.user.username if hasattr(record, 'user') else ''
            ])
        return response

    # Summary
    summary = {}
    if action == 'summary':
        totals = records.aggregate(
            total_maintenance=Sum('maintenance_cost'),
            total_fuel=Sum('fuel_cost'),
            total_cost=Sum('total_cost')
        )
        summary = {
            'total_maintenance': totals['total_maintenance'] or 0,
            'total_fuel': totals['total_fuel'] or 0,
            'total_cost': totals['total_cost'] or 0
        }

    return render(request, 'main/reports.html', {
        'drivers': drivers,
        'records': records,
        'from_date': from_date,
        'to_date': to_date,
        'selected_driver': driver,
        'summary': summary
    })

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
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
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
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'main/register.html', {'form': form})


# -----------------------------
# Home / Vehicle Records
# -----------------------------
@login_required(login_url='login')
def dashboard(request):
    # This is the post-login landing page
    return render(request, 'main/dashboard.html')
@login_required(login_url='login')
def home(request):
    submitted_record = None
    if request.method == 'POST':
        form = VehicleRecordForm(request.POST)
        if form.is_valid():
            submitted_record = form.save(commit=False)
            submitted_record.user = request.user

            # Set date to current Nepali date
            today_bs = nepali_date.today()
            submitted_record.date = today_bs.to_datetime_date()

            # Convert bill_date from Nepali string to date
            bs_bill_str = request.POST.get('bill_date')
            if bs_bill_str:
                y, m, d = map(int, bs_bill_str.split('-'))
                submitted_record.bill_date = nepali_date(y, m, d).to_datetime_date()

            submitted_record.fuel_cost = submitted_record.fuel_cost or 0
            submitted_record.distance_traveled = submitted_record.distance_traveled or 0

            submitted_record.save()
            return redirect('success', record_id=submitted_record.id)
    else:
        form = VehicleRecordForm()
        today_bs = nepali_date.today()
        form.fields['date'].initial = today_bs.strftime("%Y-%m-%d")
        form.fields['bill_date'].initial = today_bs.strftime("%Y-%m-%d")

    user_records = VehicleRecord.objects.filter(user=request.user).order_by('-date')
    for r in user_records:
        r.bs_date = nepali_date.from_datetime_date(r.date)
        r.bs_bill_date = nepali_date.from_datetime_date(r.bill_date)

    return render(request, 'main/home.html', {
        'form': form,
        'submitted_record': submitted_record,
        'user_records': user_records
    })


@login_required(login_url='login')
def success(request, record_id):
    record = get_object_or_404(VehicleRecord, id=record_id, user=request.user)
    record.bs_date = nepali_date.from_datetime_date(record.date)
    record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date)
    return render(request, 'main/success.html', {'record': record})


@login_required(login_url='login')
def my_records(request):
    records = VehicleRecord.objects.none()  # ⛔ no query by default
    show_message = False

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    action = request.GET.get('action')

    if action == 'view':
        if not from_date or not to_date:
            show_message = True
        else:
            ad_from = bs_string_to_ad(from_date)
            ad_to = bs_string_to_ad(to_date)

            if not ad_from or not ad_to:
                show_message = True
            else:
                if request.user.is_superuser:
                    records = VehicleRecord.objects.all()
                else:
                    records = VehicleRecord.objects.filter(user=request.user)

                records = records.filter(
                    date__gte=ad_from,
                    date__lte=ad_to
                ).order_by('-date', '-id')

                for r in records:
                    r.bs_date = nepali_date.from_datetime_date(r.date)
                    r.bs_bill_date = nepali_date.from_datetime_date(r.bill_date)

    return render(request, 'main/my_records.html', {
        'user_records': records,
        'from_date': from_date,
        'to_date': to_date,
        'show_message': show_message
    })


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

@user_passes_test(lambda u: u.is_superuser)
def edit_record(request, record_id):
    record = get_object_or_404(VehicleRecord, id=record_id)

    if request.method == 'POST':
        form = VehicleRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('my_records')
    else:
        form = VehicleRecordForm(instance=record)

        # Pre-fill BS dates for display
        record.bs_date = nepali_date.from_datetime_date(record.date)
        record.bs_bill_date = nepali_date.from_datetime_date(record.bill_date)

        form.fields['date'].initial = record.bs_date.strftime("%Y-%m-%d")
        form.fields['bill_date'].initial = record.bs_bill_date.strftime("%Y-%m-%d")

    return render(request, 'main/edit_record.html', {
        'form': form,
        'record': record
    })

# -----------------------------
# Helpers
# -----------------------------
def bs_string_to_ad(bs_str):
    try:
        y, m, d = map(int, bs_str.split('-'))
        return nepali_date(y, m, d).to_datetime_date()
    except:
        return None


# -----------------------------
# OLD REPORTS
# -----------------------------
@user_passes_test(lambda u: u.is_superuser)
def reports(request):
    drivers = Driver.objects.all().order_by('name')
    records = VehicleRecord.objects.all().order_by('-date', '-id')
    return render(request, 'main/reports.html', {'drivers': drivers, 'records': records})


# =====================================================
# NEW REPORT SYSTEM WITH MESSAGES
# =====================================================


## 1️⃣ RAW DATA – BY DRIVER (Corrected)
@user_passes_test(lambda u: u.is_superuser)
def reports_raw_driver(request):
    drivers = Driver.objects.all().order_by('name')
    records = VehicleRecord.objects.none()
    show_message = False

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    driver_id = request.GET.get('driver')
    action = request.GET.get('action')

    # Require only date filters; driver is optional
    if action in ['view', 'csv']:
        if not from_date or not to_date:
            show_message = True
        else:
            records = VehicleRecord.objects.all().order_by('-date', '-id')
            ad_from = bs_string_to_ad(from_date)
            ad_to = bs_string_to_ad(to_date)
            if ad_from:
                records = records.filter(date__gte=ad_from)
            if ad_to:
                records = records.filter(date__lte=ad_to)
            if driver_id:  # driver filter is optional
                records = records.filter(driver_id=driver_id)

            for r in records:
                r.bs_date = nepali_date.from_datetime_date(r.date)
                r.bs_bill_date = nepali_date.from_datetime_date(r.bill_date)

    # CSV export
    if action == 'csv' and not show_message:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="raw_driver.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Date (BS)', 'Vehicle Number', 'Type', 'Maintenance Cost', 'Fuel Cost',
            'Total Cost', 'Distance Traveled', 'Driver', 'Paid To', 'Bill Number',
            'Bill Date (BS)', 'Reason for Maintenance'
        ])
        for r in records:
            writer.writerow([
                r.bs_date, r.vehicle_number, r.vehicle_type, r.maintenance_cost,
                r.fuel_cost, r.total_cost, r.distance_traveled,
                r.driver.name if r.driver else '', r.paid_to_company,
                r.bill_number, r.bs_bill_date, r.reason_for_maintenance
            ])
        return response

    return render(request, 'main/reports_raw_driver.html', {
        'drivers': drivers,
        'records': records,
        'from_date': from_date,
        'to_date': to_date,
        'selected_driver': int(driver_id) if driver_id else None,
        'show_message': show_message
    })




@user_passes_test(lambda u: u.is_superuser)
def reports_summary_driver(request):
    drivers = Driver.objects.all().order_by('name')
    summary = None
    show_message = False

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    driver_id = request.GET.get('driver')
    action = request.GET.get('action')

    if action in ['view', 'csv']:
        # Check if dates are provided
        if not from_date or not to_date:
            show_message = True
        else:
            ad_from = bs_string_to_ad(from_date)
            ad_to = bs_string_to_ad(to_date)

            # If date conversion fails, show message
            if not ad_from or not ad_to:
                show_message = True
            else:
                records = VehicleRecord.objects.all()
                records = records.filter(date__gte=ad_from, date__lte=ad_to)

                if driver_id:
                    records = records.filter(driver_id=driver_id)

                if records.exists():
                    summary = list(
                        records.values('driver__name').annotate(
                            total_maintenance=Sum('maintenance_cost'),
                            total_fuel=Sum('fuel_cost'),
                            total_cost=Sum('total_cost')
                        )
                    )
                else:
                    summary = None

    # CSV export
    if action == 'csv' and summary:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="summary_driver.csv"'
        writer = csv.writer(response)
        writer.writerow(['Driver', 'Total Maintenance', 'Total Fuel', 'Total Cost'])
        for row in summary:
            writer.writerow([
                row.get('driver__name', 'N/A'),
                row.get('total_maintenance', 0),
                row.get('total_fuel', 0),
                row.get('total_cost', 0)
            ])
        return response

    return render(request, 'main/reports_summary_driver.html', {
        'drivers': drivers,
        'summary': summary,
        'from_date': from_date,
        'to_date': to_date,
        'selected_driver': int(driver_id) if driver_id else None,
        'show_message': show_message
    })








# 3️⃣ RAW DATA – BY VEHICLE
@user_passes_test(lambda u: u.is_superuser)
def reports_raw_vehicle(request):
    records = VehicleRecord.objects.none()
    show_message = False

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    vehicle_number = request.GET.get('vehicle_number')
    action = request.GET.get('action')

    # Normalize invalid date inputs
    if from_date in [None, '', 'None']:
        from_date = None
    if to_date in [None, '', 'None']:
        to_date = None

    # Fetch all distinct vehicle numbers for the dropdown
    vehicle_numbers = VehicleRecord.objects.values_list('vehicle_number', flat=True).distinct().order_by('vehicle_number')

    if action in ['view', 'csv']:
        # Require both from_date and to_date
        if not from_date or not to_date:
            show_message = True
        else:
            ad_from = bs_string_to_ad(from_date)
            ad_to = bs_string_to_ad(to_date)

            # If either conversion fails, show message
            if not ad_from or not ad_to:
                show_message = True
            else:
                records = VehicleRecord.objects.all().order_by('-date', '-id')
                records = records.filter(date__gte=ad_from, date__lte=ad_to)

                # Filter by vehicle_number if selected
                if vehicle_number:
                    records = records.filter(vehicle_number=vehicle_number)

                # Convert dates to BS for display
                for r in records:
                    r.bs_date = nepali_date.from_datetime_date(r.date)
                    if r.bill_date:
                        r.bs_bill_date = nepali_date.from_datetime_date(r.bill_date)
                    else:
                        r.bs_bill_date = None

    # CSV export
    if action == 'csv' and not show_message:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="raw_vehicle.csv"'
        writer = csv.writer(response)
        writer.writerow([
            'Date (BS)', 'Vehicle Number', 'Vehicle Type', 'Maintenance Cost',
            'Fuel Cost', 'Total Cost', 'Distance Traveled', 'Driver',
            'Paid To', 'Bill Number', 'Bill Date (BS)', 'Reason for Maintenance'
        ])
        for r in records:
            writer.writerow([
                r.bs_date, r.vehicle_number, r.vehicle_type, r.maintenance_cost,
                r.fuel_cost, r.total_cost, r.distance_traveled,
                r.driver.name if r.driver else '',
                r.paid_to_company, r.bill_number,
                r.bs_bill_date if r.bs_bill_date else '',
                r.reason_for_maintenance
            ])
        return response

    # Render template
    return render(request, 'main/reports_raw_vehicle.html', {
        'records': records,
        'from_date': from_date,
        'to_date': to_date,
        'show_message': show_message,
        'vehicle_numbers': vehicle_numbers,
        'selected_vehicle': vehicle_number or ''
    })




# 4️⃣ SUMMARY – BY VEHICLE
@user_passes_test(lambda u: u.is_superuser)
def reports_summary_vehicle(request):
    summary = []
    show_message = False
    message = ''

    from_date = request.GET.get('from_date')
    to_date = request.GET.get('to_date')
    vehicle_number = request.GET.get('vehicle_number')
    action = request.GET.get('action')

    # Normalize invalid date inputs
    if from_date in [None, '', 'None']:
        from_date = None
    if to_date in [None, '', 'None']:
        to_date = None

    # Fetch all distinct vehicle numbers for dropdown
    vehicle_numbers = VehicleRecord.objects.values_list('vehicle_number', flat=True).distinct().order_by('vehicle_number')

    if action in ['view', 'csv']:
        # Require both dates to be provided
        if not from_date or not to_date:
            show_message = True
            message = 'Both From Date and To Date must be provided.'
        else:
            ad_from = bs_string_to_ad(from_date)
            ad_to = bs_string_to_ad(to_date)

            if not ad_from or not ad_to:
                show_message = True
                message = 'Invalid date format provided.'
            else:
                records = VehicleRecord.objects.filter(date__gte=ad_from, date__lte=ad_to)

                if vehicle_number:
                    records = records.filter(vehicle_number__iexact=vehicle_number)

                summary = records.values('vehicle_number').annotate(
                    total_maintenance=Sum('maintenance_cost'),
                    total_fuel=Sum('fuel_cost'),
                    total_cost=Sum('total_cost')
                )

    if action == 'csv' and not show_message:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="summary_vehicle.csv"'
        writer = csv.writer(response)
        writer.writerow(['Vehicle', 'Maintenance', 'Fuel', 'Total'])
        for row in summary:
            writer.writerow([
                row['vehicle_number'],
                row['total_maintenance'],
                row['total_fuel'],
                row['total_cost']
            ])
        return response

    return render(request, 'main/reports_summary_vehicle.html', {
        'summary': summary,
        'from_date': from_date,
        'to_date': to_date,
        'show_message': show_message,
        'message': message,
        'vehicle_numbers': vehicle_numbers,
        'selected_vehicle': vehicle_number or ''
    })
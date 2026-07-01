import io
import json
from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Case, When, IntegerField
from django.db.models.functions import TruncDate, TruncHour
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .models import Customer
from .forms import CustomerRegistrationForm
from .decorators import admin_required


@login_required
def register(request):
    if request.method == 'POST':
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.has_played = True  # registration = entered the game
            customer.save()
            return redirect('registration_success', pk=customer.pk)
        else:
            messages.error(request, 'Please fix the errors below and try again.')
    else:
        form = CustomerRegistrationForm()

    return render(request, 'customers/register.html', {'form': form})


@login_required
def registration_success(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if not customer.has_played:
        customer.has_played = True
        customer.save(update_fields=['has_played'])
    return render(request, 'customers/success.html', {'customer': customer})


@admin_required
def dashboard(request):
    from datetime import date as date_type
    search_query = request.GET.get('q', '').strip()
    date_filter  = request.GET.get('date', '').strip()

    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    # Resolve selected date range or single date
    from_date = None
    to_date = None
    if date_filter:
        if ' to ' in date_filter:
            try:
                parts = date_filter.split(' to ')
                from_date = date_type.fromisoformat(parts[0].strip())
                to_date = date_type.fromisoformat(parts[1].strip())
            except (ValueError, IndexError):
                date_filter = ''
        else:
            try:
                from_date = date_type.fromisoformat(date_filter.strip())
                to_date = from_date
            except ValueError:
                date_filter = ''

    if not from_date or not to_date:
        from_date = today
        to_date = today

    # Format the display date/range text
    if from_date == to_date:
        date_display = from_date.strftime('%d %b %Y')
    else:
        date_display = f"{from_date.strftime('%d %b %Y')} to {to_date.strftime('%d %b %Y')}"

    # Single aggregation query for all stat card counts
    agg = Customer.objects.aggregate(
        total_all=Count('id'),
        played_all=Count(Case(When(has_played=True, then=1), output_field=IntegerField())),
        today=Count(Case(When(registered_at__date=today, then=1), output_field=IntegerField())),
        filtered_total=Count(Case(When(registered_at__date__gte=from_date, registered_at__date__lte=to_date, then=1), output_field=IntegerField())),
        filtered_played=Count(Case(When(registered_at__date__gte=from_date, registered_at__date__lte=to_date, has_played=True, then=1), output_field=IntegerField())),
    )

    if date_filter:
        total_count  = agg['filtered_total']
        played_count = agg['filtered_played']
    else:
        total_count  = agg['total_all']
        played_count = agg['played_all']
    today_count = agg['today']

    # Bar chart: 7-day window or selected range
    if from_date == to_date:
        start_date = from_date - timedelta(days=6)
        end_date = from_date
    else:
        start_date = from_date
        end_date = to_date

    daily_qs = (
        Customer.objects
        .filter(registered_at__date__gte=start_date,
                registered_at__date__lte=end_date)
        .annotate(date=TruncDate('registered_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    daily_map = {row['date'].strftime('%d %b'): row['count'] for row in daily_qs if row['date']}
    chart_labels = []
    chart_data = []
    num_days = (end_date - start_date).days + 1
    for i in range(num_days):
        day = start_date + timedelta(days=i)
        label = day.strftime('%d %b')
        chart_labels.append(label)
        chart_data.append(daily_map.get(label, 0))

    # Hourly chart: scoped to selected date range, 9 AM – 9 PM window
    EVENT_START = 9
    EVENT_END   = 21
    from django.db.models.functions import ExtractHour
    hourly_qs = (
        Customer.objects
        .filter(registered_at__date__gte=from_date, registered_at__date__lte=to_date)
        .annotate(hour_val=ExtractHour('registered_at'))
        .values('hour_val')
        .annotate(count=Count('id'))
        .order_by('hour_val')
    )
    hourly_map    = {row['hour_val']: row['count'] for row in hourly_qs if row['hour_val'] is not None}
    hourly_labels = [f'{h:02d}:00' for h in range(EVENT_START, EVENT_END + 1)]
    hourly_data   = [hourly_map.get(h, 0) for h in range(EVENT_START, EVENT_END + 1)]

    # All unique dates that have registrations (for calendar highlighting)
    registered_dates = list(
        Customer.objects
        .values_list('registered_at__date', flat=True)
        .distinct()
        .order_by()
    )
    registered_dates_json = json.dumps([d.isoformat() for d in registered_dates if d])

    context = {
        'search_query':  search_query,
        'date_filter':   date_filter,
        'date_display':  date_display,
        'from_date':     from_date,
        'to_date':       to_date,
        'active_date':   from_date,
        'today_iso':     today.isoformat(),
        'yesterday_iso': yesterday.isoformat(),
        'total_count':   total_count,
        'played_count':  played_count,
        'today_count':   today_count,
        'chart_labels':  json.dumps(chart_labels),
        'chart_data':    json.dumps(chart_data),
        'hourly_labels': json.dumps(hourly_labels),
        'hourly_data':   json.dumps(hourly_data),
        'registered_dates_json': registered_dates_json,
    }
    return render(request, 'customers/dashboard.html', context)


@admin_required
def report(request):
    from datetime import date as date_type
    from_date_str = request.GET.get('from_date', '').strip()
    to_date_str   = request.GET.get('to_date', '').strip()
    search_query  = request.GET.get('q', '').strip()

    customers = Customer.objects.all()

    from_date = None
    to_date   = None

    if from_date_str:
        try:
            from_date = date_type.fromisoformat(from_date_str)
            customers = customers.filter(registered_at__date__gte=from_date)
        except ValueError:
            from_date_str = ''

    if to_date_str:
        try:
            to_date = date_type.fromisoformat(to_date_str)
            customers = customers.filter(registered_at__date__lte=to_date)
        except ValueError:
            to_date_str = ''

    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(bill_number__icontains=search_query)
        )

    total_filtered = customers.count()

    paginator   = Paginator(customers, 50)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)

    context = {
        'page_obj':      page_obj,
        'search_query':  search_query,
        'from_date_str': from_date_str,
        'to_date_str':   to_date_str,
        'from_date':     from_date,
        'to_date':       to_date,
        'total_filtered': total_filtered,
    }
    return render(request, 'customers/report.html', context)


@admin_required
def export_report_excel(request):
    from datetime import date as date_type
    from_date_str = request.GET.get('from_date', '').strip()
    to_date_str   = request.GET.get('to_date', '').strip()
    search_query  = request.GET.get('q', '').strip()

    customers = Customer.objects.all()

    if from_date_str:
        try:
            customers = customers.filter(registered_at__date__gte=date_type.fromisoformat(from_date_str))
        except ValueError:
            pass

    if to_date_str:
        try:
            customers = customers.filter(registered_at__date__lte=date_type.fromisoformat(to_date_str))
        except ValueError:
            pass

    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(bill_number__icontains=search_query)
        )

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Customer Report'

    # Header row styling
    header_fill   = PatternFill('solid', fgColor='E63946')
    header_font   = Font(bold=True, color='FFFFFF', size=11)
    header_align  = Alignment(horizontal='center', vertical='center')
    thin_border   = Border(
        left=Side(style='thin', color='D0D0D0'),
        right=Side(style='thin', color='D0D0D0'),
        top=Side(style='thin', color='D0D0D0'),
        bottom=Side(style='thin', color='D0D0D0'),
    )

    headers = ['#', 'Name', 'Mobile Number', 'Aadhar Number', 'Bill Number', 'Status', 'Registered Date', 'Registered Time']
    col_widths = [6, 28, 18, 20, 18, 12, 18, 16]

    for col_idx, (header, width) in enumerate(zip(headers, col_widths), start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.fill   = header_fill
        cell.font   = header_font
        cell.alignment = header_align
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.row_dimensions[1].height = 24

    # Alternating row fill
    alt_fill = PatternFill('solid', fgColor='FFF5F5')
    data_font = Font(size=10)
    center_align = Alignment(horizontal='center', vertical='center')

    for row_idx, customer in enumerate(customers.iterator(), start=2):
        row_fill = alt_fill if row_idx % 2 == 0 else None
        row_data = [
            customer.pk,
            customer.name,
            customer.mobile_number,
            customer.aadhar_number,
            customer.bill_number,
            'Played' if customer.has_played else 'Pending',
            customer.registered_at.strftime('%d-%m-%Y'),
            customer.registered_at.strftime('%H:%M'),
        ]
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font   = data_font
            cell.border = thin_border
            cell.alignment = center_align if col_idx in (1, 6, 7, 8) else Alignment(vertical='center')
            if row_fill:
                cell.fill = row_fill

        ws.row_dimensions[row_idx].height = 18

    # Freeze header row
    ws.freeze_panes = 'A2'

    # Build filename
    parts = ['customer_report']
    if from_date_str:
        parts.append(f'from_{from_date_str}')
    if to_date_str:
        parts.append(f'to_{to_date_str}')
    filename = '_'.join(parts) + '.xlsx'

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def check_duplicate(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '').strip()

    if not field or not value:
        return JsonResponse({'exists': False})

    exists = False
    if field == 'mobile_number':
        exists = Customer.objects.filter(mobile_number=value).exists()
    elif field == 'aadhar_number':
        exists = Customer.objects.filter(aadhar_number=value).exists()
    elif field == 'bill_number':
        exists = Customer.objects.filter(bill_number=value.upper()).exists()

    return JsonResponse({'exists': exists})


from django.contrib.auth.models import User
from .forms import UserForm

@admin_required
def user_list(request):
    users = User.objects.all().order_by('-is_staff', 'username')
    return render(request, 'customers/user_list.html', {'users': users})


@admin_required
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'customers/user_form.html', {'form': form, 'title': 'Create User'})


@admin_required
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    return render(request, 'customers/user_form.html', {'form': form, 'title': 'Edit User', 'editing': True})


@admin_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, 'You cannot delete your own user account.')
        return redirect('user_list')
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('user_list')
    
    return render(request, 'customers/user_confirm_delete.html', {'target_user': user})

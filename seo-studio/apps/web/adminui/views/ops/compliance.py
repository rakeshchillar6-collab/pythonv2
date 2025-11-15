# adminui/views/ops/compliance.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ...services.compliance import generate_compliance_report

@login_required
def compliance_dashboard(request):
    """
    Displays the validation matrix showing the implementation status
    of all major features.
    """
    report = generate_compliance_report()
    return render(request, 'adminui/pages/ops/compliance.html', {'report': report})

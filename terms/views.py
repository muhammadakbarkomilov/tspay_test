from django.shortcuts import render, get_object_or_404
from .models import SitePolicy

def policy_view(request, policy_type):
    policy = get_object_or_404(SitePolicy, title=policy_type)
    return render(request, 'pages/policy.html', {'policy': policy})


from django.shortcuts import render

def landing_page(request):
    return render(request, 'dot_app/index.html')

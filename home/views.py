from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.
def home (request):
    return render(request, "html/index.html")
# def success (request):
#     print("*"*10)
#     return HttpResponse("<h1>this is a sucess</h1>")
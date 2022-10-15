from django.http import HttpResponse
from django.template import loader
from .models import User


def index(request):
    user_list = User.objects.values_list()
    template = loader.get_template('spend4castapp/index.html')
    context = {'user_list': user_list,}
    return HttpResponse(template.render(context,request))    
    #return HttpResponse("Hello, world! You're at the spend4castapp index.")

def detail(request, user_id):
    return(HttpResponse("You're lookig at user %s" % user_id))

def home(request):
    template = loader.get_template('spend4castapp/home.html')
    return HttpResponse(template.render(request))
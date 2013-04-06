from django.shortcuts import render_to_response
from django.template import RequestContext
from webstore.models import *

# Create your views here.
def ProductsAll(request):
  products = Product.objects.all().order_by('name')
  events = Event.objects.all().order_by('name')
  context = ({'products': products, 'events': events})
  return render_to_response('productsall.html', context, context_instance=RequestContext(request))
  #request can be used to store user data like shopping cart
  

def SpecificProduct(request, productslug):
  product = Product.objects.get(slug=productslug)
  context = {'product': product}
  return render_to_response('singleproduct.html', context, context_instance=RequestContext(request))


def SpecificEvent(request, eventslug):
  event = Event.objects.get(slug=eventslug)
  photos = event.photos.all()
  context = {'event': event, 'photos': photos}
  return render_to_response('singleevent.html', context, context_instance=RequestContext(request))


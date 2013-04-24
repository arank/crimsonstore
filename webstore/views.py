from django.shortcuts import render_to_response
from django.template import RequestContext
from webstore.models import *
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from django.core.urlresolvers import reverse

# Create your views here.
def ProductsAll(request):
  products = Product.objects.all().order_by('name')
  context = ({'products': products})
  return render_to_response('productsall.html', context, context_instance=RequestContext(request))

  

def SpecificProduct(request, productslug):
  product = Product.objects.get(slug=productslug)
  context = {'product': product}
  return render_to_response('singleproduct.html', context, context_instance=RequestContext(request))


def EventsAll(request):
  categories = EventCategory.objects.all().order_by('name')
  context = ({'events': categories})
  return render_to_response('eventsall.html', context, context_instance=RequestContext(request))
 

def Category(request, categoryslug):
  single_category = EventCategory.objects.get(slug=categoryslug)
  events = Event.objects.filter(category=single_category)
  context = {'events': events, 'category':single_category}
  return render_to_response('category.html', context, context_instance=RequestContext(request))


def SpecificEvent(request, eventslug):
  event = Event.objects.get(slug=eventslug)
  photos = event.photos.all()#another way to get children via back reference
  context = {'event': event, 'photos': photos}
  return render_to_response('singleevent.html', context, context_instance=RequestContext(request))


def Cart(request):
  return render_to_response('cart.html', context_instance=RequestContext(request))

#########################


import re

from django.db.models import Q
def get_query(query_string, search_fields):
  ''' Returns a query, that is a combination of Q objects. That combination
        aims to search keywords within a model by testing the given search fields.
    
  '''
  query = None # Query to search for every search term        
  terms = normalize_query(query_string)
  for term in terms:
      or_query = None # Query to search for a given term in each field
      for field_name in search_fields:
          q = Q(**{"%s__icontains" % field_name: term})
          if or_query is None:
              or_query = q
          else:
              or_query = or_query | q
      if query is None:
          query = or_query
      else:
          query = query & or_query
  return query


def normalize_query(query_string,
                    findterms=re.compile(r'"([^"]+)"|(\S+)').findall,
                    normspace=re.compile(r'\s{2,}').sub):
  return [normspace(' ', (t[0] or t[1]).strip()) for t in findterms(query_string)]

def Search(request):
  query_string = ''
  found_entries = None
  query_string = request.GET['query']
  entry_query = get_query(query_string, ['name', 'slug', 'description'])
  if entry_query:     
    found_products = Product.objects.filter(entry_query).order_by('name')
    found_events = Event.objects.filter(entry_query).order_by('name')
  else:
    found_products=""
    found_events=""
  return render_to_response('search_results.html',
                          { 'query': query_string, 'products': found_products, 'events': found_events }, context_instance=RequestContext(request))

## PayPal ##
#############################
def Paypal(request):
  base_url = 'http://thecrimson.com/crimsonstore/'
  amount = request.POST['amount']
  paypal_dict = {
      "business": settings.PAYPAL_RECEIVER_EMAIL,
      "amount": "1.00",
      "item_name": "name of the item",
      "invoice": "unique-invoice-id",
      "notify_url": "%s%s" % (settings.SITE_NAME, reverse('paypal-ipn')),
      "return_url": base_url + 'success',
      "cancel_return": base_url + 'cancel'
  }

  # Create the instance.
  form = PayPalPaymentsForm(initial=paypal_dict)
  context = {"form": form.sandbox()}
  return render_to_response("paypal.html", context)

'''
def show_me_the_money(sender, **kwargs):
  ipn_obj = sender

  # Undertake some action depending upon `ipn_obj`.
  if ipn_obj.custom == "Upgrade all users!":
      Users.objects.update(paid=True)
  print __file__,1, 'This works'        
payment_was_successful.connect(show_me_the_money)
'''
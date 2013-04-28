from django.db.models import Q
from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from webstore.models import *
from webstore.paypal import Endpoint, verify_data


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
  base_url = request.build_absolute_uri('/checkout')
  context = {'base_url' : base_url}
  return render_to_response('cart.html', context, context_instance=RequestContext(request))

#########################


import re
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


#############################

## PayPal #*
@csrf_exempt
def Success(request):
  if request.method == 'POST':
    data = dict(request.POST.items())
  else:
    return redirect('/')

  data['base_url'] = request.build_absolute_uri()

  # Takes care of verifying data and emailing
  context = verify_data(data)

  if context['verified'] == 'yes':
    return render_to_response("success.html", context, context_instance=RequestContext(request))
  else:
    return render_to_response('wrong_order.html', context, context_instance=RequestContext(request))

def Cancel(request):
  return render_to_response('cancel.html', context_instance=RequestContext(request))

# IPN implementation
@csrf_exempt
class PaypalIPN(Endpoint):

  def process(self, data):
    context = get_context(request,data)
    return render_to_response("success.html", context, context_instance=RequestContext(request))
      
  def process_invalid(self, data):
    # should probably log this somewhere
    return render_to_response('cancel.html', context_instance=RequestContext(request))
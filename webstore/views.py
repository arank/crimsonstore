from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import RequestContext
from webstore.models import *
from paypal.standard.forms import PayPalPaymentsForm

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
  base_url = request.build_absolute_uri('/checkout/')
  context = {'base_url' : base_url}
  return render_to_response('cart.html', context, context_instance=RequestContext(request))

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


#############################

## PayPal #*
## We are using SimpleCartJS. This is the sample data fed to this view.
  ''' 
  currency=USD
  shipping=0
  tax=0
  taxRate=0
  itemCount=1
  item_name_1=Crew
  item_quantity_1=11
  item_price_1=200
  item_options_1=
  return=http%3A%2F%2Fcrimsonstore.heroku.com%2Fsuccess
  cancel_return=http%3A%2F%2Fcrimsonstore.heroku.com%2Fcancel
  '''
def Paypal(request):

  if request.method == 'POST':
      return redirect('/')

  # function to calculate shipping and tax. Returns (subtotal, tax, shipping)
  def subtotal_ship_tax(tax_rate = 0, ship_rate = 0, items = 0, price = 0):
    subtotal = items * price
    (subtotal, tax_rate * subtotal, ship_rate * items)

  # function to gracefully throw Wrong Order error
  def wrong_order(error, name, right_value, wrong_value):
    context = {'error':error,'item_name':name,'right_value':right_value,'wrong_value':wrong_value}
    return render_to_response('wrong_order.html', context, context_instance=RequestContext(request))

  # static vars
  base_url = 'http://crimsonstore.heroku.com/checkout/'
  item_count = int(request.GET['itemCount'])
  
  # keep track of total price
  total_price = 0
  total_tax = 0
  total_ship = 0

  # Verify each item (price, shipping, tax)
  while item_count > 0 :

    # item data from request
    item_name = request.GET['item_name_' + item_count]
    item_price = request.GET['item_price_' + item_count]
    item_quantity = request.GET['item_quantity_' + item_count]

    # item data from database
    db_item = Event.objects.get(name=item_name)
    db_price = db_item.price_in_dollars

    # verifying price
    if db_price != item_price:
        wrong_order('price', item_name, db_price, item_price)

    # tax data
    tax_rate = request.GET['taxRate']

    # summing it up
    (subtotal, tax, shipping) = subtotal_ship_tax(tax_rate, 0, item_quantity, db_price)
    total_price += subtotal
    total_tax += tax
    total_ship += shipping

  # verifying totals
  if total_tax != request.GET['tax']:
    wrong_order('tax', 'order', total_tax, request.GET['tax'])

  if total_ship != request.GET['shipping']:
    wrong_order('shipping', 'order', total_ship, request.GET['shipping'])

  # verifying payment is in US dollars
  if request.GET['currency'] != 'USD':
      wrong_order('currency', 'currency', 'USD', request.GET['currency'])

  total = total_ship + total_tax + total_price

  import random
  import time

  invoice_id = random.randint(0,settings.MAX_INVOICE)
  invoice_id += time.clock()

  paypal_dict = {
      "business": settings.PAYPAL_RECEIVER_EMAIL,
      "amount": total,
      "item_name": "Crimson Store Purchase",
      "invoice": invoice_id,
      "notify_url": "http://crimsonstore.heroku.com/cr!ms0n/p4yp5l/E2E7135958416E4B12258FD3641FD/OwEv0w0ZVt",
      "return_url": base_url + 'success',
      "cancel_return": base_url + 'cancel',
      "custom": True
  }

  # Create the instance.
  form = PayPalPaymentsForm(initial=paypal_dict)

  # change to form.render() when live. form.sandbox() when testing
  context = {"form": form.sandbox()}

  return render_to_response("paypal.html", context, context_instance=RequestContext(request))
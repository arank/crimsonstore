from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
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
  base_url = request.build_absolute_uri('/checkout')
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
@csrf_exempt
def Success(request):

  # function to gracefully throw Wrong Order error
  def wrong_order(error, name, right_value, wrong_value):
    context = {'error':error,'item_name':name,'right_value':right_value,'wrong_value':wrong_value}
    return render_to_response('wrong_order.html', context, context_instance=RequestContext(request))

  # function to verify overall request
  def verify(request, name):
    # payer verification
    payment_status = request.POST.get('payment_status', '')
    if payment_status != 'Completed':
      wrong_order('uncompleted', name, 'Completed', payment_status)

    payer_status = request.POST.get('payer_status', '')
    if payer_status != 'verified':
      wrong_order('unverified', name, 'verified', payer_status)

  # function to verify item (subtotal, tax, and shipping)
  def subtotal_ship_tax(tax_rate, shipping_rate, price, quantity):
    subtotal = price * quantity
    tax = tax_rate * subtotal
    shipping = shipping_rate * subtotal
    return (sutotal, tax, shipping)
    
  if request.method == 'GET':
    return redirect('/')

  # customer name
  first_name = request.POST.get('first_name', '')
  last_name = request.POST.get('last_name', '')
  name = first_name + last_name

  verify(request, name)

  # item verification
  item_count = int(request.POST.get('num_cart_items', '0'))
  if item_count == 0:
    wrong_order('zero_items', name, 1, item_count)

  form_total = float(request.POST['mc_gross']) - float(request.POST['mc_fee'])
  if form_total == 0.0:
    wrong_order('zero_payment', name, 1., total)

  # other data
  tax = float(request.POST.get('tax','0.0'))
  ship_handle = float(request.POST.get('mc_shipping','0.0')) + float(request.POST['mc_handling']) 

  # keep track of total price, tax, and ship
  db_total = 0
  db_tax = 0
  db_ship = 0

  # Verify each item (price, shipping, tax)
  for x in range(1, item_count + 1) :

    xstring = str(x)

    # item data from request
    item_name = request.POST['item_name' + xstring]
    item_quantity = int(request.POST['quantity' + xstring])
    item_price = float(request.POST['mc_gross_' + xstring])
    item_shipping = float(request.POST['mc_shipping' + xstring]) + float(request.POST['mc_shipping' + xstring])
    item_tax = float(request.POST['tax' + xstring])

    # item data from database (replace this with ID soon)
    db_item = Event.objects.get(name=item_name)
    db_price = float(db_item.price_in_dollars)

    # summing it up
    (subtotal, tax, shipping) = subtotal_ship_tax(0.0, 0.0, item_quantity, db_price)

    if subtotal != item_price:
      wrong_order('price', item_name, subtotal, item_price)

    if tax != item_tax:
      wrong_order('tax', item_name, tax, item_tax)

    if shipping != item_shipping:
      wrong_order('shipping', item_name, shipping, item_shipping)

    total_price += subtotal
    total_tax += tax
    total_ship += shipping

  # verifying totals
  form_tax = float(request.POST['tax'])
  form_shipping = float(request.POST['mc_handling']) + float(request.POST['mc_shipping'])
  form_currency = request.POST['mc_currency']
  if total_tax != form_tax :
    wrong_order('tax', name, total_tax, form_tax)

  if total_ship != form_shipping:
    wrong_order('shipping', 'name', total_ship, form_shipping)

  # verifying payment is in US dollars
  if form_currency != 'USD':
      wrong_order('currency', name, 'USD', form_currency)

  total = db_ship + db_tax + db_price

  if total != form_total:
    wrong_order('total', name, total, form_total)

  # send email
  email = request.POST['payer_email']

  context = {
      "business": settings.PAYPAL_RECEIVER_EMAIL,
      "amount": total,
      "name": name,
      "email": email }

  return render_to_response("success.html", context, context_instance=RequestContext(request))

def Cancel(request):
  return render_to_response('cancel.html', context, context_instance=RequestContext(request))

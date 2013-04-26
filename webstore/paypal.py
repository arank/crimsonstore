from django.shortcuts import render_to_response
from django.shortcuts import redirect
from django.conf import settings
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
from django.template import RequestContext
from webstore.models import *
from django.http import HttpResponse
import urllib

class Endpoint:
    
    default_response_text = 'Nothing to see here'
    verify_url = "https://www.paypal.com/cgi-bin/webscr"
    
    def do_post(self, url, args):
        return urllib.urlopen(url, urllib.urlencode(args)).read()
    
    def verify(self, data):
        args = {
            'cmd': '_notify-validate',
        }
        args.update(data)
        return self.do_post(self.verify_url, args) == 'VERIFIED'
    
    def default_response(self):
        return HttpResponse(self.default_response_text)
    
    def __call__(self, request):
        r = None
        if request.method == 'POST':
            data = dict(request.POST.items())
            # We need to post that BACK to PayPal to confirm it
            if self.verify(data):
                r = self.process(data)
            else:
                r = self.process_invalid(data)
        if r:
            return r
        else:
            return self.default_response()
    
    def process(self, data):
        pass
    
    def process_invalid(self, data):
        pass

class AppEngineEndpoint(Endpoint):
    
    def do_post(self, url, args):
        from google.appengine.api import urlfetch
        return urlfetch.fetch(
            url = url,
            method = urlfetch.POST,
            payload = urllib.urlencode(args)
        ).content


# Own internal data verification
def verify_data(data):

  # function to gracefully throw Wrong Order error
  def wrong_order(error, name, right_value, wrong_value):
    context = {'error':error,'item_name':name,'right_value':right_value,'wrong_value':wrong_value}
    return render_to_response('wrong_order.html', context, context_instance=RequestContext(request))

  # function to verify overall data
  def verify(data, name):
    # payer verification
    payment_status = data.get('payment_status', '')
    if payment_status != 'Completed':
      wrong_order('uncompleted', name, 'Completed', payment_status)

    payer_status = data.get('payer_status', '')
    if payer_status != 'verified':
      wrong_order('unverified', name, 'verified', payer_status)

  # function to verify item (subtotal, tax, and shipping)
  def subtotal_ship_tax(tax_rate, shipping_rate, price, quantity):
    subtotal = price * quantity
    tax = tax_rate * subtotal
    shipping = shipping_rate * subtotal
    return (subtotal, tax, shipping)

  # customer name
  first_name = data.get('first_name', '')
  last_name = data.get('last_name', '')
  name = first_name + last_name

  verify(data, name)

  # item verification
  item_count = int(data.get('num_cart_items', '0'))
  if item_count == 0:
    wrong_order('zero_items', name, 1, item_count)

  form_total = float(data['mc_gross']) - float(data['mc_fee'])
  if form_total == 0.0:
    wrong_order('zero_payment', name, 1., total)

  # other data
  tax = float(data.get('tax','0.0'))
  ship_handle = float(data.get('mc_shipping','0.0')) + float(data['mc_handling']) 

  # keep track of total price, tax, and ship
  total_price = 0
  total_tax = 0
  total_ship = 0

  photo_urls = {}

  # Verify each item (price, shipping, tax)
  for x in range(1, item_count + 1) :

    xstring = str(x)

    # item data from request
    item_name = data['item_name' + xstring]
    item_quantity = int(data['quantity' + xstring])
    item_price = float(data['mc_gross_' + xstring])
    item_shipping = float(data['mc_shipping' + xstring]) + float(data['mc_shipping' + xstring])
    item_tax = float(data['tax' + xstring])

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

    photos = [db_item.photo1, db_item.photo2, db_item.photo3]
    photo_urls[item_name] = photos

  # verifying totals
  form_tax = float(data['tax'])
  form_shipping = float(data['mc_handling']) + float(data['mc_shipping'])
  form_currency = data['mc_currency']
  if total_tax != form_tax :
    wrong_order('tax', name, total_tax, form_tax)

  if total_ship != form_shipping:
    wrong_order('shipping', 'name', total_ship, form_shipping)

  # verifying payment is in US dollars
  if form_currency != 'USD':
      wrong_order('currency', name, 'USD', form_currency)

  total = total_ship + total_tax + total_price

  if total != form_total:
    wrong_order('total', name, total, form_total)

  # send email here
  email = data['payer_email']

  context = {
      "business": settings.PAYPAL_RECEIVER_EMAIL,
      "amount": total,
      "name": name,
      "email": email }

  return context
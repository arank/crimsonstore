from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, Http404
from django.template.loader import  get_template
from django.template import Context
from webstore.models import *
import urllib

# Modified from Django Snippets
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

def send_email(data):
  plaintext = get_template('email.txt')
  html = get_template('email.html')

  d = Context(data)
  subject, from_email = 'CrimsonStore Purchase', 'crimsonstore@thecrimson.com'
  text_content = plaintext.render(d)
  html_content = html.render(d)
  to_list = [data['email']]
  if data['verified'] == 'no':
    to_list.append(settings.PAYPAL_RECEIVER_EMAIL)

  for to in to_list:
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.content_subtype = "html"
    msg.send()

  return True

# function to gracefully throw Wrong Order error
def wrong_order(error, name, right_value, wrong_value,base_url):
  context = { 'verified'      : 'no',
              'business'      : settings.PAYPAL_RECEIVER_EMAIL,
              'error'         : error,
              'item_name'     : name,
              'right_value'   : right_value,
              'wrong_value'   : wrong_value,
              'base_url'      : base_url }
  if send_email(context):
    return context
  else:
    raise Http404

# function to verify item (subtotal, tax, and shipping)
def subtotal_ship_tax(tax_rate, shipping_rate, price, quantity):
  subtotal = price * quantity
  tax = tax_rate * subtotal
  shipping = shipping_rate * subtotal
  return (subtotal, tax, shipping)  

# Own internal data verification
# Will return something like the below, where item_name is the first item with the invalid data
'''
context = { 'verified'      : 'no',
              'error'         : error,
              'item_name'     : name,
              'right_value'   : right_value,
              'wrong_value'   : wrong_value }  '''
# Otherwise context will basically contain the following:
'''
context = { 'verified'  : 'yes',
            'business'  : settings.PAYPAL_RECEIVER_EMAIL,
            'amount'    : total,
            'name'      : name,
            'email'     : email }
'''
def verify_data(data):

  # function to verify overall data
  def verify(data, name):
    # payer verification
    payment_status = data.get('payment_status', '')
    if payment_status != 'Completed':
      wrong_order('was uncompleted', name, 'Completed', payment_status,data['base_url'])

    payer_status = data.get('payer_status', '')
    if payer_status != 'verified':
      wrong_order('was unverified', name, 'verified', payer_status,data['base_url'])

  # customer name
  first_name = data.get('first_name', '')
  last_name = data.get('last_name', '')
  name = first_name + ' ' + last_name

  verify(data, name)

  # item verification
  item_count = int(data.get('num_cart_items', '0'))
  if item_count == 0:
    wrong_order('had zero items', name, 1, item_count,data['base_url'])

  form_total = float(data['mc_gross']) # - float(data['mc_fee'])
  if form_total == 0.0:
    wrong_order('had to payment', name, 1., total,data['base_url'])

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
    event_name = data['item_name' + xstring]
    p_quantity = int(data['quantity' + xstring])
    p_price = float(data['mc_gross_' + xstring])
    p_shipping = float(data['mc_shipping' + xstring]) + float(data['mc_shipping' + xstring])
    p_tax = float(data['tax' + xstring])

    # item data from database (replace this with ID soon)
    db_event = Event.objects.get(name=event_name)
    db_price = float(db_event.price_in_dollars)

    # summing it up
    (subtotal, tax, shipping) = subtotal_ship_tax(0.0, 0.0, p_quantity, db_price)

    if subtotal != p_price:
      wrong_order('had wrong price', event_name, subtotal, p_price,data['base_url'])

    if tax != p_tax:
      wrong_order('had wrong tax', event_name, tax, p_tax,data['base_url'])

    if shipping != p_shipping:
      wrong_order('had wrong shippping', event_name, shipping, p_shipping,data['base_url'])

    total_price += subtotal
    total_tax += tax
    total_ship += shipping

    photos = Photo.objects.filter(event=db_event)
    photo_urls[event_name] = [photo.originalURL for photo in photos]

  # verifying totals
  form_tax = float(data['tax'])
  form_shipping = float(data['mc_handling']) + float(data['mc_shipping'])
  form_currency = data['mc_currency']
  if total_tax != form_tax :
    wrong_order('tax', name, total_tax, form_tax,data['base_url'])

  if total_ship != form_shipping:
    wrong_order('had wrong shipping', 'name', total_ship, form_shipping)

  # verifying payment is in US dollars
  if form_currency != 'USD':
      wrong_order('had wrong currency', name, 'USD', form_currency,data['base_url'])

  total = total_ship + total_tax + total_price

  if total != form_total:
    wrong_order('had wrong total', name, total, form_total,data['base_url'])

  # send email here TODO
  email = data['payer_email']

  context = { 'verified'  : 'yes',
              'business'  : settings.PAYPAL_RECEIVER_EMAIL,
              'amount'    : total,
              'name'      : name,
              'email'     : email,
              'photos'    : photo_urls,
              'base_url'  : data['base_url'],
              'data'      : data }

  if send_email(context):
    return context
  else:
    raise Http404
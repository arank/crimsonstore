from django.contrib import admin
import json as j
import smug_lib
from webstore.models import *

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse



class ProductAdmin(admin.ModelAdmin):
  prepopulated_fields = {'slug': ('name',)}
  list_display = ('name', 'category') 

class EventAdmin(admin.ModelAdmin):
  prepopulated_fields = {'slug': ('name',)}
  list_display = ('name', 'category') 

admin.site.register(Catalog)

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductCategory)

admin.site.register(Photo)
admin.site.register(Event, EventAdmin)
admin.site.register(EventCategory)

@staff_member_required
def sync_setup(request):
    smugmug = smug_lib.login(False)
    remote_albums = len(smugmug.albums_get(NickName="thecrimson")["Albums"])
    local_albums = len(Event.objects.all())
    message_style = "warning" if remote_albums > local_albums else "success"
    context = {'n_remote'      : remote_albums,
               'n_local'       : local_albums, 
               'diff'          : remote_albums - local_albums,
               'message_class' : message_style}
    return render_to_response('admin/syncdb.html', context, context_instance=RequestContext(request))

@staff_member_required
def sync_async(request):        
    if request.method == "POST":
        if not request.POST.__contains__('n'):
            message = "Malformed request. Try again or contact a tech associate."
            data = {"success": False,
                    "message": message}
            json = j.dumps(data)
            return HttpResponse(json, mimetype='application/json')
        n = request.POST["n"]
        if not n.isdigit():
            message = "Malformed request. Try again or contact a tech associate."
            data = {"success": False,
                    "message": message}
            json = j.dumps(data)
            return HttpResponse(json, mimetype='application/json')
        try:
            smug_lib.sync_all(True)
            smugmug = smug_lib.login(False)
            remote_albums = len(smugmug.albums_get(NickName="thecrimson")["Albums"])
            local_albums = len(Event.objects.all())
            message = "Database successfully synced with SmugMug"
            data = {"success" : True,
                    "message" : message,
                    "n_remote": remote_albums,
                    "n_local" : local_albums}
            json = j.dumps(data)
            return HttpResponse(json, mimetype='application/json')
        except Exception, arg:
            message = arg.__class__.__name__ + ": " + str(arg)
            print message
            data = {"success": False,
                    "message": message}
            print data
            json = j.dumps(data)
            return HttpResponse(json, mimetype='application/json')

    else:
        message = "Use the sync button at /admin/syncdb to sync the database"
        data = {"success": False,
                "message": message}
        json = j.dumps(data)
        return HttpResponse(json, mimetype='application/json')







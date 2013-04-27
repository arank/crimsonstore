from django.db import models

# Create your models here.

	
class Catalog(models.Model):
  name = models.CharField(max_length=255)
  slug = models.SlugField(max_length=150)
  publisher = models.CharField(max_length=300)
  description = models.TextField()
  def __unicode__(self):
    return u'%s' % (self.name)

class Product(models.Model):
  category = models.ForeignKey('ProductCategory',
                            related_name='products')
  name = models.CharField(max_length=300)
  slug = models.SlugField(max_length=150)
  description = models.TextField()
  photo = models.ImageField(upload_to='product_photos/')
  manufacturer = models.CharField(max_length=300,
                                           blank=True)
  price_in_dollars = models.DecimalField(max_digits=6,
                                      decimal_places=2)
  def __unicode__(self):
    return u'%s' % (self.name)

class ProductCategory(models.Model):
  catalog = models.ForeignKey('Catalog',
                             related_name='product_categories')
  parent = models.ForeignKey('self', blank=True, null=True,
                             related_name='children')
  name = models.CharField(max_length=300)
  slug = models.SlugField(max_length=150)
  description = models.TextField(blank=True)
  def __unicode__(self):
    if self.parent:
      return u'%s: %s - %s' % (self.catalog.name,
                               self.parent.name,
                               self.name)
    return u'%s: %s' % (self.catalog.name, self.name)

# Corresponds to Category on SmugMug
class EventCategory(models.Model):
  catalog = models.ForeignKey('Catalog',
                             related_name='event_categories')
  name = models.CharField(max_length=300)
  slug = models.SlugField(max_length=150) 
  description = models.TextField()
  # photo1 = models.ImageField(upload_to='product_photos/') 
  # photo2 = models.ImageField(upload_to='product_photos/')
  # photo3 = models.ImageField(upload_to='product_photos/')
  def __unicode__(self):
    return u'%s' % (self.name)
  def get_key_images(self):
    return Photo.objects.filter(keyImageForCategory=self)[:3]

# Corresponds to Album on SmugMug
class Event(models.Model):
  name = models.CharField(max_length=300)
  slug = models.SlugField(max_length=150)
  date = models.DateField()
  price_in_dollars = models.DecimalField(max_digits=6,
                                      decimal_places=2)
  category = models.ForeignKey('EventCategory',
                           related_name='events')
  description = models.TextField()
  photographer = models.CharField(max_length=300)
  # photo1 = models.ImageField(upload_to='product_photos/') 
  # photo2 = models.ImageField(upload_to='product_photos/')
  # photo3 = models.ImageField(upload_to='product_photos/')
  def __unicode__(self):
    return u'%s' % (self.name)
  def get_key_images(self):
    return Photo.objects.filter(keyImageForEvent=self)[:3]

# Corresponds to Images from 
class Photo(models.Model):
  event = models.ForeignKey('Event',
                           related_name='photos')
  keyImageForCategory = models.ForeignKey(EventCategory, null=True, blank=True)
  keyImageForEvent    = models.ForeignKey(Event, null=True, blank=True)
  lightboxURL = models.URLField()
  largeURL    = models.URLField()
  mediumURL   = models.URLField()
  originalURL = models.URLField()
  smallURL    = models.URLField()
  thumbURL    = models.URLField()
  tinyURL     = models.URLField()
  url         = models.URLField() 

##########################

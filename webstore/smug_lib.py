import login_info
import datetime
from models import *
import re
from smugpy import SmugMug
import sys


# Sync n albums
def sync_n(n, verbose=False):
    smugmug = login(verbose)
    # 
    # I'm not sure what Catalogs are, so I'm doing this for now.  This obviously 
    # needs to be changed eventually
    # 
    if len(Catalog.objects.all()) == 0:
        catalog = Catalog(name        = "Test",
                          slug        = "test",
                          publisher   = "Josh Palay",
                          description = "A Cateogory for internal organization!")
        catalog.save()
    else:
        catalog = Catalog.objects.all()[0]

    albums = smugmug.albums_get(NickName="thecrimson")["Albums"][:n]
    album_len = len(albums)
    events = [event.slug for event in Event.objects.all()]
    for index, album in enumerate(albums):
        
        # Add EventCategory if it doesn't already exist
        cat_name = album["Category"]["Name"]
        categories = EventCategory.objects.filter(slug=slugify(cat_name))
        new_category = False
        if categories == []:
            if verbose:
                print "ADDING CATEGORY " + cat_name + " TO DATABSE..."
            slug = slugify(cat_name)
            category = EventCategory(catalog=catalog, name=cat_name, slug=slug, 
                description="Default description")
            category.save()
            if verbose:
                print "ADDED CATEGORY\n"
            new_category = True
        else:
            category = categories[0]

        # Add Event to database
        if verbose:
            print "ADDING EVENT " + album["Title"] + " TO DATABASE ("  + \
            str(index + 1) + " of " + str(album_len) + ")..."
        if slugify(album["Title"]) not in events:
            addl_info = smugmug.albums_getInfo(AlbumID=album["id"], 
                AlbumKey=album["Key"])["Album"]
            name = album["Title"]
            slug = slugify(name)
            description = addl_info["Description"]
            date = date_or_now(addl_info["LastUpdated"])

            # if verbose:
            #     print date
            # if verbose:
            #     print name
            # if verbose:
            #     print description + "\n"

            # TODO: Get price, photographer names, and other info
            default_price_in_dollars = 42

            # print name
            # print slug
            # print date
            # print default_price_in_dollars
            # try:
            #     print category
            # except Exception, arg:
            #     print arg.__class__.__name__ + ": " + str(arg)
            #     exit()
            # print description

            # print "about to make event"
            event = Event(name=name, slug=slug, date=date, 
                price_in_dollars=default_price_in_dollars, category=category, 
                description=description)

            event.save()
            if verbose:
                print "ADDED EVENT\n"
            events.append(slug)
            

            event.save()

            photos = []
            # Save Images associated with Event
            images = smugmug.images_get(AlbumKey=album["Key"], 
                AlbumID=album["id"])["Album"]["Images"]

            img_len = len(images)
            if verbose:
                print "ADDING " + str(img_len) + " IMAGES RELATED TO " + \
                album["Title"] + " TO DATABASE..."
            
            for index, img in enumerate(images):
                urls = smugmug.images_getURLs(ImageID=img["id"], ImageKey=img["Key"])
                largeURL    = str(urls["Image"]["LargeURL"])
                lightboxURL = str(urls["Image"]["LightboxURL"])
                mediumURL   = str(urls["Image"]["MediumURL"])
                originalURL = str(urls["Image"]["OriginalURL"])
                smallURL    = str(urls["Image"]["SmallURL"])
                thumbURL    = str(urls["Image"]["ThumbURL"])
                tinyURL     = str(urls["Image"]["TinyURL"])
                url         = str(urls["Image"]["URL"])

                photo = Photo(event=event, largeURL    = largeURL,
                                           lightboxURL = lightboxURL,
                                           mediumURL   = mediumURL,
                                           originalURL = originalURL,
                                           smallURL    = smallURL,
                                           thumbURL    = thumbURL,
                                           tinyURL     = tinyURL,
                                           url         = url)
                photos.append(photo)
                photo.save()
                if verbose:
                    print "ADDED IMAGE " + str(index + 1) + " OF " + str(img_len)
           
            if verbose:
                print ""
            set_default_event_photos(event, photos[:3])
        elif verbose:
            print "EVENT ALREADY IN DATABASE"
        if new_category:
            set_default_category_photos(category, photos[:3])

def sync_all(verbose=False):
    sync_n(sys.maxint, verbose)

def login(verbose):
    if verbose:
        print "LOGGING IN..."
    smugmug = SmugMug(api_key=login_info.API_KEY, api_version="1.2.2", 
        app_name="CrimsonStore")

    smugmug.login_withPassword(EmailAddress=login_info.USER_NAME, 
        Password=login_info.PASSWORD)

    if verbose:
        print "LOGGED IN\n"

    return smugmug

def set_default_category_photos(category, photos):
    for photo in photos[:3]:
        photo.keyImageForCategory = category
        photo.save()

def set_default_event_photos(event, photos):
    for photo in photos[:3]:
        photo.keyImageForEvent = event
        photo.save()

def date_or_now(s):
    try:
        return datetime.datetime.strptime(s, 
            "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.datetime.now()

# Stolen from stackoverflow.com/questions/5574042/string-slugification-in-python
def slugify(s):
    return re.sub(r'\W+','-', s.lower())
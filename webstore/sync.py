import login_info
import datetime
from models import *
import re
from smugpy import SmugMug


# Sync n albums
def sync_n(n):
    print "LOGGING IN..."
    smugmug = SmugMug(api_key=login_info.API_KEY, api_version="1.2.2", 
        app_name="CrimsonStore")

    smugmug.login_withPassword(EmailAddress=login_info.USER_NAME, 
        Password=login_info.PASSWORD)

    print "LOGGED IN\n"
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
    categories = dict()
    for index, album in enumerate(albums):
        cat_name = album["Category"]["Name"]
        new_category = False
        # Add EventCategory if it doesn't already exist
        if cat_name not in categories.keys():
            print "ADDING CATEGORY " + cat_name + " TO DATABSE..."
            slug = slugify(cat_name)
            category = EventCategory(catalog=catalog, name=cat_name, slug=slug, 
                description="Default description")
            category.save()
            categories[cat_name] = category
            new_category = True
            print "ADDED CATEGORY\n"

        # Add Event to database
        print "ADDING EVENT " + album["Title"] + " TO DATABASE ("  + \
            str(index + 1) + " of " + str(album_len) + ")..."
        addl_info = smugmug.albums_getInfo(AlbumID=album["id"], 
            AlbumKey=album["Key"])["Album"]
        name = album["Title"]
        slug = slugify(name)
        category = categories[cat_name]
        description = addl_info["Description"]
        date = date_or_now(addl_info["LastUpdated"])

        # print date
        # print name
        # print description + "\n"

        # TODO: Get price, photographer names, and other info
        default_price_in_dollars = 42

        event = Event(name=name, slug=slug, date=date, 
            price_in_dollars=default_price_in_dollars, category=category, 
            description=description)

        event.save()
        print "ADDED EVENT\n"

        # try:
        #     event.save()
        # except:
        #     print addl_info["LastUpdated"]
        #     exit()

        photos = []
        # Save Images associated with Event
        images = smugmug.images_get(AlbumKey=album["Key"], 
            AlbumID=album["id"])["Album"]["Images"]

        img_len = len(images)
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
            print "ADDED IMAGE " + str(index + 1) + " OF " + str(img_len)
        print ""
        set_default_event_photos(event, photos[:3])

        if new_category:
            set_default_category_photos(category, photos[:3])

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
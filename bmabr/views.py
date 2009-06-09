
# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.contrib import auth
from django.contrib.auth.forms import UserCreationForm
from django.template import Context


from django.contrib.gis.geos import GEOSGeometry, fromstr
from django.contrib.gis.shortcuts import render_to_kml
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

from fixcity.bmabr.models import Rack, Comment
from fixcity.bmabr.models import Neighborhoods
from fixcity.bmabr.models import CommunityBoard
from fixcity.bmabr.models import RackForm, CommentForm
from fixcity.bmabr.models import Rack_Document, Rack_Photo

from django.contrib.gis.geos import fromstr

from django.contrib import auth

from reportlab.pdfgen import canvas 
from geopy import geocoders

cb_metric = 50.00 
GKEY="ABQIAAAApLR-B_RMiEN2UBRoEWYPlhT2yXp_ZAY8_ufC3CFXhHIE1NvwkxRzLpaA-QUSeKPxm0Vj9Bgee3eRDg"
g = geocoders.Google(GKEY)
SRID=4326

def user_context(request):
    return {
        'user': request.user
    }

def index(request):
    return render_to_response('index.html',
       {'request':request},
       context_instance=RequestContext(request, processors=[user_context])
                              ) 

def login(request): 
#    ref_url = request.GET['ref_url'] 
    if request.method == 'POST': 
        username = request.POST.get('username')
        password = request.POST.get('password') 
        user = auth.authenticate(username=username,password=password)
        if user is not None and user.is_active: 
            auth.login(request, user)
            return HttpResponseRedirect("/")
        else: 
            return HttpResponseRedirect("/user/error/")
    else: 
        pass 
    return render_to_response('login.html', 
       context_instance=RequestContext(request, processors=[user_context])
                              )

def logout(request): 
        auth.logout(request)
        return HttpResponseRedirect("/")


def built(request): 
    rack = Rack.objects.all()
    rack_extent = rack.extent()
    return render_to_response('built.html',{ 
            'rack_extent': rack_extent},
            context_instance=RequestContext(request, processors=[user_context])
            )


def get_communityboard(request):
    lat = request.POST['lat'] 
    lon = request.POST['lon'] 
    point = 'POINT(%s %s)' % (lon,lat)
    pnt = fromstr(point,srid=4326)
    cb = CommunityBoard.objects.get(the_geom__contains=pnt)  
    return HttpResponse(cb.gid)

def geocode(request): 
    location = request.POST['geocode_text']
    (place, point) = g.geocode(location)
    return HttpResponse(place, point)

def reverse_geocode(request): 
    lat = request.POST['lat'] 
    lon = request.POST['lon']
    point = (lat, lon)
    (new_place,new_point) = g.reverse(point)
    return HttpResponse(new_place)

def submit_all(request): 
    ''' 
    needs major re-working
    ''' 
    community_board_query = CommunityBoard.objects.filter() 
    return render_to_response('submit.html', {
            'community_board_query': community_board_query,
            })



def submit(request): 
    community_board_query = CommunityBoard.objects.filter(name='1')
    for communityboard in community_board_query:         
        racks_query = Rack.objects.filter(location__contained=communityboard.the_geom)
        racks_count = Rack.objects.filter(location__contained=communityboard.the_geom).count()
        cb_metric_percent = racks_count/cb_metric 
        cb_metric_percent = cb_metric_percent * 100 
        community_board_query_extent = community_board_query.extent()
    return render_to_response('submit.html', {
            'community_board_query': community_board_query,
            'cb_metric_percent':cb_metric_percent,
            'racks_query': racks_query,
            'racks_count': racks_count,
            'community_board_query_extent': community_board_query_extent,
            },
             context_instance=RequestContext(request, processors=[user_context])            
             )

def submit_pdf(request): 
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; racks.pdf'    
    p = canvas.Canvas(response)
    p.setFont("Helvetica", 18)
    p.setTitle("BUILD ME A BIKE RACK")
    p.drawString(10,800,"BUILD ME A BIKE RACK")
    p.line(0,0,0,0)
    p.setFont("Helvetica", 12)
    rack_query = Rack.objects.all()
    positionY = 700
    positionX = 10
    for rack in rack_query:         
        p.drawString(positionX,positionY,rack.address)
        positionMeta = positionY - 10 
        p.drawString(positionX,positionMeta,rack.meta)
        positionY = positionY - 100 
    p.showPage()
    p.save()
    return response


def assess(request): 
    racks_query = Rack.objects.all()
    return render_to_response('assess.html', { 
            'rack_query': racks_query,
            },
            context_instance=RequestContext(request, processors=[user_context])) 

def assess_by_communityboard(request,cb_id): 
    rack_query = Rack.objects.filter(communityboard=cb_id)    
    return render_to_response('assess_communityboard.html', { 
            'rack_query':rack_query
            },
            context_instance=RequestContext(request, processors=[user_context]))


def newrack_form(request): 
    if request.method == 'POST':
        form = RackForm(request.POST,request.FILES)            
        if form.is_valid(): 
            new_rack = form.save()
            return HttpResponseRedirect('/assess/')  
    else:
        form = RackForm()
    return render_to_response('newrack.html', { 
            'form': form,
           },
           context_instance=RequestContext(request, processors=[user_context])) 


def rack(request,rack_id): 
    rack_query = Rack.objects.filter(id=rack_id)    
    comment_query = Comment.objects.filter(rack=rack_id)
    photo_query = Rack_Photo.objects.filter(ph_rack=rack_id)
    document_query = Rack_Document.objects.filter(doc_rack=rack_id)
    return render_to_response('rack.html', { 
            'rack_query': rack_query,            
            'comment_query': comment_query,
            'photo_query': photo_query, 
            'document_query': document_query,
            },
                              context_instance=RequestContext(request, processors=[user_context])) 
           
    

def add_comment(request): 
    form = CommentForm(request.POST)
    rack_id = request.POST['rack']
    if form.is_valid(): 
        new_comment = form.save()
        return HttpResponseRedirect('/rack/%s#comments'% rack_id )   
    else: 
        return HttpResponseRedirect('/error/comment') 


def updatephoto(request,rack_id): 
    rack_query = Rack.objects.get(id=rack_id) 
    rack_photo = request.FILES['photo']
    rack = Rack(id=rack_query.id,address=rack_query.address,title=rack_query.title,date=rack_query.date,description=rack_query.description,email=rack_query.email,communityboard=rack_query.communityboard,photo=rack_photo,status=rack_query.status,location=rack_query.location)
    rack.save()
    return HttpResponse(rack)

    
def rack_all_kml(request): 
    racks = Rack.objects.all()
    return render_to_kml("placemarkers.kml", {'racks' : racks}) 


def rack_requested_kml(requst): 
    racks = Rack.objects.filter(status='suggest')
    return render_to_kml("placemarkers.kml", {'racks' : racks}) 




def community_board_kml(request): 
    community_boards = CommunityBoard.objects.all()
    return render_to_kml("community_board.kml",{'community_boards': community_boards})
 

def community_board_kml_by_id(request,cb_id): 
    community_boards = CommunityBoard.objects.filter(gid=cb_id)
    return render_to_kml("community_board.kml",{'community_boards': community_boards})

def rack_pendding_kml(request): 
    racks = Rack.objects.filter(status='a')
    return render_to_kml("placemarkers.kml", {'racks' : racks}) 


def rack_built_kml(request): 
    racks = Rack.objects.filter(status='a')
    return render_to_kml("placemarkers.kml", {'racks' : racks}) 


def rack_by_id_kml(request, rack_id): 
    racks = Rack.objects.filter(id=rack_id)
    return render_to_kml("placemarkers.kml",{'racks':racks})


def neighborhoods(request): 
    neighborhood_list = Neighborhoods.objects.all()
    return render_to_response('neighborhoods.html', {'neighborhood_list': neighborhood_list})


def communityboard(request): 
    communityboard_list = CommunityBoard.objects.all()      
    return render_to_response('communityboard.html', { 
            "communityboard_list": communityboard_list  
            }
           )


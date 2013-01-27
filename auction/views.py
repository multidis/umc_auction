# Create your views here.
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from models import Bidder, Item, Purchase
from forms import *

@login_required
def index(request):
    return render_to_response('auction/index.html', {}, context_instance=RequestContext(request))

@login_required
def items(request):
    return render_to_response('auction/items.html', {'items':Item.objects.all()}, context_instance=RequestContext(request))

@login_required
def bidders(request):
    return render_to_response('auction/bidders.html', {'bidders':Bidder.objects.all()}, context_instance=RequestContext(request))

@login_required
def item(request, item_id):
    i = get_object_or_404(Item, id=item_id)
    if request.method == 'POST': 
        form = ItemForm(request.POST, instance=i)
        if form.is_valid():
            form.save()
    purchase_form = PurchaseForm(initial={'item_code': i.code}, hide_price=i.fixed_price)
    return render_to_response('auction/item.html', {'item':i, 'purchase_form': purchase_form}, context_instance=RequestContext(request))

@login_required
def bidder(request, bidder_id):
    b = get_object_or_404(Bidder, id=bidder_id)
    if request.method == 'POST': 
        form = ItemForm(request.POST, instance=b)
        if form.is_valid():
            form.save()
    return render_to_response('auction/bidder.html', {'bidder':b}, context_instance=RequestContext(request))

@login_required
def new_item(request):
    if request.method == 'POST': 
        (i,created) = Item.objects.get_or_create(code=request.REQUEST['code'])
        form = ItemForm(request.POST, instance=i)
        if form.is_valid():
            form.save()
            return redirect(i) #TODO notify if already created?
    else:
        form = ItemForm()

    return render_to_response('auction/new_item.html', {'form':form}, context_instance=RequestContext(request))

@login_required
def new_bidder(request):
    if request.method == 'POST': 
        (b,created) = Bidder.objects.get_or_create(code=request.REQUEST['code'])
        form = BidderForm(request.POST, instance=b)
        if form.is_valid():
            form.save()
            return redirect(b)
    else:
        form = BidderForm()

    return render_to_response('auction/new_bidder.html', {'form':form}, context_instance=RequestContext(request))

@login_required
def purchase_item(request, item_id):
    if request.method == 'POST':
        item = get_object_or_404(Item, id=item_id)
        form = PurchaseForm(request.POST)
        if form.is_valid():
            bidder = form.cleaned_data['bidder']
            unit_price = item.unit_price if item.fixed_price else form.cleaned_data['unit_price']
            quantity = form.cleaned_data['quantity']
            if bidder and item and (quantity <= item.quantity_remaining() or item.quantity_remaining() == -1):
                p = Purchase(bidder=bidder, item=item, quantity=quantity, unit_price=unit_price)
                p.save()
                messages.info(request, "%s successfully purchased %s" % (bidder.name, item.name))
                return redirect(item)
        else:
            messages.error(request, "Invalid Form %s" % form.errors)
        messages.error(request, "Unable to complete purchase.")
        return redirect(item) #TODO go back to form with errors
    return redirect('/')

@login_required
def checkout(request, bidder_id):
    b = get_object_or_404(Bidder, id=bidder_id)
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            b.email = form.cleaned_data['email']
            b.save()
            for p in b.purchases.all():
                p.paid = True
                p.save()
            #TODO success message
            return redirect('/')
    else:
        form = CheckoutForm(initial={'email':b.email})
    return render_to_response('auction/checkout.html', {'bidder':b, 'form':form}, context_instance=RequestContext(request))

def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None
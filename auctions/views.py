from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from .models import User, AuctionListing, Bid


def index(request):
    listings = AuctionListing.objects.all()
    return render(request, "auctions/index.html", {
        "listings": listings
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == "GET":
        return render(request, "auctions/create_listing.html")

    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        starting_bid = request.POST["starting_bid"]
        image_url = request.POST["image_url"]
        category = request.POST["category"]

        if not title or not description or not starting_bid:
            return render(request, "auctions/create_listing.html", {
                "message": "all fields must be completed."
            })
        
        try:
            bid_value = Decimal(starting_bid)
        except InvalidOperation:
            return render(request, "auctions/create_listing.html", {
                "message": "Starting bid must be a valid number."
            })
        
        if bid_value <= 0:
            return render(request, "auctions/create_listing.html", {
                "message": "Starting bid must be a positive number."
            })
        
        currentUser = request.user

        listing = AuctionListing(
            title=title,
            description=description,
            starting_bid=bid_value,
            image_url=image_url,
            category=category,
            seller=currentUser
        )

        listing.save()

        return HttpResponseRedirect(reverse("index"))
    
   

def listing(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    is_seller = request.user == listing.seller 
    context = {
        "listing": listing,
        "is_seller": is_seller
    }

    if not listing.is_active:
        highest_bid = listing.bids.order_by('-bid_amount').first()
        final_price = highest_bid.bid_amount if highest_bid else listing.starting_bid
        context["final_price"] = final_price
        context["winner"] = listing.winner

    return render(request, "auctions/listing.html", context)



def place_bid(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(AuctionListing, pk=listing_id)
        bid_amount = request.POST.get("bid")

        if not bid_amount:
            messages.error(request, "Please enter a bid amount.")
            return render(request, "auctions/listing.html", {"listing": listing})

        try:
            bid_amount = Decimal(bid_amount)
        except InvalidOperation:
            messages.error(request, "Enter a valid number.")
            return render(request, "auctions/listing.html", {"listing": listing})

        
        minimum_valid_bid = listing.current_price if listing.current_price else listing.starting_bid

        if bid_amount <= minimum_valid_bid:
            messages.error(request, "Bid must be higher than the current price.")
            return render(request, "auctions/listing.html", {"listing": listing})

        
        bid = Bid(
            bid_amount=bid_amount,
            listing=listing,
            bidder=request.user
        )

        bid.save()

        listing.current_price = bid_amount
        listing.save()

        messages.success(request, "Your bid was sucessfully placed.")
        return redirect("listing", listing_id=listing.id)


def close_listing(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)

    is_seller = request.user == listing.seller

    if is_seller:
        listing.is_active = False
        listing.save()

        highest_bid = listing.bids.order_by('-bid_amount').first()
        if highest_bid:
            listing.winner = highest_bid.bidder
            listing.save()
            final_price = highest_bid.bid_amount
        else:
            final_price = listing.starting_bid

        messages.success(request, "The listing has been closed successfully.")
        return render(request, "auctions/listing.html", {
                "listing": listing,
                "is_seller": is_seller,
                "final_price": final_price,
                "winner": listing.winner
            })

    return redirect("listing", listing_id=listing_id)



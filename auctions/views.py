from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from .models import User, AuctionListing


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
        
        listing = AuctionListing(
            title=title,
            description=description,
            starting_bid=bid_value,
            image_url=image_url,
            category=category,
        )

        listing.save()

        return HttpResponseRedirect(reverse("index"))
    
   

def listing(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    return render(request, "auctions/listing.html", {
        "listing": listing
    })

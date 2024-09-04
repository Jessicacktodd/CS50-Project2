from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from .models import User, AuctionListing, Bid, Comments, Category


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


from django.shortcuts import render, redirect
from django.urls import reverse
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from .models import AuctionListing, Category

def create_listing(request):
    if request.method == "GET":
        # Fetch all categories to display in the dropdown
        categories = Category.objects.all()
        return render(request, "auctions/create_listing.html", {"categories": categories})

    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        starting_bid = request.POST.get("starting_bid")
        image_url = request.POST.get("image_url")
        category_name = request.POST.get("category_name")  # For existing category
        new_category_name = request.POST.get("new_category_name")  # For new category

        # Check for missing required fields
        if not title or not description or not starting_bid:
            categories = Category.objects.all()
            messages.error(request, "All fields must be completed.")
            return render(request, "auctions/create_listing.html", {"categories": categories})
        
        # Validate starting bid as a decimal number
        try:
            bid_value = Decimal(starting_bid)
        except InvalidOperation:
            categories = Category.objects.all()
            messages.error(request, "Starting bid must be a valid number.")
            return render(request, "auctions/create_listing.html", {"categories": categories})

        if bid_value <= 0:
            categories = Category.objects.all()
            messages.error(request, "Starting bid must be a positive number.")
            return render(request, "auctions/create_listing.html", {"categories": categories})
        
        currentUser = request.user

        # Determine the category to use or create a new one
        if new_category_name:
            # Create a new category if a new name is provided
            category_instance, created = Category.objects.get_or_create(category_name=new_category_name)
        elif category_name:
            # Use the existing category if selected
            try:
                category_instance = Category.objects.get(category_name=category_name)
            except Category.DoesNotExist:
                categories = Category.objects.all()
                messages.error(request, "Selected category does not exist.")
                return render(request, "auctions/create_listing.html", {"categories": categories})
        else:
            categories = Category.objects.all()
            messages.error(request, "Please select an existing category or enter a new one.")
            return render(request, "auctions/create_listing.html", {"categories": categories})

        # Create the new AuctionListing
        listing = AuctionListing(
            title=title,
            description=description,
            starting_bid=bid_value,
            image_url=image_url,
            category=category_instance,
            seller=currentUser
        )

        listing.save()

        # Redirect to the index page after saving the new listing
        return redirect(reverse("index"))

    
   

def listing(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    is_seller = request.user == listing.seller 
    in_watchlist = request.user in listing.watchlist.all()
    comments = listing.comments.all()  

    context = {
        "listing": listing,
        "is_seller": is_seller,
        "in_watchlist": in_watchlist,
        "comments": listing.comments.all() 
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


def comments(request, listing_id):
    if request.method == "POST":
        listing = get_object_or_404(AuctionListing, pk=listing_id)
        
        message = request.POST.get("newComment")
        if not message:
            messages.error(request, "Please enter comment")
            return render(request, "auctions/listing.html", {"listing": listing, "comments": listing.comments.all(), "is_seller": request.user == listing.seller})
        
        currentUser = request.user

        newComment = Comments(
            message=message,
            author=currentUser,
            listing=listing
        )

        newComment.save()

        messages.success(request, "Message sucessfully posted")
        return redirect("listing", listing_id=listing.id)
    
def display_watchlist(request):
    current_user = request.user
    listings = current_user.listing_watchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listings
    })

def remove_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    current_user = request.user
    listing.watchlist.remove(current_user)
    return HttpResponseRedirect(reverse("listing", args=(listing_id,)))


def add_to_watchlist(request, listing_id):
    listing = get_object_or_404(AuctionListing, pk=listing_id)
    current_user = request.user
    listing.watchlist.add(current_user)
    return HttpResponseRedirect(reverse("listing", args=(listing_id, )))


def categories(request):
    # Fetch all categories from the database
    all_categories = Category.objects.all()
    return render(request, "auctions/categories.html", {"categories": all_categories})

def category_listings(request, category_id):
    # Fetch the category by ID
    category = get_object_or_404(Category, pk=category_id)
    
    # Get all active listings under this category
    active_listings = AuctionListing.objects.filter(category=category, is_active=True)
    
    return render(request, "auctions/category_listings.html", {
        "category": category,
        "listings": active_listings
    })
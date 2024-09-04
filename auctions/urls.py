from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>/", views.listing, name="listing"),
    path("listing/<int:listing_id>/place_bid", views.place_bid, name="place_bid"),
    path("listing/<int:listing_id>/close", views.close_listing, name="close_listing"),
    path("listing/<int:listing_id>/comments", views.comments, name="comments"),
    path("remove_watchlist/<int:listing_id>", views.remove_watchlist, name="removeWatchlist"),
    path("add_to_watchlist/<int:listing_id>", views.add_to_watchlist, name="addWatchlist"),
    path("watchlist", views.display_watchlist, name="watchlist"),
     path("categories", views.categories, name="categories"), 
    path("categories/<int:category_id>/", views.category_listings, name="category_listings"),
]
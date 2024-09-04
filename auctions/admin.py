from django.contrib import admin

from django.contrib import admin
from .models import AuctionListing, Comments, Bid, Category


@admin.register(AuctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'starting_bid', 'current_price', 'is_active', 'category')  
    search_fields = ('title', 'seller__username', 'category__category_name') 
    list_filter = ('is_active', 'category', 'seller')
    ordering = ('-id',)
    readonly_fields = ('current_price',) 

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('message', 'author', 'listing') 
    search_fields = ('author__username', 'listing__title') 
    list_filter = ('author', 'listing') 
    ordering = ('-id',)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('bid_amount', 'bidder', 'listing')  
    search_fields = ('bidder__username', 'listing__title')  
    list_filter = ('bidder', 'listing') 
    ordering = ('-id',)  


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name',)
    search_fields = ('category_name',)
    ordering = ('category_name',)

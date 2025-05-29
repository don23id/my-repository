from django.contrib import admin
from .models import (
    Category, CollectibleItem, Comment, Vote, UserCollection,
    VisitCount, Poll, PollOption, PollVote
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0


@admin.register(CollectibleItem)
class CollectibleItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'country', 'condition', 'created_at')
    list_filter = ('category', 'country', 'condition', 'created_at')
    search_fields = ('name', 'description', 'country')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    inlines = [CommentInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('text', 'user__username', 'item__name')
    date_hierarchy = 'created_at'


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'value', 'created_at')
    list_filter = ('value', 'created_at')
    search_fields = ('user__username', 'item__name')


@admin.register(UserCollection)
class UserCollectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'item__name', 'notes')


@admin.register(VisitCount)
class VisitCountAdmin(admin.ModelAdmin):
    list_display = ('date', 'count')
    list_filter = ('date',)
    date_hierarchy = 'date'


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 3


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('question',)
    inlines = [PollOptionInline]


@admin.register(PollVote)
class PollVoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'poll', 'option', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'poll__question', 'option__text')
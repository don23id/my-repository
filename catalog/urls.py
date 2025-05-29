from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('item/<slug:slug>/', views.ItemDetailView.as_view(), name='item_detail'),
    path('item/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('item/<slug:slug>/vote/', views.vote_item, name='vote_item'),
    path('item/<slug:slug>/collection/', views.toggle_collection, name='toggle_collection'),
    path('collection/', views.user_collection, name='user_collection'),
    path('poll/<int:poll_id>/vote/', views.vote_poll, name='vote_poll'),
]
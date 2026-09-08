from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.blog_home, name='home'),
    path('search/', views.blog_search, name='search'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),
    path('post/<slug:slug>/', views.post_detail, name='post_detail'),
    path('post/<slug:slug>/comment/', views.add_comment, name='add_comment'),
    path('post/<slug:slug>/reply/<int:comment_id>/', views.add_reply, name='add_reply'),
]
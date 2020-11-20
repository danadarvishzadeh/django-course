from django.urls import path

from . import views

urlpatterns = [
    # products urls
    path('product/<int:pk>/', views.product_show, name='product_show'),
    path('product/<int:pk>/edit_inventory/', views.product_edit, name='product_edit'),
    path('product/insert/', views.product_insert, name='product_insert'),
    path('product/list/', views.product_show, name='product_show'),

    #accounts
    path('customer/<int:pk>/', views.customer_show, name='customer_show'),
    path('customer/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customer/register/', views.customer_register, name='customer_register'),
    path('customer/list/', views.customer_show, name='customer_show'),
    path('customer/profile/', views.customer_profile, name='customer_profile'),
    path('customer/login/', views.log_in, name='log_in'),
    path('customer/logout/', views.log_out, name='log_out'),


    #shopping
    path('shopping/cart/', views.cart_show, name='cart_show'),
    path('shopping/cart/add_items/', views.add_items, name='add_items'),
    path('shopping/cart/remove_items/', views.remove_items, name='remove_items'),
    path('shopping/submit/', views.submit, name='submit'),
]

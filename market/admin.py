import django
from django.contrib import admin
from .models import Order, Customer, OrderRow, Product
# Register your models here.

admin.site.register(Order)
admin.site.register(Customer)
admin.site.register(OrderRow)
admin.site.register(Product)
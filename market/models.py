from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.forms.formsets import ORDERING_FIELD_NAME
from collections import OrderedDict


class JsonManager(models.Manager):
    
    def list_result(self):
        return super().get_queryset()

    def product_search_result(self, keyword):
        return super().get_queryset().filter(name__icontains=keyword)
    
    def customer_search_result(self, keyword):
        return super().get_queryset().filter(
            Q(address__icontains=keyword) |
            Q(user__username__icontains=keyword) |
            Q(user__first_name__icontains=keyword) |
            Q(user__last_name__icontains=keyword)
        )
    
    def query_result(self, pk):
        return [super().get_queryset().get(pk=pk)]

    def cart_list(self, customer):
        open_order = super().get_queryset().filter(customer=customer).filter(status=1).first()
        if not open_order:
            open_order = Order.initiate(customer=customer)
        return open_order
    

class ProductJsonManager(JsonManager):
    
    @staticmethod
    def create_dict(data, query=False):
        information_list = []
        for product in data:
            if query:
                temp = OrderedDict()
            else:
                temp = dict()
            temp['id'] = product.id
            temp['code'] = product.code
            temp['name'] = product.name
            temp['price'] = product.price
            temp['inventory'] = product.inventory
            if query:
                return temp
            information_list.append(temp)
        result = {
            'products': information_list
            }
        return result

    def list_result(self):
        return ProductJsonManager.create_dict(super().list_result())

    def product_search_result(self, keyword):
        return ProductJsonManager.create_dict(super().product_search_result(keyword))
    
    def query_result(self, pk):
        return ProductJsonManager.create_dict(super().query_result(pk), query=True)


class CustomerJsonManager(JsonManager):

    @staticmethod
    def create_dict(data, search=True):
        information_list =[]
        for customer in data:
            temp = dict()
            temp['id'] = customer.id
            temp['username'] = customer.user.username
            temp['first_name'] = customer.user.first_name
            temp['last_name'] = customer.user.last_name
            temp['email'] = customer.user.email
            temp['phone'] = customer.phone
            temp['address'] = customer.address
            temp['balance'] = customer.balance
            information_list.append(temp)
        if search:
            result = {
                'customers': information_list
                }
            return result
        return information_list[0]

    def list_result(self):
        return CustomerJsonManager.create_dict(super().list_result())

    def customer_search_result(self, keyword):
        return CustomerJsonManager.create_dict(super().customer_search_result(keyword))
    
    def query_result(self, pk):
        return CustomerJsonManager.create_dict(super().query_result(pk), search=False)


class OrderJsonManager(JsonManager):
    
    @staticmethod
    def create_dict(data, total_price, errors=None, submit=None):
        information_list =[]
        result = dict()
        for row in data:
            temp = dict()
            temp['code'] = row.product.code
            temp['name'] = row.product.name
            temp['price'] = row.product.price
            temp['amount'] = row.amount
            information_list.append(temp)
        if submit:
            for key, value in submit.items():
                result[key] = value
        result['total_price'] = total_price
        if errors:
            result['errors'] = errors
        result['items'] = information_list
        return result

    def order_cart(self, pk, errors=None, submit=False):
        order = super().query_result(pk)[0]
        total_price = order.total_price
        if submit:
            submit = {
                'id': pk,
                'order_time': '{:%Y-%m-%d %H:%M:%S}'.format(order.order_time),
                'status': 'submitted',
            }
        return OrderJsonManager.create_dict(order.rows.all(), total_price, errors, submit)
        
    def customer_cart(self, customer):
        order = super().cart_list(customer=customer)
        total_price = order.total_price
        return OrderJsonManager.create_dict(order.rows.all(), total_price)


class Product(models.Model):
    code =  models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    inventory = models.IntegerField(default=0)

    objects = models.Manager()
    get_json = ProductJsonManager()

    def increase_inventory(self, amount):
        self.inventory += amount
        self.save()

    def decrease_inventory(self, amount):
        if self.inventory >= amount:
            self.inventory -= amount
            self.save()
        else:
            raise ValueError('inventory shortage.')
    

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    balance = models.IntegerField(default=20000)


    objects = models.Manager()
    get_json = CustomerJsonManager()


    def deposit(self, amount):
        self.balance += amount
        self.save()

    def spend(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
        else:
            raise ValueError('not enough money.')


class OrderRow(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    order = models.ForeignKey('Order',  related_name='rows', on_delete=models.CASCADE)
    amount = models.IntegerField()

    def increase_total_price_of_order(self, amount):
        total_price = self.product.price * amount
        self.order.total_price += total_price
        self.order.save()
    
    def decrease_total_price_of_order(self, amount):
        total_price = self.product.price * amount
        self.order.total_price -= total_price
        self.order.save()


class Order(models.Model):
    # Status values. DO NOT EDIT
    STATUS_SHOPPING = 1
    STATUS_SUBMITTED = 2
    STATUS_CANCELED = 3
    STATUS_SENT = 4
    
    status_choices = (
        (1, 'shopping'),
        (2, 'sibmited'),
        (3, 'canceled'),
        (4, 'sent'),
    )

    customer = models.ForeignKey('Customer', related_name='orders', on_delete=models.CASCADE)
    order_time = models.DateTimeField(auto_now_add=True)
    total_price = models.IntegerField(default=0)
    status = models.IntegerField(choices=status_choices)


    objects = models.Manager()
    get_json = OrderJsonManager()

    @staticmethod
    def initiate(customer):
        customer_orders = customer.orders.filter(status=1)
        if not customer_orders:
            order = Order.objects.create(customer=customer, status=1)
            return order
        else:
            raise ValueError('you have a pending order.')

    def add_product(self, product, amount):
        if self.status != 1:
            raise ValueError('this order is not open.')
        row = self.rows.filter(product=product).first()
        if amount == 0 or amount > product.inventory :
            raise ValueError('you can not add zero or more than our inventory.')
        if row:
            row.amount += amount
            if row.amount > product.inventory:
                raise ValueError('you can not buy more than our inventory.')
            row.save()
            row.increase_total_price_of_order(amount=amount)
        else:
            new_row = self.rows.create(product=product, amount=amount)
            new_row.increase_total_price_of_order(amount=amount)
        

    def remove_product(self, product, amount=None):
        row = self.rows.filter(product=product)
        if self.status != 1:
            raise ValueError('this order is not open.')
        if not row:
            raise ValueError('you can\'t remove a row that does not exists.')
        row = row.first()
        if amount is None:
            amount = row.amount
            row.decrease_total_price_of_order(amount=amount)
            row.delete()
        elif row.amount < amount:
            raise ValueError('you do not have this much items in your order row.')
        else:
            row.amount -= amount
            row.save()
            row.decrease_total_price_of_order(amount=amount)

    def submit(self):
        if self.status == 1:
            rows = self.rows.all()
            if not rows:
                raise ValueError('you can not submit empty orders.')
            customer = self.customer
            if self.total_price > customer.balance:
                raise ValueError('you can\'t submit an order with higher price than your balance.')
            for row in rows:
                amount = row.amount
                product = row.product
                product.decrease_inventory(amount)
            customer.spend(self.total_price)
            self.status = 2
            self.save()
        else:
            raise ValueError('you do not have an open order.')

    def cancel(self):
        if self.status == 2:
            rows = self.rows.all()
            customer = self.customer
            for row in rows:
                amount = row.amount
                product = row.product
                product.increase_inventory(amount)
            customer.deposit(self.total_price)
            self.status = 3
            self.save()
        else:
            raise ValueError('you do not have a submited order.')

    def send(self):
        if self.status == 2:
            self.status = 4
            self.save()
        else:
            raise ValueError('you do not have a submited order.')
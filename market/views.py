import json

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import ObjectDoesNotExist
from django.http import JsonResponse

from .forms import CustomerForm, UserForm, Useredit, CustomerEdit
from .models import Customer, Order, OrderRow, Product


"""
    You can define utility functions here if needed
    For example, a function to create a JsonResponse
    with a specified status code or a message, etc.

    DO NOT FORGET to complete url patterns in market/urls.py
"""


def product_insert(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            code = data['code']
            name = data['name']
            price = data['price']
            inventory = data.get('inventory', 0)
            if inventory == '':
                inventory = 0
            new_product = Product.objects.create(code=code, name=name, price=price, inventory=inventory)
            return JsonResponse({'id': new_product.id}, status=201)
        except Exception as error:
            return JsonResponse({"message": 'product was not created, {}'.format(error.args)}, status=400)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def product_show(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                return JsonResponse(Product.get_json.query_result(pk=pk), status=200)
            except ObjectDoesNotExist:
                return JsonResponse({"message": "Product Not Found."}, status=404)
        elif request.GET:
            try:
                keyword = request.GET['search']
                return JsonResponse(Product.get_json.product_search_result(keyword=keyword), status=200)
            except:
                return JsonResponse({"message": "Product Not Found."}, status=404)
        else:
            return JsonResponse(Product.get_json.list_result(), status=200)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def product_edit(request, pk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            product = Product.objects.get(pk=pk)
            if 'amount' in data.keys():
                amount = int(data['amount'])
            else:
                return JsonResponse({"message": "bad request data."}, status=400)
            if amount < 0:
                product.decrease_inventory(amount=abs(amount))
            else:
                product.increase_inventory(amount=amount)
            return JsonResponse(Product.get_json.query_result(pk=pk), status=200)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Product Not Found."}, status=404)
        except ValueError:
            return JsonResponse({"message": "inventory shortage."}, status=400)

    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def customer_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            user = UserForm(data=data)
            customer = CustomerForm(data=data)
            if user.is_valid() and customer.is_valid():
                user = user.save()
                customer = customer.save(commit=False)
                customer.user = user
                customer.save()
                return JsonResponse({"id": customer.id}, status=201)
            else:
                return JsonResponse({"message": 'failed because of {} and {}.'.format(user.errors, customer.errors)}, status=400)
        except Exception as err:
            return JsonResponse({"message": err}, status=400)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def customer_show(request, pk=None):
    if request.method == 'GET':
        if pk:
            try:
                return JsonResponse(Customer.get_json.query_result(pk=pk), status=200)
            except ObjectDoesNotExist:
                return JsonResponse({"message": "Customer Not Found."}, status=404)
        elif request.GET:
            try:
                keyword = request.GET['search']
                return JsonResponse(Customer.get_json.customer_search_result(keyword=keyword), status=200)
            except:
                return JsonResponse({"message": "Customer Not Found."}, status=404)
        else:
            return JsonResponse(Customer.get_json.list_result(), status=200)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def get_fields(data, user=None, customer=None):
    if user:
        data['email'] = data.get('email', user.email)
        data['first_name'] = data.get('first_name', user.first_name)
        data['last_name'] = data.get('last_name', user.last_name)
    if customer:
        data['address'] = data.get('address', customer.address)
        data['phone'] = data.get('phone', customer.phone)
        data['balance'] = int(data.get('balance', customer.balance))

    return data


def customer_edit(request, pk):
    if request.method == 'POST':
        data = json.loads(request.body.decode("utf-8"))
        fields = data.keys()
        if 'username' in fields or 'password' in fields or 'id' in fields:
            return JsonResponse({"message": "Cannot edit customer's identity and credentials."}, status=403)
        try:
            customer = Customer.objects.get(pk=pk)
            user = customer.user
            data = get_fields(user=user, customer=customer, data=data)
            form_u = Useredit(data, instance=user)
            form_c = CustomerEdit(data, instance=customer)
        except ObjectDoesNotExist:
            return JsonResponse({"message": "Customer Not Found."}, status=404)
        if form_u.is_valid() and form_c.is_valid():
            form_u.save()
            form_c.save()
        else:
            return JsonResponse({"message": "validation error."}, status=400)
        return JsonResponse(Customer.get_json.query_result(pk=pk), status=200)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def log_in(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode("utf-8"))
            username = data['username']
            password = data['password']
            user = authenticate(request=request, username=username, password=password)
            if user.is_authenticated:
                login(request=request, user=user)
                return JsonResponse({"message": "You are logged in successfully."}, status=200)
        except:
            return JsonResponse({"message": "bad data."}, status=404)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def log_out(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request=request)
            return JsonResponse({"message": "You are logged out successfully."}, status=200)
        else:
            return JsonResponse({"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def customer_profile(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            pk = Customer.objects.get(user=request.user).id
            return JsonResponse(Customer.get_json.query_result(pk=pk), status=200)
        else:
            return JsonResponse({"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def cart_show(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            customer = Customer.objects.get(user=request.user)
            return JsonResponse(Order.get_json.customer_cart(customer=customer), status=200)
        else:
            return JsonResponse({"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def get_or_create_order(user):
    customer = Customer.objects.get(user=user)
    try:
        return customer.orders.get(status=1)
    except:
        return Order.initiate(customer=customer)


def add_items(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            order = get_or_create_order(user=request.user)
            data = json.loads(request.body.decode("utf-8"))
            errors = []
            for item in data:
                try:
                    code = item['code']
                    amount = int(item['amount'])
                    product = Product.objects.get(code=code)
                    order.add_product(product=product, amount=amount)
                except Exception as error:
                    errors.append({'code': code, 'message': error.args[0]})
            if errors:
                status = 400
            else:
                status = 200
            return JsonResponse(Order.get_json.order_cart(pk=order.id, errors=errors), status=status)
        else:
            return JsonResponse({"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def remove_items(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            order = get_or_create_order(user=request.user)
            data = json.loads(request.body.decode("utf-8"))
            errors = []
            for item in data:
                try:
                    code = item['code']
                    amount = item.get('amount')
                    if amount != None:
                        amount = int(amount)
                    product = Product.objects.get(code=code)
                    order.remove_product(product=product, amount=amount)
                except Exception as error:
                    errors.append({'code': code, 'message': error.args[0]})
            if errors:
                status = 400
            else:
                status = 200
            return JsonResponse(Order.get_json.order_cart(pk=order.id, errors=errors), status=status)
        else:
            return JsonResponse({"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)


def submit(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            order = get_or_create_order(user=request.user)
            try:
                order.submit()
            except:
                return JsonResponse({"message": "an error occured."}, status=400)
            return JsonResponse(Order.get_json.order_cart(pk=order.id, submit=True), status=200)
        else:
            return JsonResponse({"message": "You are not logged in."}, status=403)
    else:
        return JsonResponse({"message": "wrong request method."}, status=400)

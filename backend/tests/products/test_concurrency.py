import threading
import pytest
from decimal import Decimal
from ninja.errors import HttpError

from apps.authentication.models import User
from apps.products.models import Category, Product, Inventory
from apps.products.services import InventoryService


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email='admin@test.com',
        password='testpass123',
        full_name='Admin Test',
        role=User.Role.ADMIN,
    )


@pytest.fixture
def product_with_stock(db):
    category = Category.objects.create(name='Bebidas')
    product = Product.objects.create(
        category=category,
        name='Coca Cola 500ml',
        sku='CC-500',
        price=Decimal('3.50'),
    )
    Inventory.objects.create(product=product, quantity=1)
    return product


@pytest.mark.django_db(transaction=True)
def test_concurrent_stock_deduction_prevents_negative_stock(product_with_stock, admin_user):
    """
    Two threads attempt to sell the last unit simultaneously.
    SELECT FOR UPDATE ensures only one succeeds — stock never goes negative.
    """
    results = []

    def attempt_sale():
        try:
            InventoryService.adjust_stock(
                product_id=product_with_stock.id,
                quantity_delta=-1,
                reason='Sale',
                created_by=admin_user,
            )
            results.append('success')
        except HttpError as e:
            results.append(f'error:{e.status_code}')

    t1 = threading.Thread(target=attempt_sale)
    t2 = threading.Thread(target=attempt_sale)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    product_with_stock.inventory.refresh_from_db()

    assert product_with_stock.inventory.quantity >= 0, 'Stock went negative — race condition!'
    assert results.count('success') == 1, 'Exactly one sale should succeed'
    assert results.count('error:400') == 1, 'One sale should fail with insufficient stock'


@pytest.mark.django_db(transaction=True)
def test_sequential_stock_deductions_are_consistent(product_with_stock, admin_user):
    """
    Sequential deductions should always be consistent.
    """
    product_with_stock.inventory.quantity = 10
    product_with_stock.inventory.save()

    for _ in range(10):
        InventoryService.adjust_stock(
            product_id=product_with_stock.id,
            quantity_delta=-1,
            reason='Sale',
            created_by=admin_user,
        )

    product_with_stock.inventory.refresh_from_db()
    assert product_with_stock.inventory.quantity == 0

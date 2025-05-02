import graphene
from graphene_django.types import DjangoObjectType
from .models import Product, Customer, Sale
from django.db.models import Sum
from datetime import datetime
from django.db.models.functions import TruncMonth



class ProductType(DjangoObjectType):
    class Meta:
        model = Product

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class SaleType(DjangoObjectType):
    class Meta:
        model = Sale


class SaleByProductType(graphene.ObjectType):
    product = graphene.String()
    total_quantity = graphene.Int()

class SaleByProductSummaryType(graphene.ObjectType):
    product_name = graphene.String()
    total_quantity = graphene.Int()
    price = graphene.Float()
    total_sales_value = graphene.Float()

class SaleByMonthType(graphene.ObjectType):
    month = graphene.String()
    total_sales = graphene.Int()

class Query(graphene.ObjectType):
    all_sales = graphene.List(SaleType)
    sales_by_product = graphene.List(SaleByProductType)
    sales_by_product_summary = graphene.List(SaleByProductSummaryType)
    sales_by_month = graphene.List(SaleByMonthType)
    top_customer = graphene.Field(CustomerType)

    def resolve_all_sales(self, info):
        return Sale.objects.select_related('product', 'customer').all()

    def resolve_sales_by_product(self, info):
        return (
            Sale.objects
            .values('product__name')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('-total_quantity')
        )

    def resolve_sales_by_product_summary(self, info):
        queryset = (
            Sale.objects
            .values('product__id')
            .annotate(total_quantity=Sum('quantity'))
        )

        results = []
        for item in queryset:
            product = Product.objects.get(id=item['product__id'])
            total_quantity = item['total_quantity']
            price = float(product.price)
            total_sales_value = total_quantity * price

            results.append({
                'product_name': product.name,
                'total_quantity': total_quantity,
                'price': price,
                'total_sales_value': total_sales_value,
            })

        return results

    def resolve_sales_by_month(self, info):
        queryset = (
            Sale.objects
            .annotate(month=TruncMonth('date'))
            .values('month')
            .annotate(total_sales=Sum('quantity'))
            .order_by('month')
        )

        return [
            {
                'month': item['month'].strftime('%Y-%m'),
                'total_sales': item['total_sales']
            }
            for item in queryset
        ]

    def resolve_top_customer(self, info):
        top = (
            Sale.objects
            .values('customer')
            .annotate(total_purchases=Sum('quantity'))
            .order_by('-total_purchases')
            .first()
        )
        if top:
            return Customer.objects.get(id=top['customer'])
        return None

schema = graphene.Schema(query=Query)

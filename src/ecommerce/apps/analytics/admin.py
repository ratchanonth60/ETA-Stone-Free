from django.contrib import admin
from oscar.core.loading import get_model


class ProductRecordAdmin(admin.ModelAdmin):
    list_display = ('product', 'num_views', 'num_basket_additions',
                    'num_purchases')


class UserProductViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'date_created')


class UserRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'num_product_views', 'num_basket_additions',
                    'num_orders', 'total_spent', 'date_last_order')


admin.site.register(get_model('analytics', 'ProductRecord'),
                    ProductRecordAdmin)
admin.site.register(get_model('analytics', 'UserRecord'), UserRecordAdmin)
admin.site.register(get_model('analytics', 'UserSearch'))
admin.site.register(get_model('analytics', 'UserProductView'),
                    UserProductViewAdmin)

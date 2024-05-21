from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Basket, BasketItem, Order, OrderItem, UserProfile, Message


class ProductAdminForm(forms.ModelForm):
    description = forms.CharField(widget=forms.TextInput)
    description2 = forms.CharField(widget=forms.TextInput)

    class Meta:
        model = Product
        fields = '__all__'


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = [
        'title',
        'category',
        'image',
        'description',
        'price',
        'short_description2',
        'image2',
        'image3',
        'image4']

    def short_description(self, obj):
        return obj.description[:50]
    short_description.short_description = 'Description'

    def short_description2(self, obj):
        return obj.description2[:50]  
    short_description2.short_description = 'Description 2'  


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'payment_type',
        'total_cost',
        'created_at',
        'updated_at')
    inlines = [OrderItemInline]


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'UserProfile'


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Order, OrderAdmin)  
admin.site.register(Message)
admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.site_header = 'Sales Administration'
admin.site.site_title = 'Admin Operations'

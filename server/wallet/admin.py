from django.contrib import admin

from .models import BudgetCategory, MonthlyIncome, OwnedCard, OwnedCardCreditUse, SpendLogEntry


@admin.register(OwnedCard)
class OwnedCardAdmin(admin.ModelAdmin):
    list_display = ("user", "card", "added_at")
    search_fields = ("user__email", "card__name", "card__local_slug")


@admin.register(OwnedCardCreditUse)
class OwnedCardCreditUseAdmin(admin.ModelAdmin):
    list_display = ("owned_card", "statement_credit", "created_at")
    search_fields = ("owned_card__user__email", "statement_credit__name")


@admin.register(MonthlyIncome)
class MonthlyIncomeAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "updated_at")
    search_fields = ("user__email",)


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "key", "allocated", "created_at")
    search_fields = ("user__email", "label", "key")


@admin.register(SpendLogEntry)
class SpendLogEntryAdmin(admin.ModelAdmin):
    list_display = ("user", "merchant", "category", "amount", "date")
    search_fields = ("user__email", "merchant", "category")

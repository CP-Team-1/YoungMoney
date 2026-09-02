from django.db import models


class RewardCategory(models.Model):
    
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    category = models.CharField(
        max_length = 255,
    )
    
    def __str__(self):
        return f"{self.category}"


class Incentive(models.Model):
    
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    incentive = models.CharField(
        max_length = 255,
    )
    value = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
    )
    frequency = models.CharField(
        max_length = 255
    )
    description = models.TextField(
    )
    
    def __str__(self):
        return f"{self.incentive} - {self.description}"


class Perk(models.Model):
    
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    perk = models.CharField(
        max_length = 255,
    )
    value = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
    )
    frequency = models.CharField(
        max_length = 255,
    )
    description = models.TextField(
    )
    
    def __str__(self):
        return f"{self.perk} - {self.description}"


class CreditCard(models.Model):
        
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    ##category
    name = models.CharField(
        max_length = 255,
    )
    issuer = models.CharField(
        max_length = 255,
    )
    network = models.CharField(
        max_length = 255,
    )
    annual_fee = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
    )
    foreign_transaction_fee = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
    )
    credit_score_min = models.PositiveSmallIntegerField(
        blank = True,
        null = True, 
    )
    
    def __str__(self):
        return f"{self.name} - {self.issuer} - {self.network}"
    
    
class CCRewardRate(models.Model):
    
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    credit_card = models.ForeignKey(
        CreditCard,
        related_name = 'reward_rates',
        on_delete = models.CASCADE,
    )
    category = models.ForeignKey(
        RewardCategory,
        related_name = 'reward_rates',
        on_delete = models.PROTECT,
    )
    rate = models.DecimalField(
        max_digits = 10,
        decimal_places = 2,
    )
    
    def __str__(self):
        return f"{self.credit_card.name} - {self.category.category} {self.rate}"
    
    
class CCIncentive(models.Model):
    
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    credit_card = models.ForeignKey(
        CreditCard,
        related_name = 'incentives',
        on_delete = models.CASCADE,
    )
    incentive = models.ForeignKey(
        Incentive,
        related_name = 'credit_cards',
        on_delete = models.PROTECT,
    )

    def __str__(self):
        return f"{self.credit_card.name} - {self.incentive.incentive}"
        
    
class CCPerk(models.Model):
    
    created_date = models.DateTimeField(
        auto_now_add = True,
    )
    modified_date = models.DateTimeField(
        auto_now = True,
    )
    credit_card = models.ForeignKey(
        CreditCard,
        related_name = 'perks',
        on_delete = models.CASCADE,
    )
    perk = models.ForeignKey(
        Perk,
        related_name = 'credit_cards',
        on_delete = models.PROTECT,
    )
    
    def __str__(self):
        return f"{self.credit_card.name} - {self.perk.perk}"
from django.contrib import admin

from .models import (
    CCRewardRate,
    CardRewardProgram,
    CreditCard,
    Issuer,
    Perk,
    RewardCategory,
    RewardCategoryAlias,
    RewardProgram,
    RewardProgramUnlock,
    RewardTransferRoute,
    SignupBonus,
    StatementCredit,
)


admin.site.register(
    (
        Issuer,
        CreditCard,
        RewardCategory,
        RewardCategoryAlias,
        CCRewardRate,
        CardRewardProgram,
        RewardProgram,
        RewardProgramUnlock,
        RewardTransferRoute,
        SignupBonus,
        StatementCredit,
        Perk,
    )
)

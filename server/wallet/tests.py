from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.db.utils import IntegrityError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cardapi.models import CreditCard, Issuer, StatementCredit

from .models import OwnedCard, OwnedCardCreditUse


User = get_user_model()


def _make_card(slug, name="Test Card", issuer_slug=None, is_active_issuer=True, annual_fee=None):
    issuer = Issuer.objects.create(
        slug=issuer_slug or f"{slug}-issuer",
        name="Test Issuer",
        is_active=is_active_issuer,
    )
    return CreditCard.objects.create(
        local_slug=slug, name=name, issuer=issuer, annual_fee=annual_fee
    )


class OwnedCardModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="strong-pass-123")
        self.card = _make_card("test-card")

    def test_id_is_uuid(self):
        owned = OwnedCard.objects.create(user=self.user, card=self.card)
        self.assertEqual(owned.id.version, 4)

    def test_same_card_cannot_be_owned_twice_by_same_user(self):
        OwnedCard.objects.create(user=self.user, card=self.card)
        with self.assertRaises(IntegrityError):
            OwnedCard.objects.create(user=self.user, card=self.card)

    def test_card_is_protected_and_user_delete_cascades(self):
        OwnedCard.objects.create(user=self.user, card=self.card)

        with self.assertRaises(ProtectedError):
            self.card.delete()

        self.user.delete()
        self.assertFalse(OwnedCard.objects.exists())


class OwnedCardApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="strong-pass-123")
        self.other_user = User.objects.create_user(email="other@example.com", password="strong-pass-123")
        self.card = _make_card("owned-card-1")
        self.other_card = _make_card("owned-card-2")
        self.list_url = reverse("owned-card-list")
        self.client.force_authenticate(self.user)

    def test_add_card_creates_ownership(self):
        response = self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["card_slug"], self.card.local_slug)
        self.assertEqual(response.data["card_name"], self.card.name)
        self.assertTrue(OwnedCard.objects.filter(user=self.user, card=self.card).exists())

    def test_adding_an_already_owned_card_is_idempotent(self):
        first = self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")
        second = self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(OwnedCard.objects.filter(user=self.user, card=self.card).count(), 1)

    def test_rejects_unknown_card_slug(self):
        response = self.client.post(self.list_url, {"card_slug": "does-not-exist"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("card_slug", response.data)

    def test_rejects_card_from_inactive_issuer(self):
        inactive_card = _make_card("inactive-issuer-card", is_active_issuer=False)

        response = self.client.post(self.list_url, {"card_slug": inactive_card.local_slug}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_card(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")
        detail_url = reverse("owned-card-detail", kwargs={"card_slug": self.card.local_slug})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(OwnedCard.objects.filter(user=self.user, card=self.card).exists())

    def test_list_and_delete_are_scoped_to_authenticated_user(self):
        OwnedCard.objects.create(user=self.user, card=self.card)
        OwnedCard.objects.create(user=self.other_user, card=self.other_card)

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["card_slug"] for item in response.data], [self.card.local_slug])

        other_detail_url = reverse("owned-card-detail", kwargs={"card_slug": self.other_card.local_slug})
        self.assertEqual(self.client.delete(other_detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)

        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class EffectiveAnnualFeeApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="strong-pass-123")
        self.other_user = User.objects.create_user(email="other@example.com", password="strong-pass-123")
        self.card = _make_card("fee-card", annual_fee=Decimal("95"))
        self.credit = StatementCredit.objects.create(
            credit_card=self.card,
            name="Travel Credit",
            amount=Decimal("100"),
            period=StatementCredit.Period.ANNUAL,
            source_key="fee-card-credit",
        )
        self.inactive_credit = StatementCredit.objects.create(
            credit_card=self.card,
            name="Retired Credit",
            amount=Decimal("50"),
            period=StatementCredit.Period.ANNUAL,
            source_key="fee-card-retired-credit",
            is_active=False,
        )
        self.list_url = reverse("owned-card-list")
        self.credit_use_list_url = reverse("credit-use-list")
        self.client.force_authenticate(self.user)

    def test_adding_card_defaults_all_active_credits_to_used(self):
        response = self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["used_credit_ids"], [self.credit.pk])
        # annual_fee=95, one $100/yr credit fully used → net rebate of $5/yr.
        self.assertEqual(Decimal(str(response.data["effective_annual_fee"])), Decimal("-5"))

    def test_toggling_credit_off_recomputes_effective_fee(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")
        owned = OwnedCard.objects.get(user=self.user, card=self.card)
        detail_url = reverse("credit-use-detail", kwargs={"statement_credit_id": self.credit.pk})

        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            OwnedCardCreditUse.objects.filter(owned_card=owned, statement_credit=self.credit).exists()
        )
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.data[0]["used_credit_ids"], [])
        self.assertEqual(Decimal(str(list_response.data[0]["effective_annual_fee"])), Decimal("95"))

    def test_toggling_credit_back_on(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")
        detail_url = reverse("credit-use-detail", kwargs={"statement_credit_id": self.credit.pk})
        self.client.delete(detail_url)

        response = self.client.post(
            self.credit_use_list_url,
            {"card_slug": self.card.local_slug, "statement_credit_id": self.credit.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        list_response = self.client.get(self.list_url)
        self.assertEqual(list_response.data[0]["used_credit_ids"], [self.credit.pk])

    def test_toggle_on_is_idempotent(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")

        response = self.client.post(
            self.credit_use_list_url,
            {"card_slug": self.card.local_slug, "statement_credit_id": self.credit.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        owned = OwnedCard.objects.get(user=self.user, card=self.card)
        self.assertEqual(
            OwnedCardCreditUse.objects.filter(owned_card=owned, statement_credit=self.credit).count(), 1
        )

    def test_toggle_off_is_idempotent(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")
        detail_url = reverse("credit-use-detail", kwargs={"statement_credit_id": self.credit.pk})

        first = self.client.delete(detail_url)
        second = self.client.delete(detail_url)

        self.assertEqual(first.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(second.status_code, status.HTTP_204_NO_CONTENT)

    def test_cannot_toggle_credit_for_unowned_card(self):
        response = self.client.post(
            self.credit_use_list_url,
            {"card_slug": self.card.local_slug, "statement_credit_id": self.credit.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_toggle_inactive_credit(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")

        response = self.client.post(
            self.credit_use_list_url,
            {"card_slug": self.card.local_slug, "statement_credit_id": self.inactive_credit.pk},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_toggle_another_users_credit_use(self):
        self.client.post(self.list_url, {"card_slug": self.card.local_slug}, format="json")
        self.client.force_authenticate(self.other_user)

        detail_url = reverse("credit-use-detail", kwargs={"statement_credit_id": self.credit.pk})
        response = self.client.delete(detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        owned = OwnedCard.objects.get(user=self.user, card=self.card)
        self.assertTrue(
            OwnedCardCreditUse.objects.filter(owned_card=owned, statement_credit=self.credit).exists()
        )

    def test_effective_annual_fee_is_null_when_annual_fee_unknown(self):
        no_fee_card = _make_card("no-fee-card")
        self.client.post(self.list_url, {"card_slug": no_fee_card.local_slug}, format="json")

        response = self.client.get(self.list_url)

        owned_no_fee = next(row for row in response.data if row["card_slug"] == no_fee_card.local_slug)
        self.assertIsNone(owned_no_fee["effective_annual_fee"])

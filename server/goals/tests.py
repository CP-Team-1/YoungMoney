from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Goal, UserGoal


User = get_user_model()


class UserGoalModelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="strong-pass-123")
        self.goal_type = Goal.objects.get(goal="Savings")

    def test_notes_are_optional_and_id_is_uuid(self):
        user_goal = UserGoal.objects.create(
            user=self.user,
            goal=self.goal_type,
            name="Emergency fund",
            target=Decimal("5000.00"),
        )

        self.assertEqual(user_goal.notes, "")
        self.assertEqual(user_goal.id.version, 4)

    def test_target_must_be_positive_when_validated(self):
        user_goal = UserGoal(
            user=self.user,
            goal=self.goal_type,
            name="Emergency fund",
            target=Decimal("0.00"),
        )

        with self.assertRaises(ValidationError):
            user_goal.full_clean()

    def test_goal_type_is_protected_and_user_delete_cascades(self):
        UserGoal.objects.create(
            user=self.user,
            goal=self.goal_type,
            name="Emergency fund",
            target=Decimal("5000.00"),
        )

        with self.assertRaises(ProtectedError):
            self.goal_type.delete()

        self.user.delete()
        self.assertFalse(UserGoal.objects.exists())


class UserGoalApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="owner@example.com", password="strong-pass-123")
        self.other_user = User.objects.create_user(email="other@example.com", password="strong-pass-123")
        self.goal_type = Goal.objects.get(goal="Purchase")
        self.list_url = reverse("user-goal-list")
        self.client.force_authenticate(self.user)

    def test_seeded_goal_types_are_available(self):
        response = self.client.get(reverse("goal-type-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["goal"] for item in response.data],
            ["Debt free", "Purchase", "Savings"],
        )

    def test_create_goal_with_omitted_notes(self):
        response = self.client.post(
            self.list_url,
            {"goal": self.goal_type.id, "name": "  First car  ", "target": "12000.00"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = UserGoal.objects.get(id=response.data["id"])
        self.assertEqual(created.user, self.user)
        self.assertEqual(created.name, "First car")
        self.assertEqual(created.notes, "")

    def test_rejects_blank_name_and_non_positive_target(self):
        response = self.client.post(
            self.list_url,
            {"goal": self.goal_type.id, "name": "   ", "target": "0.00", "notes": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)
        self.assertIn("target", response.data)

    def test_list_and_detail_are_scoped_to_authenticated_user(self):
        own_goal = UserGoal.objects.create(
            user=self.user, goal=self.goal_type, name="Own goal", target="100.00"
        )
        other_goal = UserGoal.objects.create(
            user=self.other_user, goal=self.goal_type, name="Private goal", target="200.00"
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.data], [str(own_goal.id)])

        detail_url = reverse("user-goal-detail", kwargs={"pk": other_goal.id})
        self.assertEqual(self.client.get(detail_url).status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            self.client.patch(detail_url, {"name": "Changed"}, format="json").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, status.HTTP_404_NOT_FOUND)

    def test_authentication_is_required(self):
        self.client.force_authenticate(user=None)

        self.assertEqual(self.client.get(self.list_url).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            self.client.get(reverse("goal-type-list")).status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

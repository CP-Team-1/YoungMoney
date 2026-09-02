from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CardAdviceRequestSerializer
from .services import GeminiError, get_card_advice


class CardAdviceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "advisor-suggest"

    def post(self, request):
        serializer = CardAdviceRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            suggestion = get_card_advice(**serializer.validated_data)
        except GeminiError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY
            )

        return Response({"suggestion": suggestion})

import jwt
import datetime
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Deck, Card, MatchResult, UserLogin
from .serializers import (
    CreateUserSerializer,
    CreateUserDeckSerializer,
    AddMatchResultSerializer,
    DeckArchetypeSerializer,
    DeckSerializer,
    DeckListSerializer,
    CardSerializer,
    MatchResultSerializer,
)


class LoginView(APIView):
    authentication_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserLogin.objects.get(email=email)
        except UserLogin.DoesNotExist:
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        payload = {
            "user_id": user.id,
            "email": user.email,
            "is_admin": user.is_admin,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
        return Response({"token": token}, status=status.HTTP_200_OK)


class CreateUserView(APIView):
    authentication_classes = []

    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"id": user.id, "email": user.email, "name": user.name}, status=status.HTTP_201_CREATED)


class AddMatchResultView(APIView):
    def post(self, request):
        serializer = AddMatchResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CreateUserDeckView(APIView):
    def post(self, request):
        serializer = CreateUserDeckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AddDeckArchetypeView(APIView):
    def post(self, request):
        serializer = DeckArchetypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DeckViewSet(viewsets.ModelViewSet):
    queryset = Deck.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return DeckListSerializer
        return DeckSerializer

    @action(detail=True, methods=["get"])
    def stats(self, request, pk=None):
        deck = self.get_object()
        results = deck.match_results.all()
        total = results.count()
        wins = results.filter(outcome=MatchResult.Outcome.WIN).count()
        losses = results.filter(outcome=MatchResult.Outcome.LOSS).count()
        draws = results.filter(outcome=MatchResult.Outcome.DRAW).count()
        return Response({
            "total": total,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_rate": round(wins / total * 100, 1) if total else 0,
        })


class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer

    def get_queryset(self):
        return Card.objects.filter(deck_id=self.kwargs["deck_pk"])

    def perform_create(self, serializer):
        serializer.save(deck_id=self.kwargs["deck_pk"])


class MatchResultViewSet(viewsets.ModelViewSet):
    serializer_class = MatchResultSerializer

    def get_queryset(self):
        return MatchResult.objects.filter(deck_id=self.kwargs["deck_pk"]).order_by("-played_at")

    def perform_create(self, serializer):
        serializer.save(deck_id=self.kwargs["deck_pk"])

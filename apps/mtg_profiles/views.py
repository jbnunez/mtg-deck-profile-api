import jwt
import datetime
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Deck, Card, MatchResult, UserLogin, ProfileField, Format, UserDeck, DeckArchetype
from .serializers import (
    CreateUserSerializer,
    CreateUserDeckSerializer,
    UserDeckSerializer,
    AddMatchResultSerializer,
    FormatSerializer,
    DeckArchetypeSerializer,
    DeckSerializer,
    DeckListSerializer,
    CardSerializer,
    MatchResultSerializer,
    UserProfileSerializer,
    UpdateProfileSerializer,
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
            "name": user.name,
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
        payload = {
            "user_id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=settings.JWT_EXPIRATION_HOURS),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm="HS256")
        return Response({"id": user.id, "email": user.email, "name": user.name, "token": token}, status=status.HTTP_201_CREATED)


class UpdateProfileView(APIView):
    def post(self, request):
        serializer = UpdateProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id = request.user["user_id"]
        field_name = serializer.validated_data["field_name"]
        field_value = serializer.validated_data["field_value"]
        ProfileField.objects.update_or_create(
            user_id=user_id,
            field_name=field_name,
            defaults={"field_value": field_value},
        )
        return Response({"field_name": field_name, "field_value": field_value}, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    def get(self, request, user_id):
        try:
            user = UserLogin.objects.prefetch_related("profile_fields").get(id=user_id)
        except UserLogin.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class AddMatchResultView(APIView):
    def post(self, request):
        serializer = AddMatchResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserDeckListView(APIView):
    def get(self, request, user_id):
        queryset = UserDeck.objects.select_related("archetype").filter(user_id=user_id).order_by("-last_played")

        format_filter = request.query_params.get("format-name")
        if format_filter:
            queryset = queryset.filter(archetype__format=format_filter)

        try:
            limit = min(int(request.query_params.get("limit", 20)), 100)
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            return Response({"error": "limit and page must be integers."}, status=status.HTTP_400_BAD_REQUEST)

        offset = (page - 1) * limit
        total = queryset.count()
        results = queryset[offset:offset + limit]

        serializer = UserDeckSerializer(results, many=True)
        return Response({
            "total": total,
            "page": page,
            "limit": limit,
            "results": serializer.data,
        })


class CreateUserDeckView(APIView):
    def post(self, request):
        serializer = CreateUserDeckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FormatListView(APIView):
    def get(self, request):
        formats = Format.objects.all().order_by("name")
        serializer = FormatSerializer(formats, many=True)
        return Response(serializer.data)


class AddFormatView(APIView):
    def post(self, request):
        if not request.user.get("is_admin"):
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = FormatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DeckArchetypeListView(APIView):
    def get(self, request):
        queryset = DeckArchetype.objects.filter(active=True).order_by("name")
        format_filter = request.query_params.get("format-name")
        if format_filter:
            queryset = queryset.filter(format=format_filter)
        serializer = DeckArchetypeSerializer(queryset, many=True)
        return Response(serializer.data)


class AddDeckArchetypeView(APIView):
    def post(self, request):
        if not request.user.get("is_admin"):
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
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

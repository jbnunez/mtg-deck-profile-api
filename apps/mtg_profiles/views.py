import jwt
import datetime
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.db.models import F
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Deck, Card, MatchResult, UserLogin, ProfileField, Format, UserDeck, DeckArchetype, PlayerMatch, ApprovedBetaEmail
from .serializers import (
    CreateUserSerializer,
    CreateUserDeckSerializer,
    UserDeckSerializer,
    UpdateUserDeckSerializer,
    AddMatchResultSerializer,
    ApprovedBetaEmailSerializer,
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
        email = request.data.get("email")
        if not ApprovedBetaEmail.objects.filter(email=email).exists():
            return Response({"error": "This email is not approved for beta access."}, status=status.HTTP_403_FORBIDDEN)
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


class AddApprovedBetaEmailView(APIView):
    def post(self, request):
        if not request.user.get("is_admin"):
            return Response({"error": "Admin access required."}, status=status.HTTP_403_FORBIDDEN)
        serializer = ApprovedBetaEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


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


WIN_RESULTS = ["W", "WW", "LWW", "WLW"]
DRAW_RESULTS = ["WL", "LW", "D"]


class UserDeckAggregateView(APIView):
    def get(self, request):
        from django.db.models import Count, Q

        deck_id = request.query_params.get("deck_id")
        if not deck_id:
            return Response({"error": "deck_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        matches = PlayerMatch.objects.filter(deck_id=deck_id).exclude(match_result__in=DRAW_RESULTS)
        total = matches.count()
        wins = matches.filter(match_result__in=WIN_RESULTS).count()

        by_opponent = (
            matches
            .values("opp_archetype_id", "opp_archetype__name", "opp_archetype__colors")
            .annotate(
                total=Count("id"),
                wins=Count("id", filter=Q(match_result__in=WIN_RESULTS)),
            )
        )

        return Response({
            "total_matches": total,
            "total_wins": wins,
            "win_rate": round(wins / total * 100, 1) if total else 0,
            "by_opponent": [
                {
                    "opp_archetype_id": row["opp_archetype_id"],
                    "opp_archetype_name": row["opp_archetype__name"],
                    "opp_archetype_colors": row["opp_archetype__colors"],
                    "total_matches": row["total"],
                    "wins": row["wins"],
                    "win_rate": round(row["wins"] / row["total"] * 100, 1) if row["total"] else 0,
                }
                for row in by_opponent
            ],
        })


class AddMatchResultView(APIView):
    def post(self, request):
        serializer = AddMatchResultSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match = serializer.save()
        if match.deck_id:
            UserDeck.objects.filter(id=match.deck_id).update(
                num_matches=F("num_matches") + 1,
                last_played=timezone.now(),
            )
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


class UserDeckDetailView(APIView):
    def get(self, request, deck_id):
        try:
            deck = UserDeck.objects.select_related("archetype").get(id=deck_id)
        except UserDeck.DoesNotExist:
            return Response({"error": "Deck not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserDeckSerializer(deck)
        return Response(serializer.data)

    def patch(self, request, deck_id):
        try:
            deck = UserDeck.objects.get(id=deck_id)
        except UserDeck.DoesNotExist:
            return Response({"error": "Deck not found."}, status=status.HTTP_404_NOT_FOUND)
        if deck.user_id != request.user.get("user_id"):
            return Response({"error": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
        serializer = UpdateUserDeckSerializer(deck, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDeckSerializer(deck).data)


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

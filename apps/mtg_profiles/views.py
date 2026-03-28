from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Deck, Card, MatchResult
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


class CreateUserView(APIView):
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

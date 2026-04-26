from django.urls import path
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter
from .views import LoginView, CreateUserView, CreateUserDeckView, AddMatchResultView, AddDeckArchetypeView, DeckViewSet, CardViewSet, MatchResultViewSet

router = DefaultRouter()
router.register(r"decks", DeckViewSet, basename="deck")

decks_router = routers.NestedDefaultRouter(router, r"decks", lookup="deck")
decks_router.register(r"cards", CardViewSet, basename="deck-cards")
decks_router.register(r"matches", MatchResultViewSet, basename="deck-matches")

urlpatterns = [
    path("users/login/", LoginView.as_view(), name="login"),
    path("users/create-user/", CreateUserView.as_view(), name="create-user"),
    path("archetypes/add-deck-archetype/", AddDeckArchetypeView.as_view(), name="add-deck-archetype"),
    path("user-decks/create-user-deck/", CreateUserDeckView.as_view(), name="create-user-deck"),
    path("matches/add-match-result/", AddMatchResultView.as_view(), name="add-match-result"),
] + router.urls + decks_router.urls

from django.urls import path
from rest_framework_nested import routers
from rest_framework.routers import DefaultRouter
from .views import LoginView, CreateUserView, UserProfileView, UpdateProfileView, UserDeckListView, CreateUserDeckView, UserDeckDetailView, UserDeckAggregateView, AddMatchResultView, FormatListView, AddFormatView, AddDeckArchetypeView, DeckArchetypeListView, DeckViewSet, CardViewSet, MatchResultViewSet

router = DefaultRouter()
router.register(r"decks", DeckViewSet, basename="deck")

decks_router = routers.NestedDefaultRouter(router, r"decks", lookup="deck")
decks_router.register(r"cards", CardViewSet, basename="deck-cards")
decks_router.register(r"matches", MatchResultViewSet, basename="deck-matches")

urlpatterns = [
    path("users/login/", LoginView.as_view(), name="login"),
    path("users/create-user/", CreateUserView.as_view(), name="create-user"),
    path("users/<int:user_id>/profile/", UserProfileView.as_view(), name="user-profile"),
    path("users/update-profile/", UpdateProfileView.as_view(), name="update-profile"),
    path("formats/", FormatListView.as_view(), name="format-list"),
    path("formats/add-format/", AddFormatView.as_view(), name="add-format"),
    path("archetypes/", DeckArchetypeListView.as_view(), name="archetype-list"),
    path("archetypes/add-deck-archetype/", AddDeckArchetypeView.as_view(), name="add-deck-archetype"),
    path("user-decks/<int:user_id>/", UserDeckListView.as_view(), name="user-deck-list"),
    path("user-decks/create-user-deck/", CreateUserDeckView.as_view(), name="create-user-deck"),
    path("user-decks/detail/<int:deck_id>/", UserDeckDetailView.as_view(), name="user-deck-detail"),
    path("user-decks/aggregate-results/", UserDeckAggregateView.as_view(), name="user-deck-aggregate"),
    path("matches/add-match-result/", AddMatchResultView.as_view(), name="add-match-result"),
] + router.urls + decks_router.urls

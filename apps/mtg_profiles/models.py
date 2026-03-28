from django.contrib.auth.hashers import make_password
from django.db import models


class UserLogin(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def __str__(self):
        return self.email

    class Meta:
        db_table = "user_logins"


class ProfileField(models.Model):
    class FieldName(models.TextChoices):
        X = "x", "X"
        MOXFIELD = "moxfield", "Moxfield"
        MTGELOPROJECT = "mtgeloproject", "MTG Elo Project"
        DISCORD = "discord", "Discord"
        TWITCH = "twitch", "Twitch"

    user = models.ForeignKey(UserLogin, on_delete=models.CASCADE, related_name="profile_fields")
    field_name = models.CharField(max_length=50, choices=FieldName.choices)
    field_value = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user} — {self.field_name}"

    class Meta:
        db_table = "profile_fields"


class DeckArchetype(models.Model):
    name = models.CharField(max_length=255, unique=True)
    format = models.CharField(max_length=50)
    colors = models.CharField(max_length=10)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "deck_archetypes"


class Deck(models.Model):
    name = models.CharField(max_length=255)
    format = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Card(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="cards")
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    is_sideboard = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.quantity}x {self.name}"


class MatchResult(models.Model):
    class Outcome(models.TextChoices):
        WIN = "win", "Win"
        LOSS = "loss", "Loss"
        DRAW = "draw", "Draw"

    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name="match_results")
    opponent_deck = models.CharField(max_length=255, blank=True)
    outcome = models.CharField(max_length=10, choices=Outcome.choices)
    notes = models.TextField(blank=True)
    played_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.deck.name} vs {self.opponent_deck} — {self.outcome}"


class UserDeck(models.Model):
    user = models.ForeignKey(UserLogin, on_delete=models.CASCADE, related_name="decks")
    archetype = models.ForeignKey(DeckArchetype, on_delete=models.RESTRICT, related_name="user_decks")
    decklist = models.TextField(null=True, blank=True)
    decklist_link = models.TextField(null=True, blank=True)
    num_matches = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} — {self.archetype}"

    class Meta:
        db_table = "user_decks"


class PlayerMatch(models.Model):
    player = models.ForeignKey(UserLogin, on_delete=models.CASCADE, related_name="matches")
    opponent = models.ForeignKey(
        UserLogin, on_delete=models.SET_NULL, null=True, blank=True, related_name="opponent_matches"
    )
    archetype = models.ForeignKey(DeckArchetype, on_delete=models.RESTRICT, related_name="matches")
    opp_archetype = models.ForeignKey(DeckArchetype, on_delete=models.RESTRICT, related_name="opponent_matches")
    deck = models.ForeignKey(
        UserDeck, on_delete=models.SET_NULL, null=True, blank=True, related_name="matches"
    )
    play = models.BooleanField()
    match_result = models.CharField(max_length=10)
    g1_result = models.CharField(max_length=10)
    g2_result = models.CharField(max_length=10, null=True, blank=True)
    g3_result = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return f"{self.player} vs {self.opponent} — {self.match_result}"

    class Meta:
        db_table = "match_results"

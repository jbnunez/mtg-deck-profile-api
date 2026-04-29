from rest_framework import serializers
from .models import UserLogin, ProfileField, Format, DeckArchetype, UserDeck, PlayerMatch, Deck, Card, MatchResult



class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = UserLogin
        fields = ["email", "name", "password"]

    def create(self, validated_data):
        user = UserLogin(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class ProfileFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileField
        fields = ["field_name", "field_value"]


class UpdateProfileSerializer(serializers.Serializer):
    field_name = serializers.ChoiceField(choices=ProfileField.FieldName.choices)
    field_value = serializers.CharField(max_length=255)


class UserProfileSerializer(serializers.ModelSerializer):
    profile_fields = ProfileFieldSerializer(many=True, read_only=True)

    class Meta:
        model = UserLogin
        fields = ["id", "name", "profile_fields"]


class FormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = ["id", "name", "description"]


class DeckArchetypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeckArchetype
        fields = ["id", "name", "format", "colors"]


class CreateUserDeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeck
        fields = ["id", "user", "archetype", "name", "decklist", "decklist_link"]


class UserDeckSerializer(serializers.ModelSerializer):
    archetype = DeckArchetypeSerializer(read_only=True)

    class Meta:
        model = UserDeck
        fields = ["id", "user", "archetype", "name", "decklist", "decklist_link", "num_matches", "last_played"]


class UpdateUserDeckSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeck
        fields = ["archetype", "name", "decklist", "decklist_link"]


class AddMatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerMatch
        fields = [
            "id", "player", "opponent", "archetype", "opp_archetype",
            "deck", "play", "match_result", "g1_result", "g2_result", "g3_result",
        ]


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ["id", "name", "quantity", "is_sideboard"]


class MatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchResult
        fields = ["id", "opponent_deck", "outcome", "notes", "played_at"]


class DeckSerializer(serializers.ModelSerializer):
    cards = CardSerializer(many=True, read_only=True)
    match_results = MatchResultSerializer(many=True, read_only=True)

    class Meta:
        model = Deck
        fields = ["id", "name", "format", "description", "created_at", "updated_at", "cards", "match_results"]


class DeckListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deck
        fields = ["id", "name", "format", "description", "created_at", "updated_at"]

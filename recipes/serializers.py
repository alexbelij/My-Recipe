#  Copyright (c) Code Written and Tested by Ahmed Emad in 24/03/2020, 14:36.
from rest_framework import serializers

from recipes.models import TagModel, RecipeModel, IngredientModel, RecipeImageModel, RecipeReviewModel
from users.serializers import UserSerializer


class TagField(serializers.Field):
    """Field for recipe tags"""

    def to_internal_value(self, data):
        tag, created = TagModel.objects.get_or_create(tag=data)
        return tag

    def to_representation(self, value):
        return value.tag


class IngredientsField(serializers.Field):
    """Field for recipe ingredients"""

    def to_internal_value(self, data):
        ingredient = IngredientModel(name=data)
        return ingredient

    def to_representation(self, value):
        return value.name


class RecipeImageField(serializers.ImageField):  # used for nested serializers
    """Field for recipe images"""

    def to_internal_value(self, data):
        image_field = super().to_internal_value(data)
        image = RecipeImageModel(image=image_field)
        return image

    def to_representation(self, value):
        return value.image.url


class RecipeImageSerializer(serializers.ModelSerializer):  # used for views
    """Serializer for recipe images"""

    class Meta:
        model = RecipeImageModel
        fields = ('image',)


class RecipeReviewsSerializer(serializers.ModelSerializer):
    """Serializer for recipe reviews"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = RecipeReviewModel
        fields = ('user', 'title', 'slug', 'rating', 'timestamp', 'body')
        extra_kwargs = {
            'slug': {
                'read_only': True
            }
        }


class DetailedRecipeSerializer(serializers.ModelSerializer):
    """Detailed Serializer for recipe model"""

    user = UserSerializer(read_only=True)
    tags = serializers.ListSerializer(child=TagField(), required=False)
    ingredients = serializers.ListSerializer(child=IngredientsField())
    images = serializers.ListSerializer(child=RecipeImageField(), required=False)
    reviews = RecipeReviewsSerializer(many=True, read_only=True)
    favourites_count = serializers.ReadOnlyField()
    reviews_count = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()

    class Meta:
        model = RecipeModel
        fields = ('user', 'name', 'main_image', 'time_to_finish', 'rating', 'ingredients',
                  'description', 'body', 'images', 'tags', 'timestamp', 'favourites_count',
                  'reviews', 'reviews_count')

    def create(self, validated_data):
        user = self.context.get('user', None)
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        images = validated_data.pop('images', [])

        recipe = RecipeModel.objects.create(user=user, **validated_data)

        for tag in tags:
            recipe.tags.add(tag)

        for image in images:
            image.recipe = recipe
            image.save()

        for ingredient in ingredients:
            ingredient.recipe = recipe
            ingredient.save()

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        images = validated_data.pop('images', None)

        recipe = super().update(instance, validated_data)

        if images is not None:
            for image in images:
                image.recipe = recipe
                image.save()
            recipe.images.set(images)

        if ingredients is not None:
            for ingredient in ingredients:
                ingredient.recipe = recipe
                ingredient.save()
            recipe.ingredients.set(ingredients)

        if tags is not None:
            recipe.tags.set(tags)

        return recipe


class RecipeSerializer(serializers.ModelSerializer):
    """Read-only Serializer for recipe model"""
    tags = serializers.ListSerializer(child=TagField())
    favourites_count = serializers.ReadOnlyField()

    class Meta:
        model = RecipeModel
        fields = ('slug', 'name', 'main_image', 'time_to_finish', 'description',
                  'tags', 'timestamp', 'favourites_count')

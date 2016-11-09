# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-14 23:38
from __future__ import unicode_literals

import json

from django.db import migrations


def split_recipes(apps, schema_editor):
    """
    Split each show-heartbeat recipe into multiple recipes: one for each
    survey configured in the recipe's arguments.
    """
    Recipe = apps.get_model('recipes', 'Recipe')

    heartbeat_recipes = Recipe.objects.filter(action__name='show-heartbeat')
    for recipe in heartbeat_recipes:
        # Delete the original, and use it as a template for new recipes.
        recipe.delete()
        recipe.enabled = False

        recipe_name = recipe.name
        arguments = json.loads(recipe.arguments_json)
        defaults = arguments.get('defaults', {})

        for survey in arguments['surveys']:
            recipe.pk = None
            recipe.name = recipe_name

            if survey.get('title'):
                recipe.name += ' - ' + survey.get('title')

            def _surveyAttr(name):
                return survey.get(name) or defaults.get(name, '')

            recipe.arguments_json = json.dumps({
                'surveyId': arguments['surveyId'],
                'message': _surveyAttr('message'),
                'engagementButtonLabel': _surveyAttr('engagementButtonLabel'),
                'thanksMessage': _surveyAttr('thanksMessage'),
                'postAnswerUrl': _surveyAttr('postAnswerUrl'),
                'learnMoreMessage': _surveyAttr('learnMoreMessage'),
                'learnMoreUrl': _surveyAttr('learnMoreUrl'),
            })
            recipe.save()


def unsplit_recipes(apps, schema_editor):
    """
    Convert split recipes back into unsplit ones. This does not
    recombine recipes that were previously combined, it just reformats
    their arguments to be valid to the old schema.
    """
    Recipe = apps.get_model('recipes', 'Recipe')

    heartbeat_recipes = Recipe.objects.filter(action__name='show-heartbeat')
    for recipe in heartbeat_recipes:
        arguments = json.loads(recipe.arguments_json)
        recipe.arguments_json = json.dumps({
            'surveyId': arguments['surveyId'],
            'defaults': {
                'message': arguments.get('message', ''),
                'engagementButtonLabel': arguments.get('engagementButtonLabel', ''),
                'thanksMessage': arguments.get('thanksMessage', ''),
                'postAnswerUrl': arguments.get('postAnswerUrl', ''),
                'learnMoreMessage': arguments.get('learnMoreMessage', ''),
                'learnMoreUrl': arguments.get('learnMoreUrl', ''),
            },
            'surveys': [{
                # Avoid stacking the names if we migrate back-and-forth
                'title': '',
                'weight': 1,
            }],
        })
        recipe.save()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0032_remove_auto_now'),
    ]

    operations = [
        migrations.RunPython(split_recipes, unsplit_recipes),
    ]
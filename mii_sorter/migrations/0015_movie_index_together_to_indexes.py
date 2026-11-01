from django.db import migrations, models

INDEX = models.Index(fields=['year', 'title'], name='mii_sorter__year_6a714a_idx')


def rename_or_create_index(apps, schema_editor):
    """
    Databases migrated before Django 5.1 have the unnamed index_together index: rename it.
    Fresh databases don't (0001 and 0005 no longer create it): create it.
    """
    movie = apps.get_model('mii_sorter', 'Movie')
    with schema_editor.connection.cursor() as cursor:
        constraints = schema_editor.connection.introspection.get_constraints(cursor, movie._meta.db_table)
    old_names = [name for name, info in constraints.items()
                 if info['index'] and not info['unique'] and not info['primary_key']
                 and info['columns'] == ['year', 'title'] and name != INDEX.name]
    if INDEX.name in constraints:
        return
    if old_names:
        schema_editor.rename_index(movie, models.Index(fields=['year', 'title'], name=old_names[0]), INDEX)
    else:
        schema_editor.add_index(movie, INDEX)


def remove_index(apps, schema_editor):
    schema_editor.remove_index(apps.get_model('mii_sorter', 'Movie'), INDEX)


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0014_auto_20230209_1207'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[migrations.AddIndex(model_name='movie', index=INDEX)],
            database_operations=[migrations.RunPython(rename_or_create_index, remove_index)],
        ),
    ]

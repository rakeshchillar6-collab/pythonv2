# vectorsearch/migrations/0003_bm25_support.py
from django.db import migrations
from django.contrib.postgres.search import SearchVectorField
from django.db.migrations.operations.base import Operation

# --- Custom Operation for Idempotency ---
# This custom operation allows running raw SQL and checks if the function/trigger
# already exists to avoid errors on re-runs. This makes migrations more robust.

class CreateOrReplaceFunction(Operation):
    reversible = True

    def __init__(self, name, sql):
        self.name = name
        self.sql = sql

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(self.sql)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"DROP FUNCTION IF EXISTS {self.name}();")

    def describe(self):
        return f"Creates or replaces the {self.name} function."


class CreateOrReplaceTrigger(Operation):
    reversible = True

    def __init__(self, name, table, sql):
        self.name = name
        self.table = table
        self.sql = sql

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(self.sql)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(f"DROP TRIGGER IF EXISTS {self.name} ON {self.table};")

    def describe(self):
        return f"Creates or replaces the {self.name} trigger."


# --- Migration Definition ---

# The SQL for the trigger function.
# It computes the tsvector from the chunk's text and the corpus's language.
# The language mapping ('fa' -> 'simple') is a basic approach. For advanced
# Persian FTS, a custom text search configuration would be needed.
TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION update_chunk_tsvector()
RETURNS TRIGGER AS $$
DECLARE
    corpus_lang TEXT;
BEGIN
    SELECT lang INTO corpus_lang FROM vectorsearch_corpus WHERE id = (
        SELECT corpus_id FROM vectorsearch_document WHERE id = NEW.document_id
    );

    NEW.tsvector := to_tsvector(
        CASE
            WHEN corpus_lang = 'fa' THEN 'simple'  -- Using 'simple' for Persian as a default
            WHEN corpus_lang = 'en' THEN 'english'
            ELSE 'simple'
        END,
        NEW.text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

# The SQL to create the trigger on the Chunk table.
# It fires the function before any insert or update.
CREATE_TRIGGER_SQL = """
CREATE TRIGGER chunk_tsvector_update_trigger
BEFORE INSERT OR UPDATE ON vectorsearch_chunk
FOR EACH ROW EXECUTE FUNCTION update_chunk_tsvector();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('vectorsearch', '0002_auto'),
    ]

    operations = [
        # 1. Add the tsvector field to the Chunk model
        migrations.AddField(
            model_name='chunk',
            name='tsvector',
            field=SearchVectorField(null=True, editable=False),
        ),

        # 2. Create the trigger function
        CreateOrReplaceFunction(
            name='update_chunk_tsvector',
            sql=TRIGGER_FUNCTION_SQL
        ),

        # 3. Create the trigger on the table
        CreateOrReplaceTrigger(
            name='chunk_tsvector_update_trigger',
            table='vectorsearch_chunk',
            sql=CREATE_TRIGGER_SQL,
        ),

        # 4. Create a GIN index on the new tsvector field for fast FTS
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS chunk_tsvector_gin_index
            ON vectorsearch_chunk
            USING GIN(tsvector);
            """,
            reverse_sql="DROP INDEX IF EXISTS chunk_tsvector_gin_index;"
        ),
    ]

    # Add a fake dependency if needed to ensure postgres_search app is installed
    # This might be needed if django.contrib.postgres is not in INSTALLED_APPS by default
    initial = True # Fake initial to avoid auto-dependency issues in some setups

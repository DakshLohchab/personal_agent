"""Phase 3B file storage metadata and document foundation.

Revision ID: 20261003_0002
Revises: 20261002_0001
"""

from typing import Sequence, Union

from alembic import op

revision: str = "20261003_0002"
down_revision: Union[str, None] = "20261002_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE files ADD COLUMN object_key text;
        ALTER TABLE files ADD COLUMN original_filename text;
        ALTER TABLE files ADD COLUMN mime_type text;
        ALTER TABLE files ADD COLUMN sha256 text;
        ALTER TABLE files ADD COLUMN storage_provider text NOT NULL DEFAULT 'r2';
        ALTER TABLE files ADD COLUMN status text NOT NULL DEFAULT 'pending';
        ALTER TABLE files ADD COLUMN extraction_status text NOT NULL DEFAULT 'not_started';
        ALTER TABLE files ADD COLUMN uploaded_at timestamptz;
        ALTER TABLE files ADD COLUMN created_by uuid;
        UPDATE files
        SET original_filename = original_name,
            mime_type = COALESCE(media_type, 'application/octet-stream'),
            sha256 = content_hash,
            created_by = user_id,
            object_key = 'users/' || user_id::text || '/files/' || id::text || '/' ||
                regexp_replace(original_name, '[^A-Za-z0-9._-]', '_', 'g');
        ALTER TABLE files ALTER COLUMN object_key SET NOT NULL;
        ALTER TABLE files ALTER COLUMN original_filename SET NOT NULL;
        ALTER TABLE files ALTER COLUMN mime_type SET NOT NULL;
        ALTER TABLE files ALTER COLUMN created_by SET NOT NULL;
        ALTER TABLE files ALTER COLUMN size_bytes TYPE bigint;
        ALTER TABLE files ADD CONSTRAINT uq_files_object_key UNIQUE (object_key);
        ALTER TABLE files ADD CONSTRAINT ck_files_status
            CHECK (status IN ('pending', 'uploaded', 'processing', 'ready', 'failed', 'deleted'));
        ALTER TABLE files ADD CONSTRAINT ck_files_extraction_status
            CHECK (extraction_status IN (
                'not_started', 'queued', 'processing', 'complete', 'failed'
            ));
        CREATE INDEX ix_files_user_status ON files(user_id, status);

        ALTER TABLE documents ADD COLUMN document_type text;
        ALTER TABLE documents ADD COLUMN page_count integer;
        ALTER TABLE documents ADD COLUMN text_status text NOT NULL DEFAULT 'not_started';
        UPDATE documents SET document_type = COALESCE(metadata->>'document_type', 'unknown');
        ALTER TABLE documents ALTER COLUMN document_type SET NOT NULL;
        UPDATE documents SET file_id = (
            SELECT id FROM files WHERE files.user_id = documents.user_id
            AND files.id = documents.file_id
        ) WHERE file_id IS NOT NULL;
        ALTER TABLE documents ALTER COLUMN file_id SET NOT NULL;
        ALTER TABLE documents ADD CONSTRAINT uq_documents_file_id UNIQUE (file_id);
        ALTER TABLE documents ADD CONSTRAINT ck_documents_text_status
            CHECK (text_status IN ('not_started', 'queued', 'processing', 'complete', 'failed'));

        ALTER TABLE document_chunks ADD COLUMN text text;
        ALTER TABLE document_chunks ADD COLUMN page_number integer;
        ALTER TABLE document_chunks ADD COLUMN section text;
        ALTER TABLE document_chunks ADD COLUMN content_hash text;
        UPDATE document_chunks SET text = content, content_hash = md5(content);
        ALTER TABLE document_chunks ALTER COLUMN text SET NOT NULL;
        ALTER TABLE document_chunks ALTER COLUMN content_hash SET NOT NULL;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE document_chunks DROP COLUMN IF EXISTS content_hash;
        ALTER TABLE document_chunks DROP COLUMN IF EXISTS section;
        ALTER TABLE document_chunks DROP COLUMN IF EXISTS page_number;
        ALTER TABLE document_chunks DROP COLUMN IF EXISTS text;
        ALTER TABLE documents DROP CONSTRAINT IF EXISTS ck_documents_text_status;
        ALTER TABLE documents DROP CONSTRAINT IF EXISTS uq_documents_file_id;
        ALTER TABLE documents DROP COLUMN IF EXISTS text_status;
        ALTER TABLE documents DROP COLUMN IF EXISTS page_count;
        ALTER TABLE documents DROP COLUMN IF EXISTS document_type;
        DROP INDEX IF EXISTS ix_files_user_status;
        ALTER TABLE files DROP CONSTRAINT IF EXISTS ck_files_extraction_status;
        ALTER TABLE files DROP CONSTRAINT IF EXISTS ck_files_status;
        ALTER TABLE files DROP CONSTRAINT IF EXISTS uq_files_object_key;
        ALTER TABLE files DROP COLUMN IF EXISTS created_by;
        ALTER TABLE files DROP COLUMN IF EXISTS uploaded_at;
        ALTER TABLE files DROP COLUMN IF EXISTS extraction_status;
        ALTER TABLE files DROP COLUMN IF EXISTS status;
        ALTER TABLE files DROP COLUMN IF EXISTS storage_provider;
        ALTER TABLE files DROP COLUMN IF EXISTS sha256;
        ALTER TABLE files DROP COLUMN IF EXISTS mime_type;
        ALTER TABLE files DROP COLUMN IF EXISTS original_filename;
        ALTER TABLE files DROP COLUMN IF EXISTS object_key;
        """
    )

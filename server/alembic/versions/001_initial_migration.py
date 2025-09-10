"""Initial migration for scene graph database

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create video table
    op.create_table('video',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('video_unique_id', sa.Integer(), nullable=False),
        sa.Column('drama_name', sa.String(length=255), nullable=False),
        sa.Column('episode_number', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('video_unique_id')
    )
    op.create_index('idx_video_unique_id', 'video', ['video_unique_id'], unique=False)
    op.create_index('idx_video_drama_episode', 'video', ['drama_name', 'episode_number'], unique=False)
    op.create_unique_constraint('uq_video_drama_episode', 'video', ['drama_name', 'episode_number'])

    # Create scenes table
    op.create_table('scenes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('scene_number', sa.String(length=255), nullable=False),
        sa.Column('scene_place', sa.Text(), nullable=True),
        sa.Column('scene_time', sa.String(length=100), nullable=True),
        sa.Column('scene_atmosphere', sa.Text(), nullable=True),
        sa.Column('start_frame', sa.Integer(), nullable=True),
        sa.Column('end_frame', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['video.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_scenes_video_id', 'scenes', ['video_id'], unique=False)
    op.create_unique_constraint('uq_scene_video_number', 'scenes', ['video_id', 'scene_number'])

    # Create objects table
    op.create_table('objects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('super_type', sa.String(length=100), nullable=False),
        sa.Column('type_of', sa.String(length=100), nullable=False),
        sa.Column('label', sa.Text(), nullable=False),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_objects_scene_id', 'objects', ['scene_id'], unique=False)
    op.create_index('idx_objects_super_type', 'objects', ['super_type'], unique=False)
    op.create_index('idx_objects_type_of', 'objects', ['type_of'], unique=False)
    op.create_index('idx_objects_label', 'objects', ['label'], unique=False)
    op.create_unique_constraint('uq_object_scene_id', 'objects', ['scene_id', 'object_id'])

    # Create events table
    op.create_table('events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('verb', sa.String(length=100), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=True),
        sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_events_scene_id', 'events', ['scene_id'], unique=False)
    op.create_index('idx_events_verb', 'events', ['verb'], unique=False)
    op.create_unique_constraint('uq_event_scene_id', 'events', ['scene_id', 'event_id'])

    # Create spatial table
    op.create_table('spatial',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('spatial_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('predicate', sa.String(length=100), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_spatial_scene_id', 'spatial', ['scene_id'], unique=False)
    op.create_index('idx_spatial_predicate', 'spatial', ['predicate'], unique=False)
    op.create_unique_constraint('uq_spatial_scene_id', 'spatial', ['scene_id', 'spatial_id'])

    # Create temporal table
    op.create_table('temporal',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scene_id', sa.Integer(), nullable=False),
        sa.Column('temporal_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer(), nullable=False),
        sa.Column('predicate', sa.String(length=100), nullable=False),
        sa.Column('object_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['scene_id'], ['scenes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_temporal_scene_id', 'temporal', ['scene_id'], unique=False)
    op.create_index('idx_temporal_predicate', 'temporal', ['predicate'], unique=False)
    op.create_unique_constraint('uq_temporal_scene_id', 'temporal', ['scene_id', 'temporal_id'])

    # Create embeddings table with pgvector support
    op.create_table('embeddings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('node_id', sa.Integer(), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=True),  # Will be updated to vector type after pgvector extension
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_embeddings_node_id', 'embeddings', ['node_id'], unique=False)
    op.create_index('idx_embeddings_node_type', 'embeddings', ['node_type'], unique=False)
    op.create_unique_constraint('uq_embedding_node_type', 'embeddings', ['node_id', 'node_type'])
    
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Update embedding column to vector type
    op.execute('ALTER TABLE embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::vector')


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('embeddings')
    op.drop_table('temporal')
    op.drop_table('spatial')
    op.drop_table('events')
    op.drop_table('objects')
    op.drop_table('scenes')
    op.drop_table('video')
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')

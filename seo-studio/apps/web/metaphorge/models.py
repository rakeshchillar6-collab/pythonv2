# metaphorge/models.py
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField

from common.models import BaseModel
from core.models import Site
from content.models import Post, Media

class MFProject(BaseModel):
    class Status(models.TextChoices):
        IDLE = 'idle', 'Idle'
        RUNNING = 'running', 'Running'
        PAUSED = 'paused', 'Paused'
        STOPPED = 'stopped', 'Stopped'
        DONE = 'done', 'Done'

    class Stage(models.TextChoices):
        SEED = 'seed', 'Seed'
        COMBINE = 'combine', 'Combine'
        EXPAND = 'expand', 'Expand'
        SERP = 'serp', 'SERP Collection'
        CLUSTER = 'cluster', 'Clustering'
        LSI_ENTITY = 'lsi_entity', 'LSI & Entity Extraction'
        PROMPT = 'prompt', 'Prompt Building'
        TEXT_GEN = 'text_gen', 'Text Generation'
        IMAGE_GEN = 'image_gen', 'Image Generation'
        PUBLISH = 'publish', 'Publishing'

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='mf_projects')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.IDLE)
    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.SEED)
    config = models.JSONField(default=dict, help_text="Project configuration.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self) -> str:
        return self.name

class MFSeed(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='seeds')
    text = models.CharField(max_length=255)
    lang = models.CharField(max_length=10, default='auto')
    source = models.CharField(max_length=20, default='manual')
    active = models.BooleanField(default=True)

class MFCombo(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='combos')
    seed = models.ForeignKey(MFSeed, on_delete=models.CASCADE, related_name='combos')
    pattern = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)

class MFKeywordRaw(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='raw_keywords')
    seed = models.ForeignKey(MFSeed, on_delete=models.CASCADE)
    combo = models.ForeignKey(MFCombo, on_delete=models.CASCADE, null=True, blank=True)
    phrase = models.CharField(max_length=512)
    source = models.CharField(max_length=20, default='suggest')
    depth = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('project', 'phrase')

class MFKeywordExpanded(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='expanded_keywords')
    parent_raw = models.ForeignKey(MFKeywordRaw, on_delete=models.CASCADE, related_name='children')
    phrase = models.CharField(max_length=512)
    depth = models.PositiveIntegerField()

    class Meta:
        unique_together = ('project', 'phrase')

class MFSerpResult(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='serp_results')
    phrase = models.CharField(max_length=512, unique=True)
    top10 = models.JSONField(default=list)
    fetched_at = models.DateTimeField(auto_now_add=True)

class MFCluster(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='clusters')
    main_key = models.CharField(max_length=512)
    secondaries = ArrayField(models.CharField(max_length=512), default=list)
    phrases = ArrayField(models.CharField(max_length=512), default=list)
    similarity_k = models.PositiveIntegerField()

class MFCorpusDoc(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='corpus_docs')
    cluster = models.ForeignKey(MFCluster, on_delete=models.CASCADE, related_name='corpus_docs')
    url = models.URLField(max_length=1024)
    title = models.CharField(max_length=512)
    raw_html = models.TextField()
    cleaned_text = models.TextField()
    fetched_at = models.DateTimeField(auto_now_add=True)

class MFAnalytics(BaseModel):
    project = models.OneToOneField(MFProject, on_delete=models.CASCADE, related_name='analytics')
    metrics = models.JSONField(default=dict)

class MFLSIEntity(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='lsi_entities')
    cluster = models.OneToOneField(MFCluster, on_delete=models.CASCADE, related_name='lsi_entities')
    lsi = ArrayField(models.CharField(max_length=255), default=list)
    entities = ArrayField(models.CharField(max_length=255), default=list)
    method = models.CharField(max_length=50, default='tfidf_spacy')

class MFPrompt(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='prompts')
    cluster = models.ForeignKey(MFCluster, on_delete=models.CASCADE, related_name='prompts')
    template_ref = models.CharField(max_length=100)
    prompt_text = models.TextField()
    vars = models.JSONField(default=dict)

class MFDraft(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='drafts')
    cluster = models.ForeignKey(MFCluster, on_delete=models.CASCADE, related_name='drafts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='mf_drafts')
    status = models.CharField(max_length=20, default='draft')

class MFImagePlan(BaseModel):
    project = models.ForeignKey(MFProject, on_delete=models.CASCADE, related_name='image_plans')
    cluster = models.ForeignKey(MFCluster, on_delete=models.CASCADE, related_name='image_plans')
    name = models.CharField(max_length=255)
    placement = models.CharField(max_length=50)
    position = models.CharField(max_length=20, default='after')
    prompt_text = models.TextField()
    generated_media = models.ForeignKey(Media, on_delete=models.SET_NULL, null=True, blank=True)

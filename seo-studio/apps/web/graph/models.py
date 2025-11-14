# graph/models.py
from django.db import models
from common.models import BaseModel
from content.models import Post, Category

class TopicNode(BaseModel):
    class NodeRole(models.TextChoices):
        PILLAR = 'PILLAR', 'Pillar'
        CLUSTER = 'CLUSTER', 'Cluster'
        SUPPORTING = 'SUPPORTING', 'Supporting'

    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='topic_node')
    role = models.CharField(max_length=15, choices=NodeRole.choices)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    pagerank_internal = models.FloatField(default=0.0)
    inlinks_count = models.PositiveIntegerField(default=0)
    outlinks_count = models.PositiveIntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.post.title} ({self.get_role_display()})"

class TopicEdge(BaseModel):
    source = models.ForeignKey(TopicNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    destination = models.ForeignKey(TopicNode, on_delete=models.CASCADE, related_name='incoming_edges')
    anchor_text = models.CharField(max_length=255)
    weight = models.FloatField(default=1.0)

    class Meta:
        unique_together = ('source', 'destination')

    def __str__(self) -> str:
        return f"{self.source.post.title} -> {self.destination.post.title}"

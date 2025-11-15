# adminui/views/ops/health.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from celery import current_app

def get_queue_depths():
    """Gets the current depth of all configured Celery queues."""
    try:
        with current_app.connection() as connection:
            queues = ['default', 'embeddings', 'serp', 'publishing', 'reports']
            depths = {}
            for queue in queues:
                depths[queue] = connection.default_channel.queue_declare(
                    queue=queue, passive=True
                ).message_count
            return depths
    except Exception as e:
        return {"error": str(e)}

@login_required
def system_health_dashboard(request):
    """Main view for the system health and operations dashboard."""

    # In a real app, these would come from a metrics store like Prometheus or Redis
    metrics = {
        'api_p95_latency': 180, # ms
        'job_success_rate': "99.8%",
    }

    context = {
        'queue_depths': get_queue_depths(),
        'metrics': metrics,
    }
    return render(request, 'adminui/pages/ops/health.html', context)

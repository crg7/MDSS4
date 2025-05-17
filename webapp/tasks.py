import logging
import requests
from celery import shared_task
from django.conf import settings
from users.models import Question, Answer, Notification

logger = logging.getLogger(__name__)

def _get_analyzer_token():
    resp = requests.post(
        f"{settings.ANALYZER_BASE}/api/auth/token/",
        json={"username": settings.ANALYZER_USER, "password": settings.ANALYZER_PASS},
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=10
    )
    resp.raise_for_status()
    return resp.json().get('access')


def _prepare_texts(instance, model_name):
    if model_name == 'question':
        return [
            {"id": "title", "text": instance.title},
            {"id": "description", "text": instance.description},
        ]
    return [{"id": "description", "text": instance.description}]


@shared_task(bind=True)
def send_notifications(self, instance_id):
    logger.info("Sending notifications for instance %s", instance_id)


@shared_task(bind=True)
def analyze_text(self, model_name, instance_id):
    Model = Question if model_name == 'question' else Answer
    instance = Model.objects.get(pk=instance_id)
    texts_list = _prepare_texts(instance, model_name)

    try:
        token = _get_analyzer_token()
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        resp = requests.post(
            f"{settings.ANALYZER_BASE}/api/analyzer/analysis/",
            json={"texts_list": texts_list},
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise self.retry(exc=exc, countdown=60, max_retries=3)

    data = resp.json()
    final = data.get('final_result')
    if final is not None:
        instance.apto = final
    else:
        results = data.get('retrieved_result', [])
        instance.apto = not any(
            entry.get('palabrotas', {}).get('contains', False)
            for entry in results
        )
    instance.save(update_fields=['apto'])

    status = 'válida' if instance.apto else 'inapropiada'
    Notification.objects.create(
        user=instance.user,
        description=f"Tu última {model_name} fue marcada como {status}"
    )

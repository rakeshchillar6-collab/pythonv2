# metaphorge/tasks/combine.py
import logging
from celery import shared_task
from ..models import MFProject, MFSeed, MFCombo

logger = logging.getLogger(__name__)

@shared_task
def combine_seeds_task(project_id: str):
    """
    Generates keyword combinations based on the project's seeds and configuration.
    """
    try:
        project = MFProject.objects.get(id=project_id)
        seeds = MFSeed.objects.filter(project=project, active=True)
        config = project.config

        logger.info(f"Starting seed combination for project {project.name} with {len(seeds)} seeds.")

        for seed in seeds:
            # Pattern: space
            MFCombo.objects.get_or_create(project=project, seed=seed, pattern='space', defaults={'payload': {'query': f"{seed.text} "}})

            # Pattern: space_q
            MFCombo.objects.get_or_create(project=project, seed=seed, pattern='space_q', defaults={'payload': {'query': f"{seed.text} ?"}})

            # Pattern: space_letters
            if config.get('letters') in ['en', 'both']:
                for letter in "abcdefghijklmnopqrstuvwxyz":
                    MFCombo.objects.get_or_create(project=project, seed=seed, pattern='space_letters', payload={'query': f"{seed.text} {letter}"})
            if config.get('letters') in ['fa', 'both']:
                # Simplified Persian alphabet
                for letter in "ا ب پ ت ث ج چ ح خ د ذ ر ز ژ س ش ص ض ط ظ ع غ ف ق ک گ ل م ن و ه ی":
                    MFCombo.objects.get_or_create(project=project, seed=seed, pattern='space_letters', payload={'query': f"{seed.text} {letter}"})

            # Pattern: space_numbers
            num_range = config.get('numbers_range', [1, 9])
            for i in range(num_range[0], num_range[1] + 1):
                MFCombo.objects.get_or_create(project=project, seed=seed, pattern='space_numbers', payload={'query': f"{seed.text} {i}"})

            # Pattern: before_after
            for pair in config.get('before_after', []):
                before, after = pair
                MFCombo.objects.get_or_create(project=project, seed=seed, pattern='before_after', payload={'query': f"{before} {seed.text} {after}"})

        logger.info(f"Finished seed combination for project {project.name}.")
        return f"Generated combos for {len(seeds)} seeds."

    except MFProject.DoesNotExist:
        logger.error(f"MFProject with ID {project_id} not found.")
        raise

import datetime
import logging
import sys

import workflow
from workflow import web

logger = logging.getLogger(__name__)
today = datetime.datetime.today()


def main(wf):
    # Switch this to query same stats backend
    def wanikani():
        return web.get('https://www.wanikani.com/api/user/{0}/study-queue'.format(
            wf.settings['wanikani_api']
        )).json()

    def countdowns():
        return web.get('https://tsundere.co/api/countdown.json').json()

    def issues():
        return web.get('https://api.github.com/repos/kfdm/alfred-info-dashboard/issues').json()

    wk = wf.cached_data('wanikani', wanikani)
    wf.add_item(
        'WaniKani',
        'Reviews: {reviews_available} Lessons: {lessons_available} '.format(**wk['requested_information']),
        arg='https://www.wanikani.com',
        icon='wk.png',
        valid=True,
    )

    for countdown in wf.cached_data('countdowns', countdowns).get('results', []):
        created = datetime.datetime.strptime(countdown['created'], "%Y-%m-%dT%H:%M:%SZ")
        delta = created - today
        wf.add_item(
            countdown['label'],
            str(delta),
            icon=workflow.ICON_CLOCK,
        )

    issues = wf.cached_data('issues', issues)
    wf.add_item(
        'Issues',
        '{} issues'.format(len(issues)),
        arg='https://github.com/kfdm/alfred-info-dashboard/issues',
        icon=workflow.ICON_WARNING,
        valid=True,
    )

    wf.send_feedback()

if __name__ == '__main__':
    sys.exit(main(workflow.Workflow()))

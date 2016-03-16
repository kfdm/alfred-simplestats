import datetime
import logging
import os
import sys

import pytz
import workflow
from workflow import web

logger = logging.getLogger(__name__)
timezone = pytz.timezone('Asia/Tokyo')
today = timezone.localize(datetime.datetime.today()).replace(microsecond=0)
tomorrow = today.replace(hour=0, minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
now = datetime.datetime.now(timezone).replace(microsecond=0)



class Workflow(workflow.Workflow):
    def cached_link(self, key, url, **kwargs):
        def fetch():
            if 'headers' not in kwargs:
                kwargs['headers'] = {}

            kwargs['headers']['user-agent'] = 'alfred-info-dashboard/{0} https://github.com/kfdm/alfred-info-dashboard'.format(self.version)
            return web.get(url, **kwargs).json()
        # Cache data for 5 minutes
        return self.cached_data(key, fetch, 300)

    def countdowns(self):
        return self.cached_link(
            'countdowns',
            'https://tsundere.co/api/countdown.json', headers={
                'Authorization': 'Token ' + self.settings['coutdown_token']
            }
        ).get('results', [])

def main(wf):
    wk = wf.cached_link('wanikani', 'https://www.wanikani.com/api/user/{0}/study-queue'.format(
        wf.settings['wanikani_api']
    ))

    wf.add_item(
        'Time Remaining',
        '{} remaining today'.format(tomorrow - now),
        icon=workflow.ICON_CLOCK,
    )

    wf.add_item(
        'WaniKani',
        'Reviews: {reviews_available} Lessons: {lessons_available} '.format(**wk['requested_information']),
        arg='https://www.wanikani.com',
        icon='wk.png',
        valid=True,
    )

    for countdown in wf.countdowns():
        created = datetime.datetime.strptime(countdown['created'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
        # Simple filter for expired countdowns for now
        if created < today:
            continue
        delta = created - today
        icon = wf.datafile(countdown['id'] + '.png')
        if os.path.exists(icon) is False:
            if countdown['icon']:
                request = web.get(countdown['icon'])
                request.save_to_path(icon)
            else:
                icon = workflow.ICON_CLOCK

        wf.add_item(
            countdown['label'],
            str(delta),
            icon=icon,
        )

    try:
        issues = wf.cached_link('issues', 'https://api.github.com/repos/kfdm/alfred-info-dashboard/issues')
        wf.add_item(
            'Issues',
            '{} issues'.format(len(issues)),
            arg='https://github.com/kfdm/alfred-info-dashboard/issues',
            icon=workflow.ICON_WARNING,
            valid=True,
        )
    except:
        logger.exception('Error fetching from GitHub')

    wf.send_feedback()

if __name__ == '__main__':
    sys.exit(main(Workflow()))

import datetime
import json
import logging
import os
import sys

import pytz
import workflow
from workflow import web

logger = logging.getLogger(__name__)

# Read currently configured timezone
# Taken from
# https://github.com/regebro/tzlocal/blob/master/tzlocal/darwin.py
link = os.readlink("/etc/localtime")
tzname = link[link.rfind("zoneinfo/") + 9:]
timezone = pytz.timezone(tzname)

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
            'https://tsundere.co/api/countdown.json?ordering=created', headers={
                'Authorization': 'Token ' + self.settings['coutdown_token']
            }
        ).get('results', [])


def main(wf):
    items = []
    wk = wf.cached_link('wanikani', 'https://www.wanikani.com/api/user/{0}/study-queue'.format(
        wf.settings['wanikani_api']
    ))

    wf.add_item(
        'Time Remaining',
        '{} remaining today'.format(tomorrow - now),
        icon=workflow.ICON_CLOCK,
    )


    items.append({
        'title': 'WaniKani',
        'subtitle': 'Reviews: {reviews_available} Lessons: {lessons_available} '.format(**wk['requested_information']),
        'arg': 'https://www.wanikani.com',
        'icon': {'path': 'wk.png'},
        'valid': True,
    })

    for countdown in wf.countdowns():
        created = datetime.datetime.strptime(countdown['created'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)

        # Simple filter for expired countdowns for now
        if created < today:
            continue
        delta = created - today
        icon = wf.cachefile(countdown['id'] + '.png')
        if os.path.exists(icon) is False:
            if countdown['icon']:
                request = web.get(countdown['icon'])
                request.save_to_path(icon)
            else:
                icon = workflow.ICON_CLOCK


        items.append({
            'title': countdown['label'],
            'subtitle': str(delta),
            'icon': {'path': icon},
            'mods': {
                'ctrl': {
                    'valid': True,
                    'arg': 'https://tsundere.co/admin/simplestats/countdown/{}/change/'.format(countdown['id']),
                    'subtitle': 'Edit Countdown',
                }
            }
        })

    try:
        issues = wf.cached_link('issues', 'https://api.github.com/repos/kfdm/alfred-info-dashboard/issues')

        items.append({
            'title': 'Issues',
            'subtitle': '{} issues'.format(len(issues)),
            'icon': {'path': workflow.ICON_WARNING},
            'arg': 'https://github.com/kfdm/alfred-info-dashboard/issues',
            'valid': True
        })
    except:
        logger.exception('Error fetching from GitHub')

    print(json.dumps({'items': items}))

if __name__ == '__main__':
    sys.exit(main(Workflow()))

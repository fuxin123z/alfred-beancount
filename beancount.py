#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: Yue Wu
# @Date:   2016-02-29 23:43:43
# @Last Modified by:   Yue Wu
# @Last Modified time: 2017-01-05 12:40:38

import os
import re
import sys
import json
from math import log
from glob import glob
from datetime import datetime


class Beancount:

    '''APPEND OR MODIFY BEANCOUNT ENTRY VIA ALFRED:

    bean_add: add new entry to beancount file;
    bean_clear: clear an entry in beancount file by adding #clear tag;
    bean_cache: create a cache file with all accounts and payees with frequency.
    '''

    def __init__(self, wf, settingpath='beancount.json'):
        self.wf = wf
        self.length = len(wf.args)-1
        self.args = wf.args[1:] + ['']*(6-self.length)
        with open(settingpath, 'r') as settingfile:
            self.settings = json.loads(settingfile.read())

        for k, v in self.settings['icons'].items():
            wfdir = self.wf.workflowdir
            if not os.path.isfile(v.format(workflowdir=wfdir)):
                self.settings['icons'][k] = '{workflowdir}/icons/{cat}.png'
            self.settings['icons'][k] = v.format(workflowdir=wfdir, cat=k)

    def bean_add(self):
        try:
            with open(self.settings['temp_path'], 'r') as tempfile:
                accounts = json.loads(tempfile.read())
        except IOError:
            accounts = self.bean_cache()

        subtitle = u'{from} ➟ {to} by {payee}'
        params = ['from', 'to', 'payee'][:self.length]
        values = {x: '\t' for x in ['from', 'to', 'payee']}

        for index, p in enumerate(params[:self.length-1]):
            values[p] = self.rank(self.args[index], accounts[p])[0][0]

        if self.length <= 3:
            for v, s in self.rank(self.args[self.length-1], accounts[params[-1]]):
                values[params[-1]] = v
                if params[-1] in ['from', 'to']:
                    if v==self.args[self.length-1]:
                        continue
                    icon = self.settings['icons'][v.split(':')[0]]
                else:
                    icon = self.wf.workflowdir + '/icon.png'
                self.wf.add_item(
                    title=v,
                    subtitle=subtitle.format(**values),
                    icon=icon,
                    valid=False
                )
        else:
            values['date'] = datetime.now().strftime('%Y-%m-%d')
            values['amount'] = float(self.args[3])
            if self.args[4]:
                self.args[4] = '#'+self.args[4].replace('+', ' #')
            values['tags'] = self.args[4]
            values['comment'] = self.args[5]
            entry = [self.settings['title_format'].format(**values).strip()]
            entry.append(self.settings['body_format'].format(
                account=values['from'], flow=-values['amount'],
                currency=self.settings['default_currency']
            ))
            entry.append(self.settings['body_format'].format(
                account=values['to'], flow=values['amount'],
                currency=self.settings['default_currency']
            ))
            entry = '\n'.join(entry)
            self.wf.add_item(
                title='New ${amount:.2f} Entry'.format(**values),
                subtitle=subtitle.format(**values),
                valid=True,
                arg=entry,
                copytext=entry
            )

    def bean_cache(self, ledger_folder=None):
        if not ledger_folder:
            ledger_folder = self.settings['ledger_folder']

        beans = []
        for f in glob(ledger_folder+'/*.beancount'):
            with open(f, 'r') as beanfile:
                beans.append(beanfile.read())
        bean = '\n'.join(beans)

        matches = {}
        for key, reg in self.settings['regexes'].items():
            pattern = re.compile(reg)
            matches[key] = pattern.findall(bean)

        accounts = {
            'from': {
                x: matches['from'].count(x)
                for x in matches['open']
                if x not in matches['close']
            },
            'to': {
                x: matches['to'].count(x)
                for x in matches['open']
                if x not in matches['close']
            },
            'payee': {
                x: matches['payee'].count(x)
                for x in set(matches['payee'])
            }
        }

        with open(self.settings['temp_path'], 'w') as tempfile:
            json.dump(accounts, tempfile)

        return accounts

    def bean_clear(self, inputs=None):
        with open(self.settings['default_ledger'], 'r') as beanfile:
            bean = beanfile.read()

        par = re.compile('[^;](\d{4}-\d{2}-\d{2}) ! ?(.*)\n(.+)\n(.+)')
        for m in par.finditer(bean):
            tail = [i.strip() for i in m.group(2).split('"') if i.strip()!='']
            values = {
                'date': m.group(1),
                'from': m.group(3).split()[0],
                'to': m.group(4).split()[0],
                'amount': abs(float(m.group(3).split()[-2])),
                'comment': (tail+['NULL'])[0].upper()
            }

            if inputs and not self.wf.filter(inputs, [values['from']]):
                continue

            self.wf.add_item(
                title='${amount:.2f} with {comment}'.format(**values),
                subtitle=u'{date} {from} ➟ {to}'.format(**values),
                icon=self.settings['icons'][values['from'].split(':')[0]],
                valid=True,
                arg=str(m.start())
            )

    def rank(self, inputs, searches):
        if not inputs:
            return [(inputs, 0)]

        results = self.wf.filter(inputs, searches.keys(), include_score=True)
        results = [(v, s*log(searches[v]+1)) for v, s, _ in results]
        if results:
            return sorted(results, key=lambda x: -x[1])
        else:
            return [(inputs, 0)]


def main(wf):
    bean = Beancount(wf)

    action = wf.args[0]
    if len(wf.args) >= 2:
        inputs = wf.args[1]
    else:
        inputs = None

    if action == 'add':
        bean.bean_add()
    elif action == 'cache':
        bean.bean_cache(inputs)
    elif action == 'clear':
        bean.bean_clear(inputs)

    wf.send_feedback()


if __name__ == '__main__':
    from workflow import Workflow, ICON_INFO
    wf = Workflow(
        update_settings = {
            'github_slug': 'blaulan/alfred-beancount',
            'version': 'v0.2',
        }
    )
    wf.magic_prefix = 'wf:'

    if wf.update_available:
        wf.add_item(
            'New version available',
            'Action this item to install the update',
            autocomplete='wf:update',
            icon=ICON_INFO
        )

    sys.exit(wf.run(main))

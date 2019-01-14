# -*- coding: utf-8 -*-

"""
This addon is based on: Additional Card Fields https://ankiweb.net/shared/info/441235634
                        by https://www.reddit.com/user/Dayjaby/
My modification also contains some functions from other people, for details see the 
comments about these functions.

License: AGPLv3, http://www.gnu.org/licenses/agpl.html


Modifications:
- attempt to fix unicode error (see below)
- also show deck options and stats
- re-arranged code to make it easier to add additional fields: 
  put additional fields below this line: "##add your additional fields here"
  format: addInfo['NameInCardTemplateWindow'] = ValueShownDuringReview

use at your own risk

about the unicode error in Anki 2.0:
the original add-on sometimes throws errors like this:
"UnicodeDecodeError: 'ascii' codec can't decode byte 0xc3 in position 8: ordinal not in range(128)"
This error is because lines 73, 74 
  L73: additionalFields[16] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(first/1000))
  L74: additionalFields[17] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(last/1000)) 
of the original add-on. time.strftime for some locales (languages) outputs non-ascii characters because of:
  %a - Locale’s abbreviated weekday name
  %b - Locale’s abbreviated month name
    (https://docs.python.org/2/library/time.html)
"""

import locale
import copy
import time
from anki.collection import _Collection
from anki.utils import fmtTimeSpan, isWin
from aqt.utils import tooltip

from anki.stats import CardStats
from aqt import mw

import collections


oldRenderQA = _Collection._renderQA


# this is function timefn is from anki from anki/stats.py which is at
# https://github.com/dae/anki/blob/master/anki/stats.py#L77 and
    # Copyright: Damien Elmes <anki@ichi2.net>
    # License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html
def timefn(tm):
    str = ""
    if tm >= 60:
        str = fmtTimeSpan((tm/60)*60, short=True, point=-1, unit=1)
    if tm%60 != 0 or not str:
        str += fmtTimeSpan(tm%60, point=2 if not str else -1, short=True)
    return str


#from Advanced Browser - overdue_days
#https://github.com/hssm/advanced-browser/blob/master/advancedbrowser/advancedbrowser/custom_fields.py#L225
#which is 
    # GPLv3
    # by HSSM (no copyright info found)
def valueForOverdue(odid, queue, type, due, d):
    if odid or queue == 1:
        return
    elif queue == 0 or type == 0:
        return
    elif queue in (2,3) or (type == 2 and queue < 0):
        diff = due - d.sched.today
        if diff < 0:
            return diff * -1
        else:
            return


def _renderQA(self,data,qfmt=None,afmt=None):
    """
    this function overwrites a function from collection.py
    The beginning of this function reads:
        "Returns hash of id, question, answer."
        # data is [cid, nid, mid, did, ord, tags, flds]
        # unpack fields and create dict
    """
    origFieldMap = self.models.fieldMap
    model = self.models.get(data[2])
    if data[0] is None:
        card = None
    elif data[0] == 1:
        card = None
    else:
        try:
            card = self.getCard(data[0])
        except:
            card = None


    origdata = copy.copy(data)
    data[6] += "\x1f"

    addInfo = collections.OrderedDict()

    if card is not None:
        r = mw.reviewer
        d = mw.col
        cs = CardStats(d, r.card)

        if card.odid:
            conf=d.decks.confForDid(card.odid)
        else:
            conf=d.decks.confForDid(card.did)

        (first,last,cnt, total) = self.db.first(
                "select min(id), max(id), count(), sum(time)/1000 from revlog where cid = :id",
                id=card.id)

        if cnt:
            #unicode error fix
            #locales on Windows are more complicated so I just remove the %a and %b
            if isWin:    
                addInfo['FirstReview'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(first/1000))
                addInfo['LastReview'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(last/1000)) 
            else:
                mylocale = locale.getlocale(locale.LC_TIME)
                locale.setlocale(locale.LC_TIME,('en_US', 'UTF-8'))
                addInfo['FirstReview'] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(first/1000))
                addInfo['LastReview'] = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime(last/1000))
                locale.setlocale(locale.LC_TIME,mylocale)

            #https://docs.python.org/2/library/datetime.html  #todo
            addInfo['TimeAvg']  = timefn(total/float(cnt))
            addInfo['TimeTotal'] = timefn(total)

            cOverdueIvl = valueForOverdue(card.odid, card.queue, card.type, card.due, d)
            if cOverdueIvl:
                addInfo['overdue_fmt'] = str(cOverdueIvl) + " day" + ('s' if cOverdueIvl > 1 else '')
                addInfo['overdue_days'] = str(cOverdueIvl)         

        
        addInfo['Ord'] = data[4]
        addInfo['Did'] = card.did
        addInfo['Due'] = card.due
        addInfo['Id'] = card.id
        addInfo['Queue'] = card.queue
        addInfo['Reviews'] = card.reps
        addInfo['Lapses'] = card.lapses
        addInfo['Type'] = card.type
        addInfo['Nid'] = card.nid
        addInfo['Mod'] = time.strftime("%Y-%m-%d",time.localtime(card.mod))
        addInfo['Usn'] = card.usn
        addInfo['Factor'] = card.factor
        addInfo['New?'] = 'New' if card.type==0 else ''
        addInfo['Learning?'] = 'Learning' if card.type==1 and card.queue==3 else ''
        addInfo['Review?'] = 'Review' if card.type==2 else ''
        addInfo['Options_Group_ID'] = conf['id']
        addInfo['Options_Group_Name'] = conf['name']
        addInfo['Ignore_answer_times_longer_than'] = conf['maxTaken']
        addInfo['Show_answer_time'] = conf['timer']
        addInfo['Auto_play_audio'] = conf['autoplay']
        addInfo['When_answer_shown_replay_q'] = conf['replayq']
        addInfo['is_filtered_deck'] = conf['dyn']
        addInfo['deck_usn'] = conf['usn']
        addInfo['deck_mod_time'] = conf['mod']
        addInfo['new__steps_in_minutes'] = conf['new']['delays']
        addInfo['new__order_of_new_cards'] = conf['new']['order']
        addInfo['new__cards_per_day'] = conf['new']['perDay']
        addInfo['graduating_interval'] = conf['new']['ints'][0]
        addInfo['easy_interval'] = conf['new']['ints'][1]
        addInfo['Starting_ease'] = conf['new']['initialFactor'] / 10
        addInfo['bury_related_new_cards'] = conf['new']['bury']
        addInfo['MaxiumReviewsPerDay'] = conf['rev']['perDay']
        addInfo['EasyBonus'] = int(100 * conf['rev']['ease4'])
        addInfo['IntervalModifier'] = int(100 * conf['rev']['ivlFct'])
        addInfo['MaximumInterval'] = conf['rev']['maxIvl']
        addInfo['bur_related_reviews_until_next_day'] = conf['rev']['bury']
        addInfo['lapse_learning_steps'] = conf['lapse']['delays']
        addInfo['lapse_new_ivl'] = int(100 * conf['lapse']['mult'])
        addInfo['lapse_min_ivl'] = conf['lapse']['minInt']
        addInfo['lapse_leech_threshold'] = conf['lapse']['leechFails']
        addInfo['lapse_leech_action'] = conf['lapse']['leechAction']
        addInfo['Date_Created'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(card.nid/1000))
    
        ##add your additional fields here 
  

    #for debugging quickly add all values to template
    tt = " <table>" + "\n"
    for k in addInfo.keys():
        tt += '<tr><td align="left">%s </td><td align="left">  {{info::%s}}  </td></tr> +\n' % (k, k)
    tt += " </table>" + "\n"
    addInfo['allfields'] = tt

    additionalFields = [""] * len(addInfo)

    for i, v in enumerate(addInfo.values()):
        additionalFields[i]=str(v)
                                  
    data[6] += "\x1f".join(additionalFields)   #\x1f is used as a field separator

    def tmpFieldMap(m):
        "Mapping of field name -> (ord, field)."
        d = dict((f['name'], (f['ord'], f)) for f in m['flds'])

        newFields = []
        for k in addInfo.keys():
            newFields.append('info::' + k)

        for i,f in enumerate(newFields):
            d[f] = (len(m['flds'])+i,0)
        return d

    self.models.fieldMap = tmpFieldMap

    result = oldRenderQA(self,data,qfmt,afmt)
    data = origdata
    self.models.fieldMap = origFieldMap
    return result


def previewCards(self, note, type=0):
    existingTemplates = {c.template()[u'name'] : c for c in note.cards()}
    if type == 0:
        cms = self.findTemplates(note)
    elif type == 1:
        cms = [c.template().name() for c in note.cards()]
    else:
        cms = note.model()['tmpls']
    if not cms:
        return []
    cards = []
    for template in cms:
        if template[u'name'] in existingTemplates:
            card = existingTemplates[template[u'name']]
        else:
            card = self._newCard(note, template, 1, flush=False)
        cards.append(card)
    return cards

_Collection._renderQA = _renderQA
_Collection.previewCards = previewCards
 

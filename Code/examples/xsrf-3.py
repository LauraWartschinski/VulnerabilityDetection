# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
# 
# The Original Code is Reddit.
# 
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
# 
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################
from pylons import c
from r2.lib.db.thing     import Thing, Relation, NotFound
from r2.lib.db.operators import lower
from r2.lib.db.userrel   import UserRel
from r2.lib.memoize      import memoize, clear_memo
from r2.lib.utils        import modhash, valid_hash, randstr 
from r2.lib.strings      import strings, plurals

from pylons import g
from pylons.i18n import _
import time, hashlib
from copy import copy

class AccountExists(Exception): pass
class NotEnoughKarma(Exception): pass

class Account(Thing):
    _data_int_props = Thing._data_int_props + ('link_karma', 'comment_karma',
                                               'report_made', 'report_correct',
                                               'report_ignored', 'spammer',
                                               'reported')
    _int_prop_suffix = '_karma'
    _defaults = dict(pref_numsites = 10,
                     pref_frame = False,
                     pref_newwindow = False,
                     pref_public_votes = False,
                     pref_kibitz = False,
                     pref_hide_ups = False,
                     pref_hide_downs = True,
                     pref_min_link_score = -2,
                     pref_min_comment_score = -2,
                     pref_num_comments = g.num_comments,
                     pref_lang = 'en',
                     pref_content_langs = ('en',),
                     pref_over_18 = False,
                     pref_compress = False,
                     pref_organic = True,
                     pref_show_stylesheets = True,
                     pref_url = '',
                     pref_location = '',
                     reported = 0,
                     report_made = 0,
                     report_correct = 0,
                     report_ignored = 0,
                     spammer = 0,
                     sort_options = {},
                     has_subscribed = False,
                     pref_media = 'subreddit',
                     share = {},
                     )

    def karma(self, kind, sr = None):
        from subreddit import Subreddit
        suffix = '_' + kind + '_karma'
        
        #if no sr, return the sum
        if sr is None:
            total = 0
            for k, v in self._t.iteritems():
                if k.endswith(suffix):
                    if kind == 'link':
                        try:
                            karma_sr_name = k[0:k.rfind(suffix)]
                            karma_sr = Subreddit._by_name(karma_sr_name)
                            multiplier = karma_sr.post_karma_multiplier
                        except NotFound:
                            multiplier = 1
                    else:
                        multiplier = 1
                    total += v * multiplier
            return total
        else:
            try:
                return getattr(self, sr.name + suffix)
            except AttributeError:
                #if positive karma elsewhere, you get min_up_karma
                if self.karma(kind) > 0:
                    return g.MIN_UP_KARMA
                else:
                    return 0

    def incr_karma(self, kind, sr, amt):
        prop = '%s_%s_karma' % (sr.name, kind)
        if hasattr(self, prop):
            return self._incr(prop, amt)
        else:
            default_val = self.karma(kind, sr)
            setattr(self, prop, default_val + amt)
            self._commit()

    @property
    def link_karma(self):
        return self.karma('link')

    @property
    def comment_karma(self):
        return self.karma('comment')

    @property
    def safe_karma(self):
        karma = self.link_karma + self.comment_karma
        return max(karma, 0) if karma > -1000 else karma

    def all_karmas(self):
        """returns a list of tuples in the form (name, link_karma,
        comment_karma)"""
        link_suffix = '_link_karma'
        comment_suffix = '_comment_karma'
        karmas = []
        sr_names = set()
        for k in self._t.keys():
            if k.endswith(link_suffix):
                sr_names.add(k[:-len(link_suffix)])
            elif k.endswith(comment_suffix):
                sr_names.add(k[:-len(comment_suffix)])
        for sr_name in sr_names:
            karmas.append((sr_name,
                           self._t.get(sr_name + link_suffix, 0),
                           self._t.get(sr_name + comment_suffix, 0)))
        karmas.sort(key = lambda x: x[1] + x[2])

        karmas.insert(0, ('total',
                          self.karma('link'),
                          self.karma('comment')))

        karmas.append(('old',
                       self._t.get('link_karma', 0),
                       self._t.get('comment_karma', 0)))

        return karmas

    def vote_cache_key(self, kind):
        """kind is 'link' or 'comment'"""
        return 'account_%d_%s_downvotes' % (self._id, kind)

    def check_downvote(self, vote_kind):
        """Checks whether this account has enough karma to cast a downvote.

        vote_kind is 'link' or 'comment' depending on the type of vote that's
        being cast.

        This makes the assumption that the user can't cast a vote for something
        on the non-current subreddit.
        """
        from r2.models.vote import Vote, Link, Comment

        def get_cached_downvotes(content_cls):
            kind = content_cls.__name__.lower()
            downvotes = g.cache.get(self.vote_cache_key(kind))
            if downvotes is None:
                vote_cls = Vote.rel(Account, content_cls)
                downvotes = len(list(vote_cls._query(Vote.c._thing1_id == self._id,
                                                          Vote.c._name == str(-1))))
                g.cache.set(self.vote_cache_key(kind), downvotes)
            return downvotes

        link_downvote_karma = get_cached_downvotes(Link) * c.current_or_default_sr.post_karma_multiplier
        comment_downvote_karma = get_cached_downvotes(Comment)
        karma_spent = link_downvote_karma + comment_downvote_karma

        karma_balance = self.safe_karma * 4
        vote_cost = c.current_or_default_sr.post_karma_multiplier if vote_kind == 'link' else 1
        if karma_spent + vote_cost > karma_balance:
            points_needed = abs(karma_balance - karma_spent - vote_cost)
            msg = strings.not_enough_downvote_karma % (points_needed, plurals.N_points(points_needed))
            raise NotEnoughKarma(msg)

    def incr_downvote(self, delta, kind):
        """kind is link or comment"""
        try:
            g.cache.incr(self.vote_cache_key(kind), delta)
        except ValueError, e:
            print 'Account.incr_downvote failed with: %s' % e

    def make_cookie(self, timestr = None, admin = False):
        if not self._loaded:
            self._load()
        timestr = timestr or time.strftime('%Y-%m-%dT%H:%M:%S')
        id_time = str(self._id) + ',' + timestr
        to_hash = ','.join((id_time, self.password, g.SECRET))
        if admin:
            to_hash += 'admin'
        return id_time + ',' + hashlib.sha1(to_hash).hexdigest()

    def needs_captcha(self):
        return self.safe_karma < 1

    def modhash(self, rand=None, test=False):
        return modhash(self, rand = rand, test = test)
    
    def valid_hash(self, hash):
        return valid_hash(self, hash)

    @classmethod
    @memoize('account._by_name')
    def _by_name_cache(cls, name, allow_deleted = False):
        #relower name here, just in case
        deleted = (True, False) if allow_deleted else False
        q = cls._query(lower(Account.c.name) == name.lower(),
                       Account.c._spam == (True, False),
                       Account.c._deleted == deleted)

        q._limit = 1
        l = list(q)
        if l:
            return l[0]._id

    @classmethod
    def _by_name(cls, name, allow_deleted = False):
        #lower name here so there is only one cache
        uid = cls._by_name_cache(name.lower(), allow_deleted)
        if uid:
            return cls._byID(uid, True)
        else:
            raise NotFound, 'Account %s' % name

    @property
    def friends(self):
        return self.friend_ids()

    def delete(self):
        self._deleted = True
        self._commit()
        clear_memo('account._by_name', Account, self.name.lower(), False)
        
        #remove from friends lists
        q = Friend._query(Friend.c._thing2_id == self._id,
                          Friend.c._name == 'friend',
                          eager_load = True)
        for f in q:
            f._thing1.remove_friend(f._thing2)

    @property
    def subreddits(self):
        from subreddit import Subreddit
        return Subreddit.user_subreddits(self)

    @property
    def draft_sr_name(self):
      return self.name + "-drafts"

    def recent_share_emails(self):
        return self.share.get('recent', set([]))

    def add_share_emails(self, emails):
        if not emails:
            return
        
        if not isinstance(emails, set):
            emails = set(emails)

        self.share.setdefault('emails', {})
        share = self.share.copy()

        share_emails = share['emails']
        for e in emails:
            share_emails[e] = share_emails.get(e, 0) +1
            
        share['recent'] = emails

        self.share = share
        
            
            


class FakeAccount(Account):
    _nodb = True


def valid_cookie(cookie):
    try:
        uid, timestr, hash = cookie.split(',')
        uid = int(uid)
    except:
        return (False, False)

    try:
        account = Account._byID(uid, True)
        if account._deleted:
            return (False, False)
    except NotFound:
        return (False, False)

    if cookie == account.make_cookie(timestr, admin = False):
        return (account, False)
    elif cookie == account.make_cookie(timestr, admin = True):
        return (account, True)
    return (False, False)

def valid_login(name, password):
    try:
        a = Account._by_name(name)
    except NotFound:
        return False

    if not a._loaded: a._load()
    return valid_password(a, password)

def valid_password(a, password):
    try:
        if a.password == passhash(a.name, password, ''):
            #add a salt
            a.password = passhash(a.name, password, True)
            a._commit()
            return a
        else:
            salt = a.password[:3]
            if a.password == passhash(a.name, password, salt):
                return a
    except AttributeError:
        return False

def passhash(username, password, salt = ''):
    if salt is True:
        salt = randstr(3)
    tohash = '%s%s %s' % (salt, username, password)
    if isinstance(tohash, unicode):
        # Force tohash to be a byte string so it can be hashed
        tohash = tohash.encode('utf8')
    return salt + hashlib.sha1(tohash).hexdigest()

def change_password(user, newpassword):
    user.password = passhash(user.name, newpassword, True)
    user._commit()
    return True

#TODO reset the cache
def register(name, password, email=None):
    try:
        a = Account._by_name(name)
        raise AccountExists
    except NotFound:
        a = Account(name = name,
                    password = passhash(name, password, True))
        if email:
            a.email = email

        a._commit()
            
        # Clear memoization of both with and without deleted
        clear_memo('account._by_name', Account, name.lower(), True)
        clear_memo('account._by_name', Account, name.lower(), False)
        return a

class Friend(Relation(Account, Account)): pass
Account.__bases__ += (UserRel('friend', Friend),)

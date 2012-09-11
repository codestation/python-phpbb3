#!/usr/bin/python3
# -*- coding: utf-8 -*-

import configparser
from phpbb import phpBB


class Settings(object):

    def __init__(self, configfile):
        self.config = configparser.ConfigParser(interpolation=None)
        self.config.read(configfile)

    def load(self, section, opts):
        try:
            for key in opts:
                try:
                    setattr(self, key, self.config.get(section, key))
                except configparser.NoOptionError:
                    setattr(self, key, self.config.get('default', key))

        except configparser.NoSectionError:
            print('The section "%s" does not exist' % section)
        except configparser.NoOptionError:
            print('The value for "%s" is missing' % key)
        else:
            return True
        return False

cfg_opts = ['host',
            'username',
            'password',
            'forum_id',
            'topic_id',
            'message',
            'join_msg',
            'extra_msg',
            'user_agent',
            'add_signature',
            'ban_tab']

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print(('Usage: %s <config-name> <profile url>' % sys.argv[0]))
        sys.exit(1)

    user = int(sys.argv[2])
    cfg = Settings('ban.cfg')
    if cfg.load(sys.argv[1], cfg_opts):
        forum = phpBB(cfg.host)
        forum.setUserAgent(cfg.user_agent)
        if forum.login(cfg.username, cfg.password):
            username = forum.getUsername(user)
            print('> Processing user %s\n' % username)
            posts = forum.searchPosts(user)
            post_info = None
            if posts:
                post_info = forum.queryPostInfo(posts[0]['f'], posts[0]['p'])
                forum.showPosts(posts)
                print()
                if input('Do you want to delete those posts? type "delete" to confirm: ') == 'delete':
                    print()

                    def callback_msg(post, msg):
                        print('Delete post #%i: %s' % (post, msg))

                    forum.deletePosts(posts, callback_msg)
                    print('> Done')
                else:
                    print('> Leaving posts untouched')
            else:
                print('> No results')

            if input('Do you want to ban this user? type "ban" to confirm: ') == 'ban':
                bantime = input('Ban time in minutes (0 or blank for permaban): ')
                if not bantime:
                    bantime = 0
                else:
                    bantime = int(bantime)
                reason = input('Reason: ')
                givereason = input('Given reason (leave blank to use the same as above): ')
                if input('Type "confirm" to confirm: ') == 'confirm':
                    forum.banUsers(int(cfg.ban_tab), [username], bantime, reason, givereason, user)

            if input('\nDo you want to post a report? type "post" to confirm: ') == 'post':
                base_msg = (cfg.message % (cfg.host + forum.profile_url % user, forum.getUsername(user)))
                full_msg = base_msg
                join_ip = forum.queryJoinIP(user)
                if join_ip:
                    full_msg += "\n" + cfg.join_msg % (join_ip['user_ip'], join_ip['country_name'])
                if post_info:
                    user_list = list()
                    if 'related_users' in post_info:
                        for u in post_info['related_users']:
                            user_list.append('[url=%s]%s[/url]' % (cfg.host + forum.profile_url % u['id'], u['user']))
                    usernames = ", ".join(user_list)
                    if not usernames:
                        usernames = "None"
                    full_msg += "\n" + cfg.extra_msg % (post_info['post_ip'], usernames)
                if cfg.add_signature:
                    full_msg += "\n\n" + "Ban-o-matic v0.4\n"

                full_msg = full_msg.replace('\\n', '\n')
                forum.postReply(int(cfg.forum_id), int(cfg.topic_id), full_msg)
        else:
            print('> Login failed')

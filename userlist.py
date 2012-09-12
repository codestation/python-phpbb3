#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from phpbb import phpBB


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(('Usage: %s <limit>' % sys.argv[0]))
        sys.exit(1)

    p = phpBB("http://mydomain.com/forum/")
    p.login("username", "password")
    limit = int(sys.argv[1])
    ulist = p.getUserList(limit)
    res = list()
    for u in ulist:
        r = p.queryJoinIP(u['id'])
        if r:
            r['user'] = u['name']
            r['id'] = u['id']
            r['posts'] = u['posts']
            r['group'] = u['group']
            res.append(r)
    p._table_print(res, [('id', 'ID'), ('user', 'User'), ('group', 'Group'), ('posts', 'Posts'),('user_ip', 'User IP'), ('country_name', 'Country name')])

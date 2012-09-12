#!/usr/bin/python3
# -*- coding: utf-8 -*-

#   Copyright 2012 codestation
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

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

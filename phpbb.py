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

import re
import codecs
import mimetypes
import http.cookiejar
from io import BytesIO
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlencode, urljoin
from urllib.request import build_opener, install_opener
from urllib.request import Request, HTTPCookieProcessor
from urllib.error import HTTPError


class phpBB(object):

    login_url = 'ucp.php?mode=login'
    post_url = 'viewtopic.php?f=%s&t=%i&p=%i#p%i'
    reply_url = 'posting.php?mode=reply&f=%i&t=%i'
    delete_url = 'posting.php?mode=delete&f=%i&p=%i'
    userpost_url = 'search.php?st=0&sk=t&sd=d&sr=posts&author_id=%i&start=%i'
    profile_url = 'memberlist.php?mode=viewprofile&u=%i'
    search_url = 'search.php?st=0&sk=t&sd=d&sr=posts&search_id=%s&start=%i'
    mcp_url = 'mcp.php?i=%i'
    member_url = 'memberlist.php?sk=c&sd=d&start=%i'
    notes_url = 'mcp.php?i=notes&mode=user_notes&u=%i'
    details_url = 'mcp.php?i=main&mode=post_details&f=%i&p=%i'

    search_type = ['newposts', 'active_topics', 'unreadposts', 'unanswered', 'egoposts']

    user_agent = 'Mozilla/5.0 (X11; Linux x86_64; rv:14.0) Gecko/20100101 Firefox/14.0.1'

    login_form_id = 'login'
    delete_form_id = 'confirm'
    reply_form_id = 'postform'
    ucp_form_id = 'ucp'
    mcp_ban_id = 'mcp_ban'

    def __init__(self, host):
        self.host = host
        self.jar = http.cookiejar.CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.jar))
        install_opener(self.opener)

    def _encode_multipart_formdata(self, fields, boundary=None):
        writer = codecs.lookup('utf-8')[3]
        body = BytesIO()

        if boundary is None:
            boundary = '----------b0uNd@ry_$'

        for name, value in getattr(fields, 'items')():
            body.write(bytes('--%s\r\n' % boundary, 'utf-8'))
            if isinstance(value, tuple):
                file, data = value
                writer(body).write('Content-Disposition: form-data; name="%s"; filename="%s"\r\n' % (name, file))
                body.write(bytes('Content-Type: %s\r\n\r\n' % (self._get_content_type(file)), 'utf-8'))
            else:
                data = value
                writer(body).write('Content-Disposition: form-data; name="%s"\r\n' % (name))
                body.write(bytes('Content-Type: text/plain\r\n\r\n', 'utf-8'))

            if isinstance(data, int):
                data = str(data)

            if isinstance(data, str):
                writer(body).write(data)
            else:
                body.write(data)

            body.write(bytes('\r\n', 'utf-8'))

        body.write(bytes('--%s--\r\n' % (boundary), 'utf-8'))

        content_type = 'multipart/form-data; boundary=%s' % boundary
        return body.getvalue(), content_type

    def _get_content_type(self, filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

    def _send_query(self, url, query, extra_headers=None, encode=True):
        headers = {'User-Agent': self.user_agent}

        if extra_headers:
            headers.update(extra_headers)

        if encode:
            data = bytes(urlencode(query), 'utf-8')
        else:
            if not isinstance(query, bytes):
                data = bytes(query, 'utf-8')
            else:
                data = query

        request = Request(url, data, headers)
        resp = self.opener.open(request)
        html = resp.read()
        self.opener.close()
        return html

    def _get_html(self, url):
        headers = {}
        headers['User-Agent'] = self.user_agent
        request = Request(url, headers=headers)
        resp = self.opener.open(request)
        soup = BeautifulSoup(resp)
        self.opener.close()
        return soup

    def _get_form_from_html(self, html, form_id):
        soup = BeautifulSoup(BytesIO(html))
        form = soup.find("form", id=form_id)
        return self._get_form_values(form)

    def _get_form(self, url, form_id):
        form = self._get_html(url).find("form", id=form_id)
        return self._get_form_values(form)

    def _get_form_values(self, soup):
        inputs = soup.find_all("input")
        values = {x['name']: x['value'] for x in inputs if x.get("value") and x.get('type') != "submit"}
        return {'values': values, 'action': soup['action']}

    def _get_posts(self, url, count=0):
        out = []
        res = self._get_html(url).find_all("ul", "searchresults")
        for ul in res:
            href = ul.li.a['href']
            o = urlparse(href)
            if o.query:
                out.append(dict([part.split('=') for part in o[4].split('&')]))
                for sub in out:
                    for key in sub:
                        sub[key] = int(sub[key])
                if count > 0 and len(out) >= count:
                    break
        return out

    def _get_users(self, url, count=0):
        out = []
        rows = self._get_html(url).find("table", "table1").find_all('tr')
        for row in rows:
            d = {}
            cols = row.find_all('td')
            if len(cols) > 1:
                user = cols[0].a.text
                query = urlparse(cols[0].a['href']).query
                user_id = query.split("&")[1].split("=")[1]

                if not cols[1].get("a"):
                    posts = cols[1].text
                else:
                    posts = cols[1].a.text

                join_date = cols[3].text
                d['name'] = user
                d['id'] = int(user_id)
                d['posts'] = posts
                d['join_date'] = join_date
                out.append(d)
            if count > 0 and len(out) >= count:
                break
        return out

    def _table_print(self, data, title_row):
        """data: list of dicts,
           title_row: e.g. [('name', 'Programming Language'), ('type', 'Language Type')]
        """
        max_widths = {}
        data_copy = [dict(title_row)] + list(data)
        for col in data_copy[0].keys():
            max_widths[col] = max([len(str(row[col])) for row in data_copy])
        cols_order = [tup[0] for tup in title_row]

        def custom_just(col, value):
            if type(value) == int:
                return str(value).rjust(max_widths[col])
            else:
                return value.ljust(max_widths[col])

        for row in data_copy:
            row_str = " | ".join([custom_just(col, row[col]) for col in cols_order])
            print("| %s |" % row_str)
            if data_copy.index(row) == 0:
                underline = "-+-".join(['-' * max_widths[col] for col in cols_order])
                print('+-%s-+' % underline)

    def login(self, username, password):
        form = self._get_form(urljoin(self.host, self.login_url), self.login_form_id)
        form['values']['username'] = username
        form['values']['password'] = password
        form['values']['login'] = 'Login'
        self._send_query(urljoin(self.host, self.login_url), form['values'])
        return self.isLogged()

    def isLogged(self):
        if self.jar != None:
            for cookie in self.jar:
                if re.search('phpbb3_.*_u', cookie.name) and cookie.value:
                    return True
        return False

    def getUsername(self, user_id):
        soup = self._get_html(urljoin(self.host, self.profile_url % user_id))
        dl = soup.find("form", id="viewprofile").find("dl", "left-box details")
        return dl.dd.span.text

    def showPosts(self, post_list):
        for post in post_list:
            print((self.host + self.post_url % (post['f'], post['t'], post['p'], post['p'])))

    def setUserAgent(self, agent):
        self.user_agent = agent

    def searchPosts(self, user_id):
        o = urlparse(self.profile_url % user_id)
        if o.query:
            params = dict([part.split('=') for part in o[4].split('&')])
            if 'u' in params:
                start = 0
                posts = []
                while True:
                    post_list = self._get_posts(urljoin(self.host, self.userpost_url % (int(params['u']), start)))
                    if not post_list:
                        break
                    posts.extend(post_list)
                    start += 10
                return posts

    def getNewPosts(self, search_id, max_count):
        if not search_id in self.search_type:
            print('Invalid search type')
            return
        start = 0
        posts = []
        while start < max_count:
            if (start + 10) < max_count:
                count = 0
            else:
                count = max_count - start
            post_list = self._get_posts(urljoin(self.host, self.search_url % (search_id, start)), count)
            if not post_list:
                break
            posts.extend(post_list)
            start += 10
        return posts

    def deletePosts(self, post_list, callback=None):
        for post in post_list:
            url = urljoin(self.host, self.delete_url % (post['f'], post['p']))
            form = self._get_form(url, self.delete_form_id)
            form['values']['confirm'] = 'Yes'
            queryurl = urljoin(self.host, form['action'])
            html = self._send_query(queryurl, form['values'], {'Referer': url})
            soup = BeautifulSoup(BytesIO(html))
            resp = soup.find("div", id="message")
            if callback and resp:
                callback(post['p'], resp.p.find(text=True, recursive=False))

    def postReply(self, forum, topic, message):
        url = urljoin(self.host, self.reply_url % (forum, topic))
        try:
            form = self._get_form(url, self.reply_form_id)
            form['values']['message'] = message
            form['values']['post'] = 'Submit'
            body, content_type = self._encode_multipart_formdata(form['values'])
            headers = {'Content-Type': content_type}

            """ wait at least 2 seconds so phpBB let us post """
            sleep(2)

            html = self._send_query(url, body, headers, encode=False)
            soup = BeautifulSoup(BytesIO(html))
            resp = soup.find("div", id="message")
            if resp:
                print('>>> %s' % resp.p.find(text=True, recursive=False))
            else:
                print('>>> no message')
        except HTTPError as e:
            print('\n>>> Error %i: %s' % (e.code, e.msg))

    def changeAvatar(self, imagefile):
        url = urljoin(self.host, self.profile_url % 'avatar')
        form = self._get_form(url, self.ucp_form_id)
        form['values']['uploadfile'] = (imagefile, open(imagefile, 'rb').read())
        form['values']['submit'] = 'Submit'
        body, content_type = self._encode_multipart_formdata(form['values'])
        headers = {'Content-Type': content_type, 'Content-length': str(len(body)), 'Referer': url}

        """ wait at least 2 seconds so phpBB let us post """
        sleep(2)

        html = self._send_query(url, body, headers, encode=False)
        soup = BeautifulSoup(BytesIO(html))
        error_msg = soup.find("div", id=self.ucp_form_id).find("p", "error").text
        if error_msg:
            print('Error: %s' % error_msg)
        resp = soup.find("div", id="message")
        if resp:
            print('>>> %s' % resp.p.text)
        else:
            print('>>> no message')

    def banUsers(self, tab_id, user_list, length, reason, givereason=None, user_id=None):
        url = urljoin(self.host, self.mcp_url % tab_id)
        if user_id:
            url += "&u=%s" % user_id
        form = self._get_form(url, self.mcp_ban_id)
        form['values']['ban'] = "\r\n".join(user_list)
        form['values']['banlength'] = str(length)
        form['values']['banlengthother'] = ""
        form['values']['banreason'] = reason
        if givereason:
            form['values']['bangivereason'] = givereason
        else:
            form['values']['bangivereason'] = reason
        form['values']['banexclude'] = "0"
        form['values']['bansubmit'] = 'Submit'
        referer = urljoin(self.host, form['action'])
        html = self._send_query(referer, form['values'], {'Referer': url})
        form = self._get_form_from_html(html, "confirm")
        form['values']['confirm'] = 'Yes'
        url = urljoin(self.host, form['action'])

        html = self._send_query(url, form['values'], {'Referer': referer})
        soup = BeautifulSoup(BytesIO(html))
        resp = soup.find("div", id="message")
        if resp:
            print('>>> %s' % resp.p.find(text=True, recursive=False))
        else:
            print('>>> no message')

    def getUserList(self, limit):
        start = 0
        users = []
        while start < limit:
            if (start + 25) < limit:
                count = 0
            else:
                count = limit - start
            user_list = self._get_users(urljoin(self.host, self.member_url % start), count)
            if not user_list:
                break
            users.extend(user_list)
            start += 25
        return users

    def queryPostInfo(self, forum_id, post_id):
        url = urljoin(self.host, self.details_url % (forum_id, post_id))
        soup = self._get_html(url)
        div = soup.find("div", id="ip").div
        post_ip = div.p.a.text
        tr = div.find("table", "table1").tbody.find_all("tr")
        related_users = list()
        for item in tr:
            if item.td.a:
                query = urlparse(item.td.a['href']).query
                user_id = int(query.split('&')[1].split('=')[1])
                related_users.append({'user': item.td.a.text, 'id': user_id})
            #else:
            #    related_users.append(item.td.text)
        return {'post_ip': post_ip, 'related_users': related_users}

    def queryJoinIP(self, user_id, geoip_path=None):
        url = urljoin(self.host, self.notes_url % user_id)
        soup = self._get_html(url)
        form = soup.find("form", id="mcp")
        tr = form.find("table", "table1").tbody.find_all("tr")
        reports = list()
        for item in tr:
            td = item.find_all("td")
            if len(td) > 1:
                name = td[0].text
                ip = td[1].text
                reports.append({'report_by': name, 'user_ip': ip})

        if reports:
            filtered = [x for x in reports if x['report_by'] == "Anonymous"]
            if filtered:
                res = filtered[0]
                try:
                    import pygeoip  # @UnresolvedImport
                except ImportError:
                    res['country_name'] = "No GeoIP loaded"
                    return res

                if not geoip_path:
                    geoip_path = '/usr/share/GeoIP/GeoIP.dat'
                gi = pygeoip.GeoIP(geoip_path, pygeoip.MEMORY_CACHE)
                res['country_name'] = gi.country_name_by_addr(res['user_ip'])
                return res

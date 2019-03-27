# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 18:49:25 2019

@author: Михаил
"""
import webbrowser
from urllib.parse import urljoin
import sys
from threading import Timer

import click
import requests
from bs4 import BeautifulSoup
from bottle import route, run

TM_POSTFIX_HTML = u'&trade;'
WORD_LENGTH = 6


class ProxyHabr:
    """Simple configurable proxy bottle server."""

    def __init__(self, url, port):
        """Set url, port and routes"""
        self.url = url
        self.port = port

        # Setup routes
        route('/')(self.root)
        route('/<path:path>')(self.sub)

    def trademark(self, response):
        """Trademark all the 6 letter words."""
        if response.status_code == requests.codes.ok:

            # Update hrefs to point to localhost:port
            soup = BeautifulSoup(response.content, 'html.parser')
            for a in soup.find_all('a'):
                try:
                    domain = urljoin.urljoin(self.url).netloc
                    if domain in a['href']:
                        a['href'] = a['href'].replace(
                            domain, u'localhost:{0:d}'.format(self.port))
                except KeyError:
                    pass

            # Urgh...
            encoding = response.encoding if response.encoding else 'utf-8'
            contents = unicode(str(soup), encoding)

            # Find all 6 letter words (try to ignore scripts and styles)
            words = []
            for div in soup.find_all('div'):
                for word in div.text.split(u' '):
                    if len(word) == WORD_LENGTH:
                        words.append(word)

            # Trademark EVERYTHING
            for word in set(words):
                contents = contents.replace(word, word + TM_POSTFIX_HTML)

            return contents

        # On 404 and others
        else:
            return 'Cannot proxy that!'

    def root(self):
        """Process base route."""
        return self.trademark(requests.get(self.url))

    def sub(self, path):
        """Process all the sub-routes."""
        return self.trademark(
            requests.get(urljoin.urljoin(self.url, path)))

    def run(self):
        """Run bottle server."""
        run(host='localhost', port=self.port)


@click.command()
@click.option('--url', default='http://habrahabr.ru',
              prompt='Url to proxy', help='Url to process.')
@click.option('--port', default=8232,
              prompt='Port to serve on', help='Port to listen on.')
@click.option('--browse', is_flag=True, default=False,
              prompt='Launch default browser?', help='Should open browser.')
def serve(url, port, browse):
    """
    Reverse-proxy provided url and modify page contents in an amusing manner."""
    # Check if provided url is valid
    if not urljoin.urljoin(url).netloc:
        sys.exit('Invalid url. Please specify something like http://yada.yada')

    # Launch browser?
    if browse:
        t = Timer(1.0, lambda: webbrowser.open_new_tab(
            'http://localhost:{0:d}'.format(port)))
        t.start()

    # Run proxy server
    ProxyHabr(url, port).run()


if __name__ == '__main__':
    serve()

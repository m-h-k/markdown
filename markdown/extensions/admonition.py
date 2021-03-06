"""
Admonition extension for Python-Markdown
========================================

Adds rST-style HTMLBOOK_ADMONITIONS. Inspired by [rST][] feature with the same name.

[rST]: http://docutils.sourceforge.net/docs/ref/rst/directives.html#specific-HTMLBOOK_ADMONITIONS  # noqa

See <https://Python-Markdown.github.io/extensions/admonition>
for documentation.

Original code Copyright [Tiago Serafim](http://www.tiagoserafim.com/).

All changes Copyright The Python Markdown Project

License: [BSD](http://www.opensource.org/licenses/bsd-license.php)

"""

from __future__ import absolute_import
from __future__ import unicode_literals
from . import Extension
from ..blockprocessors import BlockProcessor
from ..util import etree
import re


HTMLBOOK_ADMONITIONS = ['note', 'warning', 'tip', 'caution', 'important']

class AdmonitionExtension(Extension):
    """ Admonition extension for Python-Markdown. """

    def __init__(self, **kwargs):
        self.config = {
            "htmlbook": [False,
                          "Whether to product HTMLBook compliant html - "
                          "Defaults to `False`."],
        }

        super(AdmonitionExtension, self).__init__(**kwargs)

    def extendMarkdown(self, md):
        """ Add Admonition to Markdown instance. """
        md.registerExtension(self)

        processor = AdmonitionProcessor(md.parser, self.getConfigs())

        md.parser.blockprocessors.register(processor, 'admonition', 105)


class AdmonitionProcessor(BlockProcessor):

    CLASSNAME = 'admonition'
    CLASSNAME_TITLE = 'admonition-title'
    RE = re.compile(r'(?:^|\n)!!! ?([\w\-]+(?: +[\w\-]+)*)(?: +"(.*?)")? *(?:\n|$)')
    RE_SPACES = re.compile('  +')

    def __init__(self, md, config):
        super(AdmonitionProcessor, self).__init__(md)

        self.htmlbook = config["htmlbook"]

    def test(self, parent, block):
        sibling = self.lastChild(parent)
        if self.htmlbook:
            return self.RE.search(block) or \
                (block.startswith(' ' * self.tab_length) and sibling is not None and
                sibling.get('data-type', '') in HTMLBOOK_ADMONITIONS)
        else:
            return self.RE.search(block) or \
                (block.startswith(' ' * self.tab_length) and sibling is not None and
                sibling.get('class', '').find(self.CLASSNAME) != -1)

    def run(self, parent, blocks):
        sibling = self.lastChild(parent)
        block = blocks.pop(0)
        m = self.RE.search(block)

        if m:
            block = block[m.end():]  # removes the first line

        block, theRest = self.detab(block)

        if m:
            klass, title = self.get_class_and_title(m)
            div = etree.SubElement(parent, 'div')
            if self.htmlbook:
                if not klass in HTMLBOOK_ADMONITIONS:
                    klass = 'note'
                div.set('data-type', klass)
                if title:
                    p = etree.SubElement(div, 'h1')
                    p.text = title
            else:
                div.set('class', '%s %s' % (self.CLASSNAME, klass))
                if title:
                    p = etree.SubElement(div, 'p')
                    p.text = title
                    p.set('class', self.CLASSNAME_TITLE)
        else:
            div = sibling

        self.parser.parseChunk(div, block)

        if theRest:
            # This block contained unindented line(s) after the first indented
            # line. Insert these lines as the first block of the master blocks
            # list for future processing.
            blocks.insert(0, theRest)

    def get_class_and_title(self, match):
        klass, title = match.group(1).lower(), match.group(2)
        klass = self.RE_SPACES.sub(' ', klass)
        if title is None:
            # no title was provided, use the capitalized classname as title
            # e.g.: `!!! note` will render
            # `<p class="admonition-title">Note</p>`
            title = klass.split(' ', 1)[0].capitalize()
        elif title == '':
            # an explicit blank title should not be rendered
            # e.g.: `!!! warning ""` will *not* render `p` with a title
            title = None
        return klass, title


def makeExtension(**kwargs):  # pragma: no cover
    return AdmonitionExtension(**kwargs)

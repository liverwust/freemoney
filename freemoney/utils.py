from io import BytesIO
from lxml import etree
import re


def parse_formset_management_form(page_content):
    """Extract the <input> values required for Django formset postback."""
    postdata = {}
    name_re = re.compile(r'^([^-]*)-(TOTAL|INITIAL|MIN_NUM|MAX_NUM)_FORMS$')
    ET = etree.parse(BytesIO(page_content), etree.HTMLParser())
    for element in ET.findall(r".//form//input[@type='hidden']"):
        match = name_re.match(element.get('name'))
        if match != None:
            form_name, field_meaning = match.group(1), match.group(2)
            postdata[match.group(0)] = element.get('value')
    return postdata

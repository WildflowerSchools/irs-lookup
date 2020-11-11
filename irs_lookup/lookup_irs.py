import traceback
import sys
import requests
import re
from pdf2image import convert_from_bytes
import pandas as pd
import math
import itertools
import io
from google.cloud import vision
import dateparser
import csv
import bs4
from PIL import Image
Image.MAX_IMAGE_PIXELS = 1000000000

#import pytesseract


# def csv_writeline(file, line):
#     with open(file, 'a', newline='') as f:
#         w = csv.writer(f, delimiter=',')
#         w.writerow(line)

# in_file = sys.argv[1]
# out_file = sys.argv[2]

#csv_writeline(out_file, header)


# with open(in_file) as f:
#     f = f.readlines()


def image_to_byte_array(image: Image, format=None):
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=format or image.format)
    imgByteArr = imgByteArr.getvalue()
    return imgByteArr


def load_990(url):
    pdf_request = requests.get(url)

    # After downloading PDF, grab a single page with single_file=True
    # Also, DPI is very high, but needs to be to get consistent OCR results
    pages = convert_from_bytes(pdf_request.content, dpi=400, single_file=True)
    page_1 = pages[0]

    # The info we're after is at the top of the report, crop it out
    w, h = page_1.size
    page_1_cropped = page_1.crop((math.ceil(
        w * .04), math.ceil(h * .07), w - math.ceil(w * .09), math.ceil(h * .20)))
    # page_1_cropped.save("/Users/btalberg/Projects/WildFlower/irs-990-lookup/example.ppm")
    img_byte_arr = image_to_byte_array(page_1_cropped, format='PPM')

    #page_1_cropped = page_1_cropped.convert('JPEG')
    # text = str(pytesseract.image_to_string(page_1_cropped))
    # text = text.replace('-\n', '')

    client = vision.ImageAnnotatorClient()

    # image_to_byte_array(img_byte_arr)
    response = client.document_text_detection(
        image=vision.Image(content=img_byte_arr))

    document = response.full_text_annotation

    # Zero in on the line containing start/end dates for 990 fiscal year and
    # crop again
    needle = None
    for page in document.pages:
        for block in page.blocks:
            for paragraph in block.paragraphs:
                nested_text = list(
                    map(lambda w: list(map(lambda s: s.text, w.symbols)), paragraph.words))
                flattened_text = list(
                    itertools.chain.from_iterable(nested_text))
                text = "".join(flattened_text).lower()

                if "calendaryear" in text:
                    needle = paragraph
                    break

            if needle is not None:
                break

        if needle is not None:
            break

    w, h = needle.bounding_box.vertices[2].x - \
        needle.bounding_box.vertices[0].x, needle.bounding_box.vertices[2].y - \
        needle.bounding_box.vertices[0].y
    left, top = needle.bounding_box.vertices[0].x - math.ceil(
        w * .05), needle.bounding_box.vertices[0].y - math.ceil(h * .2)
    right, bottom = page_1_cropped.width, needle.bounding_box.vertices[2].y + math.ceil(
        h * .2)

    page_1_cropped = page_1_cropped.crop((left, top, right, bottom))
    # page_1_cropped.save("/Users/btalberg/Projects/WildFlower/irs-990-lookup/example2.ppm")
    img_byte_arr = image_to_byte_array(page_1_cropped, format='PPM')

    response = client.document_text_detection(
        image=vision.Image(content=img_byte_arr))

    text = response.text_annotations[0].description
    return text


def lookup_990s_by_ein(ein):
    ein = ein.strip()

    columns = [
        'ein',
        'name',
        'tax_period',
        'return_id',
        'return_type',
        'filing_name',
        'filing_url',
        'filing_date_start',
        'filing_date_end']
    irs_returns = pd.DataFrame(columns=columns)

    if len(ein) < 9:  # EIN has to be at least 9 characters
        return irs_returns
    else:
        print("Loading {}'s 990 data".format(ein))

        url = 'https://apps.irs.gov/app/eos/displayCopyOfReturns.do?dispatchMethod=displayCORInfo&CopyOfReturnId=1211739&ein={}&country=US&deductibility=all&dispatchMethod=searchCopyOfReturns&isDescending=false&city=&ein1={}&postDateFrom=&exemptTypeCode=al&submitName=Search&sortColumn=orgName&totalResults=1&names=&resultsPerPage=25&indexOfFirstRow=0&postDateTo=&state=All+States'.format(
            ein,
            ein)
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.text, 'html.parser')

        # with open("page.html", "w") as html_file:
        #     html_file.write(str(soup))

        rows = soup.find_all(id=re.compile(r"copyOfReturns\d*"))
        try:
            for row in rows:
                returns = row.find_all(['b', 'br', 'span', 'a'])

                def flattened_details(tags):
                    values = []
                    for tag in tags:
                        if not isinstance(tag, bs4.NavigableString) and len(
                                list(tag.children)) > 0:
                            if isinstance(tag, bs4.Tag) and tag.name == 'a':
                                values.append(
                                    'https://apps.irs.gov{}'.format(tag.attrs['href']))
                            values += flattened_details(list(tag.children))
                        else:
                            if isinstance(tag, bs4.NavigableString):
                                value = str(tag).strip()
                            else:
                                value = tag.getText().strip()

                            if value != "":
                                values.append(value)
                    return values

                details = flattened_details(returns)

                r_name, r_tax_period, r_return_id, r_return_type, r_filing_name, r_filing_url, r_filing_date_start, r_filing_date_end = None, None, None, None, None, None, None, None
                ii = 0
                while ii < len(details):
                    if details[ii].lower() == 'organization name:':
                        r_name = details[ii + 1]
                        ii += 1
                        continue

                    elif r_tax_period is None and details[ii].lower() == 'tax period:':
                        r_tax_period = details[ii + 1]
                        ii += 1
                        continue

                    elif details[ii].lower() == 'return id:':
                        r_return_id = details[ii + 1]
                        ii += 1
                        continue

                    elif details[ii].lower() == 'copy of return:':
                        r_filing_url = details[ii + 1]
                        r_filing_name = details[ii + 2]
                        ii += 2
                        continue

                    elif r_return_type is None and details[ii].lower() == 'return type:':
                        r_return_type = details[ii + 1]
                        ii += 1
                        continue

                    ii += 1

                if r_filing_url is not None:
                    print(
                        "Fetching {}'s '{}' (ReturnId={})".format(
                            ein, r_filing_name, r_return_id))
                    text_990 = load_990(r_filing_url)

                    date_reg = r"((?:(?:\d{1,2}|j(?:an(?:uary)?|(?:u(?:ne|n|ly|l))))|(?:feb(?:ruary)?)|(?:mar(?:ch)?)|(?:may)|(?:a(?:pr(?:il)?|ug(?:ust)?))|(?:(?:sep(?:t)?|nov|dec)(?:em(?:ber)?)?)|(?:oct(?:ober|ob)?))).*?(\d{1,2}).*?(\d{2}\W\d{2}|(?:\d{4}|\d{2}[^\d\%]))"

                    filing_date_beginning_regex = re.compile(
                        "beg(?:i?n?n?i?n?g?)?.*?" + date_reg, flags=re.IGNORECASE | re.S)
                    filing_date_ending_regex = re.compile(
                        r"(?:^|\s){1}endi(?:n?g?)?.*?" + date_reg, flags=re.IGNORECASE | re.S)

                    filing_date_beginning_match = re.search(
                        filing_date_beginning_regex, text_990)
                    if filing_date_beginning_match is not None:
                        r_filing_date_start = "{} {} {}".format(
                            filing_date_beginning_match.group(1).strip(),
                            filing_date_beginning_match.group(2).strip(),
                            filing_date_beginning_match.group(3).strip())
                        r_filing_date_start = dateparser.parse(
                            r_filing_date_start).strftime('%m-%d-%Y')

                    filing_date_ending_match = re.search(
                        filing_date_ending_regex, text_990)
                    if filing_date_ending_match is not None:
                        r_filing_date_end = "{} {} {}".format(
                            filing_date_ending_match.group(1).strip(),
                            filing_date_ending_match.group(2).strip(),
                            filing_date_ending_match.group(3).strip())
                        r_filing_date_end = re.sub(
                            r"\s+", " ", r_filing_date_end)
                        r_filing_date_end = dateparser.parse(
                            r_filing_date_end).strftime('%m-%d-%Y')

                row = pd.DataFrame([[ein,
                                     r_name,
                                     r_tax_period,
                                     r_return_id,
                                     r_return_type,
                                     r_filing_name,
                                     r_filing_url,
                                     r_filing_date_start,
                                     r_filing_date_end]],
                                   columns=columns)
                # row = {
                #     'ein': ein,
                #     'name': r_name,
                #     'tax_period': r_tax_period,
                #     'return_id': r_return_id,
                #     'return_type': r_return_type,
                #     'filing_name': r_filing_name,
                #     'filing_url': r_filing_url,
                #     'filing_date_start': dateparser.parse(r_filing_date_start).strftime('%m-%d-%Y'),
                #     'filing_date_end': dateparser.parse(r_filing_date_end).strftime('%m-%d-%Y')
                # }
                irs_returns = irs_returns.append(row)

            print("Finished {}".format(ein))
        except Exception as err:
            print(ein, 'error')
            traceback.print_exc()

            print(err)

            return irs_returns

        return irs_returns


def lookup_990s(eins=[]):
    irs_returns = None
    for ein in eins:
        df = lookup_990s_by_ein(ein)
        if df is None:
            continue

        if irs_returns is None:
            irs_returns = df
        else:
            irs_returns = irs_returns.append(df)

    return irs_returns

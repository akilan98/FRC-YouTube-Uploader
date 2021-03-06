#!/usr/bin/python

import os
import re
import sys
import time
import random
import datetime as dt

import tbapy
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from consts import *

"""Utility Functions"""


def convert_bytes(num):
    for x in sizes:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0


def file_size(path):
    file_info = os.stat(path)
    return convert_bytes(file_info.st_size)


"""YouTube Title Generators"""


def quals_yt_title(options):
    return options.title.format(options.mnum)


def quarters_yt_title(options):
    mnum = options.mnum
    if mnum <= 8:
        return options.ename + " - " + QUARTER.format(mnum)
    elif mnum <= 12:
        mnum -= 8
        return options.ename + " - " + QUARTERT.format(mnum)
    else:
        raise ValueError("options.mnum must be within 1 and 12")


def semis_yt_title(options):
    mnum = options.mnum
    if mnum <= 15 and options.ein:
        return options.ename + " - Einstein Round Robin {}".format(mnum)
    if mnum <= 4 and not options.ein:
        return options.ename + " - " + SEMI.format(mnum)
    elif mnum <= 6 and not options.ein:
        mnum -= 4
        return options.ename + " - " + SEMIT.format(mnum)
    else:
        raise ValueError("options.mnum must be within 1 and 6")


def finals_yt_title(options):
    if options.ein:
        return options.ename + " - Einstein Final {}".format(options.mnum)
    else:
        return options.ename + " - " + FINALS.format(options.mnum)


def ceremonies_yt_title(options):
    title = None
    if options.ceremonies is 1:
        if not options.eday:
            title = options.ename + " - " + \
                "{} Opening Ceremonies".format(options.day)
        else:
            title = options.ename + " - " + \
                "Day {} Opening Ceremonies".format(options.eday)
    elif options.ceremonies is 2:
        title = options.ename + " - " + "Alliance Selection"
    elif options.ceremonies is 3:
        if not options.eday:
            title = options.ename + " - " + "Closing Ceremonies"
        else:
            title = options.ename + " - " + \
                "Day {} Closing Ceremonies".format(options.eday)
    return title


"""File Location Functions"""


def quals_filename(options):
    file = None
    for f in options.files:
        fl = f.lower()
        if all([" " + str(options.mnum) + "." in fl and any(k in fl for k in ("qual", "qualification", "qm"))]):
            file = f
    if file is None:
        raise Exception("No File Found")
    return file


def quarters_filename(options):
    file = None
    if 1 <= options.mnum <= 8:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in (
                "quarter", "final", " " + str(options.mnum) + ".")):
                if "tiebreak" not in fl:
                    file = f
    elif 9 <= options.mnum <= 12:
        mnum = options.mnum - 8
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("quarter", "tiebreak", "final", " " + str(mnum) + ".")):
                file = f
    if file is None:
        raise Exception("No File Found")
    return file


def semis_filename(options):
    file = None
    if options.mnum <= 15 and options.ein:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("einstein", " " + str(options.mnum) + ".")):
                if "final" not in fl:
                    file = f
    if options.mnum <= 4 and not options.ein:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("semi", "final", " " + str(options.mnum) + ".")):
                if "tiebreak" not in fl:
                    file = f
    elif options.mnum <= 6 and not options.ein:
        mnum = options.mnum - 4
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("semi", "tiebreak", "final", " " + str(mnum) + ".")):
                file = f
    if file is None:
        raise Exception("No File Found")
    return file


def finals_filename(options):
    file = None
    if options.mnum <= 2 and options.ein:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("final", "einstein", " " + str(options.mnum) + ".") and "match" not in fl):
                file = f
    elif options.mnum <= 2 and not options.ein:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("final", " " + str(options.mnum) + ".")):
                if all(k not in fl for k in ("quarter", "semi")) and "tiebreak" not in fl:
                    file = f
    elif options.mnum >= 3:
        for f in options.files:
            fl = f.lower()
            if "final" in fl and any(k in fl for k in ("tiebreak", " " + str(options.mnum) + ".")):
                if all(k not in fl for k in ("quarter", "semi")):
                    file = f
    if file is None:
        raise Exception("No File Found")
    return file


def ceremonies_filename(options):
    file = None
    if options.ceremonies is 1:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("opening", "ceremon")):
                if any(k in fl for k in (options.day.lower(), "day {}".format(options.eday))):
                    file = f
    elif options.ceremonies is 2:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("alliance", "selection")):
                file = f
    elif options.ceremonies is 3:
        for f in options.files:
            fl = f.lower()
            if any(k in fl for k in ("closing", "award")) and "ceremon" in fl:
                if any(k in fl for k in (options.day.lower(), "day {}".format(options.eday))):
                    file = f
    if file is None:
        raise Exception("No File Found")
    return file


def create_names(options):
    if options.ceremonies is 0:
        fname = {
            "qm": quals_filename,
            "qf": quarters_filename,
            "sf": semis_filename,
            "f1m": finals_filename,
        }
        yt = {
            "qm": quals_yt_title,
            "qf": quarters_yt_title,
            "sf": semis_yt_title,
            "f1m": finals_yt_title,
        }
        try:
            return fname[options.mtype](options), yt[options.mtype](options)
        except KeyError:
            print options.mtype
    else:
        return ceremonies_filename(options), ceremonies_yt_title(options)


"""Match Code Generators"""


def quals_match_code(mtype, mnum):
    match_code = str(mtype) + str(mnum)
    return match_code


def quarters_match_code(mtype, mnum):
    match_set = str(mnum % 4)
    match_set = "4" if match_set == "0" else match_set
    match_code = mtype + match_set
    if mnum <= 4:
        match_code += "m1"
    elif mnum <= 8:
        match_code += "m2"
    elif mnum <= 12:
        match_code += "m3"
    else:
        raise ValueError("Match Number can't be larger than 12")
    return match_code


def semis_match_code(mtype, mnum):
    match_set = str(mnum % 2)
    match_set = "2" if match_set == "0" else match_set
    match_code = mtype + match_set
    if mnum <= 2:
        match_code += "m1"
    elif mnum <= 4:
        match_code += "m2"
    elif mnum <= 6:
        match_code += "m3"
    else:
        raise ValueError("Match Number can't be larger than 6")
    return match_code


def finals_match_code(mtype, mnum):
    match_code = mtype + str(mnum)
    return match_code


def get_match_code(mtype, mnum, mcode):
    if any(k == mcode for k in ("", "0")):
        switcher = {
            "qm": quals_match_code,
            "qf": quarters_match_code,
            "sf": semis_match_code,
            "f1m": finals_match_code,
        }
        return switcher[mtype](mtype, mnum)
    print "Uploading as {}".format(mcode)
    return mcode.lower()


"""Data Compliation and Adjustment Functions"""


def get_match_results(event_key, match_key):
    tba = tbapy.TBA(
        "wvIxtt5Qvbr2qJtqW7ZsZ4vNppolYy0zMNQduH8LdYA7v2o1myt8ZbEOHAwzRuqf")
    match_data = tba.match("_".join([event_key, match_key]))
    if match_data is None:
        raise ValueError("""{} {} does not exist on TBA. Please use a match that exists""".format(
            event_key, match_key))
    blue_data, red_data = parse_data(match_data)
    while (blue_data[0] == -1 or red_data[0] == -1):
        print "Waiting 1 minute for TBA to update scores"
        time.sleep(60)
        match_data = event_get(event_key).get_match(match_key)
        blue_data, red_data = parse_data(match_data)
    return blue_data, red_data


def parse_data(match_data):
    blue = match_data['alliances']['blue']['team_keys']
    red = match_data['alliances']['red']['team_keys']
    blue_data = [match_data['alliances']['blue']['score']]
    red_data = [match_data['alliances']['red']['score']]
    for team in blue:
        blue_data.append(team[3:])
    for team in red:
        red_data.append(team[3:])
    return blue_data, red_data


def tba_results(options):
    mcode = get_match_code(options.mtype, options.mnum, options.mcode)
    blue_data, red_data = get_match_results(options.ecode, mcode)
    return blue_data, red_data, mcode


def create_description(options, blue1, blue2, blue3, blueScore, red1, red2, red3, redScore):
    if all(x == -1 for x in (red1, red2, red3, redScore, blue1, blue2, blue3, blueScore)):
        return NO_TBA_DESCRIPTION.format(ename=options.ename, team=options.prodteam, twit=options.twit, fb=options.fb, weblink=options.weblink)
    try:
        return options.description.format(ename=options.ename, team=options.prodteam,
                                          red1=red1, red2=red2, red3=red3, redscore=redScore, blue1=blue1, blue2=blue2, blue3=blue3, bluescore=blueScore,
                                          ecode=options.ecode, twit=options.twit, fb=options.fb, weblink=options.weblink)
    except TypeError, e:
        print e
        return options.description


def tiebreak_mnum(mnum, mtype):
    switcher = {
        "qm": mnum,
        "qf": mnum + 8,
        "sf": mnum + 4,
        "f1m": 3,
    }
    return switcher[mtype]


"""Additional YouTube Functions"""


def upload_multiple_videos(youtube, spreadsheet, options):
    while options.mnum <= options.end:
        try:
            conclusion = initialize_upload(youtube, spreadsheet, options)
            if conclusion == "FAILED":
                print "Try again"
                return
            print conclusion
            options.then = dt.datetime.now()
            options.mnum = options.mnum + 1
            options.file, options.yttitle = create_names(options)
            while options.file is None and options.mnum <= options.end:
                print "{} Match {} is missing".format(options.mtype.upper(), options.mnum)
                options.mnum = options.mnum + 1
                options.file, options.yttitle = create_names(options)
        except HttpError, e:
            print "An HTTP error {} occurred:\n{}\n".format(e.resp.status, e.content)
    print "All matches have been uploaded"


def update_thumbnail(youtube, video_id, thumbnail):
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=thumbnail
    ).execute()
    print "Thumbnail added to video {}".format(video_id)


def add_to_playlist(youtube, videoID, playlistID):
    if type(videoID) is list:  # Recursively add videos if videoID is list
        for vid in videoID:
            add_video_to_playlist(youtube, vid, playlistID)
    else:
        youtube.playlistItems().insert(
            part="snippet",
            body={
                'snippet': {
                    'playlistId': playlistID,
                    'resourceId': {
                        'kind': 'youtube#video',
                        'videoId': videoID
                    }
                }
            }
        ).execute()
        print "Added to playlist"


def attempt_retry(error, retry, max_retries):
    if error is not None:
        print error
        retry += 1
        if retry > max_retries:
            exit("No longer attempting to retry.")

        max_sleep = 2 ** retry
        sleep_seconds = random.random() * max_sleep
        print "Sleeping {} seconds and then retrying...".format(sleep_seconds)
        time.sleep(sleep_seconds)
        error = None


"""TBA Trusted API"""


def post_video(token, secret, match_video, match_key):
    trusted_auth = {'X-TBA-Auth-Id': "", 'X-TBA-Auth-Sig': ""}
    trusted_auth['X-TBA-Auth-Id'] = token
    m = md5()
    request_path = "/api/trusted/v1/event/{}/match_videos/add".format(
        match_key)
    concat = secret + request_path + str(request_body)
    m.update(concat)
    md5 = m.hexdigest()
    trusted_auth['X-TBA-Auth-Sig'] = str(md5)

    url = "http://thebluealliance.com/api/trusted/v1/event/{}/match_videos/add"
    url_str = url.format(match_key)
    if trusted_auth['X-TBA-Auth-Id'] == "" or trusted_auth['X-TBA-Auth-Sig'] == "":
        raise Exception("""An auth ID and/or auth secret required. 
            Please use set_auth_id() and/or set_auth_secret() to set them""")
    r = s.post(url_str, data=match_video, headers=trusted_auth)

    while "405" in r.content:
        print "Failed to POST to TBA"
        print "Attempting to POST to TBA again"
        r = s.post(url_str, data=match_video, headers=trusted_auth)
    if "Error" in r.content:
        raise Exception(r.content)
    else:
        print "Successfully added to TBA"


"""The program starts here"""


def init(options):
    options.ein = False
    options.privacy = VALID_PRIVACY_STATUSES[0]
    options.day = dt.datetime.now().strftime("%A")
    options.files = list(reversed([f for f in os.listdir(options.where)
        if os.path.isfile(os.path.join(options.where, f))]))
    options.tags = DEFAULT_TAGS.format(options.ecode)
    options.category = DEFAULT_VIDEO_CATEGORY
    options.title = options.ename + " - " + QUAL
    if any(k == options.description for k in ("Add alternate description here.", "")):
        options.description = DEFAULT_DESCRIPTION
    # fix types
    options.ceremonies = int(options.ceremonies)
    options.tba = int(options.tba)
    options.mnum = int(options.mnum)
    options.tiebreak = int(options.tiebreak)
    options.eday = int(options.eday)

    if options.ceremonies != 0:
        options.tba = 0
    if options.tiebreak == 1:
        options.mnum = tiebreak_mnum(options.mnum, options.mtype)

    options.file, options.yttitle = create_names(options)

    if options.file is not None:
        print "Found {} to upload".format(options.file)
        try:
            if int(options.end) > options.mnum:
                options.end = int(options.end)
                upload_multiple_videos(youtube, spreadsheet, options)
        except ValueError:
            try:
                print initialize_upload(youtube, spreadsheet, options)
            except HttpError, e:
                print "An HTTP error {} occurred:\n{}".format(e.resp.status, e.content)
    else:
        raise Exception("First match file must exist")


def initialize_upload(youtube, spreadsheet, options):
    if not options.ceremonies:
        print "Initializing upload for {} match {}".format(options.mtype, options.mnum)
    else:
        print "Initializing upload for: {}".format(ceremonies_yt_title(options))
    if options.tba:
        blue_data, red_data, mcode = tba_results(options)
        tags = options.tags.split(",")
        for team in blue_data[1:] + red_data[1:]:
            tags.append("frc{}".format(team))
        tags.extend(options.ename.split(" "))
        tags.append("frc" + re.search('\D+', options.ecode).group())

        body = dict(
            snippet=dict(
                title=options.yttitle,
                description=create_description(options, blue_data[1], blue_data[2], blue_data[3], blue_data[0],
                                               red_data[1], red_data[2], red_data[3], red_data[0]),
                tags=tags,
                categoryId=options.category
            ),
            status=dict(
                privacyStatus=options.privacy
            )
        )
    else:
        mcode = get_match_code(options.mtype, options.mnum, options.mcode)

        tags = options.tags.split(",")
        tags.append("frc" + re.search('\D+', options.ecode).group())

        body = dict(
            snippet=dict(
                title=options.yttitle,
                description=create_description(
                    options, -1, -1, -1, -1, -1, -1, -1, -1),
                tags=tags,
                categoryId=options.category
            ),
            status=dict(
                privacyStatus=options.privacy
            )
        )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(options.where + options.file,
                                   chunksize=-1,
                                   resumable=True),
    )
    size1 = file_size(options.where + options.file)
    time.sleep(1)
    size2 = file_size(options.where + options.file)
    while (size1 != size2):
        size1 = file_size(options.where + options.file)
        print "Size of the file is changing, waiting 2 seconds for stabiliziation"
        time.sleep(2)
        size2 = file_size(options.where + options.file)
    return upload(insert_request, options, mcode, youtube, spreadsheet)


def upload(insert_request, options, mcode, youtube, spreadsheet):
    response = None
    status = None
    print "Uploading {} of size {}".format(options.file)
    while response is None:
        try:
            error = None
            status, response = insert_request.next_chunk()
            if 'id' in response:
                options.vid = response['id']
                print "Video link is https://www.youtube.com/watch?v={}".format(options.vid)
            else:
                exit("The upload failed with an unexpected response: {}".format(response))
        except HttpError, e:
            if e.resp.status in retry_status_codes:
                error = "A retriable HTTP error {} occurred:\n{}".format(e.resp.status,
                                                                         e.content)
            elif "uploadLimitExceeded" in e.content:
                retryforlimit += 1
                if retryforlimit < max_retries:
                    print "Waiting {} minutes to avoid upload limit".format(sleep_minutes / 60)
                    for x in xrange(sleep_minutes):
                        time.sleep(1)
                        if x % 60 == 0:
                            print "Minute {} of {}".format(x / 60, sleep_minutes / 60)
                    sleep_minutes -= 60
                    error = None
                else:
                    print "Upload limit could not be avoided\n{} was not uploaded".format(options.file)
                    return "FAILED"
            else:
                raise

        except TypeError as e:
            print response
            response = None
            status = None
            print "Upload failed, delete failed video from YouTube\nTrying again in 15 seconds"
            time.sleep(15)

        except retry_exceptions as e:
            print response
            error = "A retriable error occurred: {}".format(e)

        attempt_retry(error, retry, max_retries)
    if 'id' in response:
        options.vid = response['id']
        print "Video link is https://www.youtube.com/watch?v={}".format(options.vid)
    else:
        print "There was a problem with the upload"
    request_body = json.dumps({mcode: options.vid})
    if options.tba:
        post_video(options.tbaID, options.tbaSecret,
                   request_body, options.ecode)
    vidOptions = False
    while vidOptions == False:
        try:
            error = None
            if any("thumbnail" in file for file in [f for f in os.listdir(".") if os.path.isfile(os.path.join(".", f))]):
                update_thumbnail(youtube, options.vid, "thumbnail.png")
            else:
                print "thumbnail.png does not exist"
            add_to_playlist(youtube, options.vid, options.pID)
            vidOptions = True

        except HttpError, e:
            if e.resp.status in retry_status_codes:
                error = "A retriable HTTP error {} occurred:\n{}".format(e.resp.status,
                                                                         e.content)

        except retry_exceptions as e:
            error = "A retriable error occurred: {}".format(e)

        attempt_retry(error, retry, max_retries)

    wasBatch = "True" if any(options.end != y for y in (
        "Only for batch uploads", "")) else "False"
    usedTBA = "True" if options.tba == 1 else "False"
    totalTime = dt.datetime.now() - options.then
    values = [[str(dt.datetime.now()), str(totalTime), "https://www.youtube.com/watch?v={}".format(
        options.vid), usedTBA, options.ename, wasBatch, mcode]]
    body = {'values': values}
    spreadsheet.spreadsheets().values().append(spreadsheetId=spreadsheetID,
        range=rowRange, valueInputOption="USER_ENTERED", body=body).execute()
    return "DONE UPLOADING {}\n".format(options.file)

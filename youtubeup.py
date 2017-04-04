#!/usr/bin/python

import os
import random
import sys
import time
import argparse

from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from tbaAPI import *
from youtubeAuthenticate import *
import datetime as dt

# Default Variables
DEFAULT_VIDEO_CATEGORY = 28
DEFAULT_THUMBNAIL = "thumbnail.png"
DEFAULT_TAGS = """%s, FIRST, omgrobots, FRC, FIRST Robotics Competition, robots, Robotics, FIRST STEAMworks"""
QUAL = "Qualification Match %s"
QUARTER = "Quarterfinal Match %s"
QUARTERT = "Quarterfinal Tiebreaker %s"
SEMI = "Semifinal Match %s"
SEMIT = "Semifinal Tiebreaker %s"
FINALS = "Final Match %s"
FINALST = "Final Tiebreaker"
EXTENSION = ".mp4"
DEFAULT_TITLE = "%s" + " - " + QUAL
DEFAULT_FILE = "%s" + " - " + QUAL + EXTENSION
MATCH_TYPE = ["qm", "qf", "sf", "f1m"]
DEFAULT_DESCRIPTION = """Footage of the %s is courtesy of the %s.

Red Alliance (%s, %s, %s) - %s
Blue Alliances (%s, %s, %s) - %s

To view match schedules and results for this event, visit The Blue Alliance Event Page: https://www.thebluealliance.com/event/%s

Follow us on Twitter (@%s) and Facebook (%s).

For more information and future event schedules, visit our website: %s

Thanks for watching!

Uploaded with FRC-Youtube-Uploader (https://github.com/NikhilNarayana/FRC-YouTube-Uploader)"""

NO_TBA_DESCRIPTION = """Footage of the %s Event is courtesy of the %s.

Follow us on Twitter (@%s) and Facebook (%s).

For more information and future event schedules, visit our website: %s

Thanks for watching!

Uploaded with FRC-Youtube-Uploader (https://github.com/NikhilNarayana/FRC-YouTube-Uploader)"""

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def quals_yt_title(options):
    return options.title % options.mnum

def quarters_yt_title(options):
    if 1 <= options.mnum <= 8:
        title = options.ename + " - " + QUARTER % options.mnum
        return title
    elif 9 <= options.mnum <= 12:
        mnum = int(options.mnum) - 8
        title = options.ename + " - " + QUARTERT % str(mnum)
        return title
    else:
        raise ValueError("options.mnum must be within 1 and 12")

def semis_yt_title(options):
    if 1 <= options.mnum <= 4:
        title = options.ename + " - " + SEMI % options.mnum
        return title
    elif 5 <= options.mnum <= 6:
        mnum = int(options.mnum) - 4
        title = options.ename + " - " + SEMIT % str(mnum)
        return title
    else:
        raise ValueError("options.mnum must be within 1 and 6")

def finals_yt_title(options):
    if 1 <= options.mnum <= 2:
        title = options.ename + " - " + FINALS % options.mnum
        return title
    elif options.mnum == 3:
        title = options.ename + " - " + FINALST
        return title
    else:
        raise ValueError("options.mnum must be within 1 and 3")

def ceremonies_title(options):
    title = None 
    if options.ceremonies is 1:
        title = options.ename + " - " + "%s Opening Ceremonies" % dt.datetime.now().strftime("%A")
    if options.ceremonies is 2:
        title = options.ename + " - " + "Alliance Selection"
    if options.ceremonies is 3:
        title = options.ename + " - " + "Closing Ceremonies"
    return title

def create_title(options):
    if options.ceremonies is 0:
        switcher = {
                "qm": quals_yt_title,
                "ef": eights_yt_title,
                "qf": quarters_yt_title,
                "sf": semis_yt_title,
                "f1m": finals_yt_title,
                }
        try:
            return switcher[options.mcode](options)
        except KeyError:
            print options.mcode
    else:
        return ceremonies_title(options)

def quals_filename(options):
    for f in options.files:
        fl = f.lower()
        if all(k in fl for k in ("qual", " "+str(options.mnum), options.ename.lower())):
            print "Found %s to upload" % f
            return str(f)
    raise Exception("Cannot find Qualification file with match number %s" % options.mnum)

def quarters_filename(options):
    if 1 <= options.mnum <= 8:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("quarter", "final", " "+str(options.mnum), options.ename.lower())):
                print "Found %s to upload" % f
                return str(f)
    elif 9 <= options.mnum <= 12:
        mnum = int(options.mnum) - 8
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("quarter", "tiebreak", "final"," "+str(options.mnum), options.ename.lower())):
                print "Found %s to upload" % f
                return str(f)
    else:
        raise ValueError("mnum must be between 1 and 12")

def semis_filename(options):
    if 1 <= options.mnum <= 4:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("semi", "final", " "+str(options.mnum), options.ename.lower())):
                print "Found %s to upload" % f
                return str(f)
    elif 5 <= options.mnum <= 6:
        mnum = int(options.mnum) - 4
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("semi", "tiebreak", "final"," "+str(options.mnum), options.ename.lower())):
                print "Found %s to upload" % f
                return str(f)
    else:
        raise ValueError("mnum must be between 1 and 6")

def finals_filename(options):
    if 1 <= options.mnum <= 2:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in ("final"," "+str(options.mnum), options.ename.lower())):
                if all(k not in fl for k in ("quarter","semi")):
                    print "Found %s to upload" % f
                    return str(f)
    elif options.mnum == 3:
        for f in options.files:
            if all(k in fl for k in ("tiebreak", "final"," "+str(options.mnum), options.ename.lower())):
                if all(k not in fl for k in ("quarter","semi")):
                    print "Found %s to upload" % f
                    return str(f)
    else:
        raise ValueError("mnum must be between 1 and 3")

def ceremonies_filename(options):
    if options.ceremonies is 1:
        for f in options.files:
            fl = f.lower()
            if all(k in fl for k in (dt.datetime.now().strftime("%A").lower(), "opening", "ceremonies")) in f:
                print "Found %s to upload" % f
                return str(f)
    if options.ceremonies is 2:
        for f in options.files:
            fl = f.lower()
            if "alliance selection" in fl:
                print "Found %s to upload" % f
                return str(f)
    if options.ceremonies is 3:
        for f in options.files:
            fl = f.lower()
            if "closing" in fl or "award" in fl and "ceremonies" in fl:
                print "Found %s to upload" % f
                return str(f)

def create_filename(options):
    if options.ceremonies is 0:
        switcher = {
                "qm": quals_filename,
                "qf": quarters_filename,
                "sf": semis_filename,
                "f1m": finals_filename,
                }
        try:
            return switcher[options.mcode](options)
        except KeyError:
            print options.mcode
    else:
        return ceremonies_filename(options)
def quals_match_code(mcode, mnum):
    match_code = str(mcode) + str(mnum)
    return match_code

def eights_match_code(mcode, mnum):
    match_set = str(mnum % 8)
    match_code = None
    if match_set == "0":
        match_set = "8"
    if mnum <= 8:
        match_code = mcode + match_set + "m1"
    elif mnum <= 16:
        match_code = mcode + match_set + "m2"
    elif mnum <= 24:
        match_code = mcode + match_set + "m3"
    else:
        raise ValueError("Match Number can't be larger than 24")
    return match_code


def quarters_match_code(mcode, mnum):
    match_set = str(mnum % 4)
    match_code = None
    if match_set == "0":
        match_set = "4"
    if mnum <= 4:
        match_code = mcode + match_set + "m1"
    elif 5 <= mnum <= 8:
        match_code = mcode + match_set + "m2"
    elif 9 <= mnum <= 12:
        match_code = mcode + match_set + "m3"
    else:
        raise ValueError("Match Number can't be larger than 12")
    return match_code

def semis_match_code(mcode, mnum):
    match_set = str(mnum % 2)
    match_code = None
    if match_set == "0":
        match_set = "2"
    if mnum <= 2:
        match_code = mcode + match_set + "m1"
    elif 3 <= mnum <= 4:
        match_code = mcode + match_set + "m2"
    elif 5 <= mnum <= 6:
        match_code = mcode + match_set + "m3"
    else:
        raise ValueError("Match Number can't be larger than 6")
    return match_code

def finals_match_code(mcode, mnum):
    if mnum > 3:
        raise ValueError("Match Number can't be larger than 3")
    match_code = str(mcode) + str(mnum)
    return match_code

def get_match_code(mcode, mnum):
    switcher = {
            "qm": quals_match_code,
            "ef": eights_match_code,
            "qf": quarters_match_code,
            "sf": semis_match_code,
            "f1m": finals_match_code,
    }
    return switcher[mcode](mcode, mnum)

def tba_results(options):
    mcode = get_match_code(options.mcode, int(options.mnum))
    blue_data, red_data = get_match_results(options.ecode, mcode)
    return blue_data, red_data, mcode

def create_description(options, blue1, blue2, blue3, blueScore, red1, red2, red3, redScore):
    if all(x <= -1 for x in (red1, red2, red3, redScore, blue1, blue2, blue3, blueScore)):
        return options.description % (options.ename, options.prodteam, options.twit, options.fb, options.weblink)
    try:
        return options.description % (str(options.ename), str(options.prodteam),
                str(red1), str(red2), str(red3), str(redScore), str(blue1), str(blue2), str(blue3), str(blueScore),
                str(options.ecode), str(options.twit), str(options.fb), str(options.weblink))
    except TypeError, e:
        print e
        return options.description

def tiebreak_mnum(mnum, mcode):
    switcher = {
            "qm": int(mnum),
            "ef": int(mnum) + 16,
            "qf": int(mnum) + 8,
            "sf": int(mnum) + 4,
            "f1m": 3,
    }
    return switcher[mcode]

def upload_multiple_videos(youtube, spreadsheet, options):
    while int(options.mnum) <= int(options.end):
        try:
            initialize_upload(youtube, spreadsheet, options)
        except HttpError, e:
            print "An HTTP error %d occurred:\n%s\n" % (e.resp.status, e.content)
        options.mnum = int(options.mnum) + 1
        print "All matches have been uploaded"

def update_thumbnail(youtube, video_id, thumbnail):
    youtube.thumbnails().set(
        videoId=video_id,
        media_body=thumbnail
        ).execute()
    print "Thumbnail added to video %s" % video_id

def add_to_playlist(youtube,videoID,playlistID):
    if type(videoID) is list: # Recursively add videos if videoID is list
        for vid in videoID:
            add_video_to_playlist(youtube,vid,playlistID)
    else:
        add_video_request=youtube.playlistItems().insert(
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

def init(options):
    """The program starts here"""
    options.files = reversed([f for f in os.listdir(options.where) if os.path.isfile(os.path.join(options.where, f))])
    options.tags = DEFAULT_TAGS % options.ecode
    options.privacyStatus = 0
    options.ceremonies = int(options.ceremonies)
    options.category = DEFAULT_VIDEO_CATEGORY
    options.title = options.ename + " - " + QUAL
    options.file = options.ename + " - " + QUAL + EXTENSION
    if options.description == "Add alternate description here.":
        options.description = DEFAULT_DESCRIPTION
    options.tba = int(options.tba)
    if options.tba:
        TBA_ID = options.tbaID
        TBA_SECRET = options.tbaSecret
    if int(options.ceremonies) != 0:
        options.tba = 0
    if not options.tba:
        TBA_ID = -1
        TBA_SECRET = -1
        options.description = NO_TBA_DESCRIPTION
    if int(options.tiebreak) == 1:
        options.mnum = tiebreak_mnum(options.mnum, options.mcode)

    youtube = get_youtube_service()
    spreadsheet = get_spreadsheet_service()

    try:
        if int(options.end) > int(options.mnum):
            upload_multiple_videos(youtube, spreadsheet, options)
    except ValueError:
        try:
            initialize_upload(youtube, spreadsheet, options)
        except HttpError, e:
            print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

def initialize_upload(youtube, spreadsheet, options):
    if options.ceremonies == 0:
        print "Initializing upload for %s match %s" % (options.mcode, options.mnum)
    else:
        print "Initializing upload for: %s" % ceremonies_title(options)
    tags = None
    if options.tba == 1:
        blue_data, red_data, mcode = tba_results(options)
        tags = options.tags.split(",")
        tags.extend(["frc" + str(blue_data[1]), "frc" + str(blue_data[2]), "frc" + str(blue_data[3])])
        tags.extend(["frc" + str(red_data[1]), "frc" + str(red_data[2]), "frc" + str(red_data[3])])
        tags.append(get_event_hashtag(options.ecode))
        tags.extend(options.ename.split(" "))

        body = dict(
                snippet=dict(
                    title=create_title(options),
                    description=create_description(options, blue_data[1], blue_data[2], blue_data[3], blue_data[0],
                        red_data[1], red_data[2], red_data[3], red_data[0]),
                    tags=tags,
                    categoryId=options.category
                    ),
                status=dict(
                    privacyStatus=VALID_PRIVACY_STATUSES[options.privacyStatus]
                    )
                )
    else:
        mcode = get_match_code(options.mcode, int(options.mnum))

        tags = options.tags.split(",")
        tags.append(get_event_hashtag(options.ecode))

        body = dict(
                snippet=dict(
                    title=create_title(options),
                    description=create_description(options, -1, -1, -1, -1, -1, -1, -1, -1),
                    tags=tags,
                    categoryId=options.category
                    ),
                status=dict(
                    privacyStatus=VALID_PRIVACY_STATUSES[options.privacyStatus]
                    )
                )

    insert_request = youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=MediaFileUpload(options.where+create_filename(options), chunksize=-1, resumable=True),
            )

    resumable_upload(insert_request, options, mcode, youtube, spreadsheet)

def resumable_upload(insert_request, options, mcode, youtube, spreadsheet):
    response = None
    error = None
    retry = 0
    retry_status_codes = get_retry_status_codes()
    retry_exceptions = get_retry_exceptions()
    max_retries = get_max_retries()
    while response is None:
        try:
            print "Uploading file..."
            status, response = insert_request.next_chunk()
            if 'id' in response:
                print "Video link is https://www.youtube.com/watch?v=%s" % response['id']
                update_thumbnail(youtube, response['id'], "thumbnail.png")
                add_to_playlist(youtube, response['id'], options.pID)
                request_body = json.dumps({mcode: response['id']})
                if options.tba:
                    post_video(options.tbaID, options.tbaSecret, request_body, options.ecode)
                totalTime = dt.datetime.now() - options.then
                spreadsheetID = "18flsXvAcYvQximmeyG0-9lhYtb5jd_oRtKzIN7zQDqk"
                rowRange = "Data!A1:F1"
                wasBatch = "True" if type(options.end) is int else "False"
                usedTBA = "True" if int(options.tba) == 1 else "False"
                values = [[str(dt.datetime.now()),str(totalTime),"https://www.youtube.com/watch?v=%s" % response['id'], usedTBA, options.ename, wasBatch]]
                body = {'values': values}
                appendSpreadsheet = spreadsheet.spreadsheets().values().append(spreadsheetId=spreadsheetID, range=rowRange, valueInputOption="RAW", body=body).execute()
            else:
                exit("The upload failed with an unexpected response: %s" %
                        response)
        except HttpError, e:
            if e.resp.status in retry_status_codes:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                        e.content)
            else:
                raise
        except retry_exceptions as e:
            error = "A retriable error occurred: %s" % e

        if error is not None:
            print error
            retry += 1
            if retry > max_retries:
                exit("No longer attempting to retry.")

            max_sleep = 2 ** retry
            sleep_seconds = random.random() * max_sleep
            print "Sleeping %f seconds and then retrying..." % sleep_seconds
            time.sleep(sleep_seconds)

#!/usr/bin/python

import httplib
import httplib2
import os
import random
import sys
import time
import pyperclip
import datetime

from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.tools import argparser
from TBA import *
from addtoplaylist import add_video_to_playlist
from updateThumbnail import update_thumbnail
from youtubeAuthenticate import *

# Default Variables - A lot needs to be changed based on event
DEFAULT_VIDEO_CATEGORY = 28
DEFAULT_THUMBNAIL = "thumbnail.png"
DEFAULT_PLAYLIST_ID = "PL9UFVOe2UANx7WGnZG57BogYFKThwhIa2"
TBA_TOKEN = "8h9BbNm24dRkbCOo" # Contact TBA for a token unique to each event
TBA_SECRET = "MaroS6T59BrQ90zZAdq2gyPK0S0QiUjjBaR8Sa8CRuBwqpX9Wn PlNIdlOQXr7FD3" # ^
EVENT_CODE = "2016arc"
DEFAULT_TAGS = EVENT_CODE + \
    ", FIRST, omgrobots, FRC, FIRST Robotics Competition, automation, robots, Robotics, FIRST Stronghold, INFIRST, IndianaFIRST, Indiana, District Championship"
EVENT_NAME = "2016 INFIRST Indiana State Championship"
QUAL = "Qualification Match %s"
QUARTER = "Quarterfinal Match %s"
QUARTERT = "Quarterfinal Tiebreaker %s"  # Dear FIRST, what the hell?
SEMI = "Semifinal Match %s"
SEMIT = "Semifinal Tiebreaker %s"
FINALS = "Finals Match %s"
FINALST = "Finals Tiebreaker"
EXTENSION = ".mp4"
DEFAULT_TITLE = EVENT_NAME + " - " + QUAL
DEFAULT_FILE = EVENT_NAME + " - " + QUAL + EXTENSION
MATCH_TYPE = ["qm", "qf", "sf", "f1m"]
DEFAULT_DESCRIPTION = "Footage of the " + EVENT_NAME + " Event is courtesy the IndianaFIRST AV Crew." + """

Blue Alliance (%s, %s, %s) - %s
Red Alliance  (%s, %s, %s) - %s

To view match schedules and results for this event, visit The Blue Alliance Event Page: https://www.thebluealliance.com/event/2016""" + EVENT_CODE + """

Follow us on Twitter (@IndianaFIRST) and Facebook (IndianaFIRST).

For more information and future event schedules, visit our website: www.indianafirst.org

Thanks for watching!"""

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def create_title(options):
    mcode = MATCH_TYPE[options.mcode]
    if mcode == "qm":
        return options.title % options.mnum
    elif mcode == "qf":
        if options.mnum < 8:
            title = YEAR + " " + EVENT_NAME + " - " + QUARTER % options.mnum
            return title
        elif options.mnum > 8:
            mnum = options.mnum - 8
            title = YEAR + " " + EVENT_NAME + " - " + QUARTERT % mnum
            return title
    elif mcode == "sf":
        if options.mnum < 4:
            title = YEAR + " " + EVENT_NAME + " - " + SEMI % options.mnum
            return title
        elif options.mnum > 4:
            mnum = options.mnum - 4
            title = YEAR + " " + EVENT_NAME + " - " + SEMIT % mnum
            return title
    elif mcode == "f1m":
        if options.mnum < 2:
            title = YEAR + " " + EVENT_NAME + " - " + FINALS % options.mnum
            return title
        elif options.mnum > 2:
            mnum = options.mnum - 2
            title = YEAR + " " + EVENT_NAME + " - " + FINALST % mnum
            return title

def create_filename(options):
    mcode = MATCH_TYPE[options.mcode]
    if mcode == "qm":
        return options.file % options.mnum
    elif mcode == "qf":
        if options.mnum < 8:
            filename = EVENT_NAME + " - " + QUARTER + EXTENSION % options.mnum
            return str(filename)
        elif options.mnum > 8:
            mnum = options.mnum - 8
            filename = EVENT_NAME + " - " + QUARTERT + EXTENSION % mnum
            return str(filename)
    elif mcode == "sf":
        if options.mnum < 4:
            filename = EVENT_NAME + " - " + SEMI + EXTENSION % options.mnum
            return str(filename)
        elif options.mnum > 4:
            mnum = options.mnum - 4
            filename = EVENT_NAME + " - " + SEMIT + EXTENSION % mnum
            return str(filename)
    elif mcode == "f1m":
        if options.mnum < 2:
            filename = EVENT_NAME + " - " + FINALS + EXTENSION % options.mnum
            return str(filename)
        elif options.mnum > 2:
            mnum = options.mnum - 2
            filename = EVENT_NAME + " - " + FINALST + EXTENSION % mnum
            return str(filename)

def get_match_code(mcode, mnum):
    if mcode == "qm":
        match_code = mcode + mnum
        return EVENT_CODE, match_code
    if mcode == "qf":
        match_set = mnum%4
        if mnum <= 4:
            match = 1
            match_code = mcode + str(match_set) + "m" + str(match)
            return EVENT_CODE, match_code
        if mnum > 4 and mnum <= 8:
            match = 2
            match_code = mcode + str(match_set) + "m" + str(match)
            return EVENT_CODE, match_code
        if mnum > 8 and mnum <= 12:
            match = 3
            match_code = mcode + str(match_set) + "m" + str(match)
            return EVENT_CODE, match_code
    if mcode == "sf":
        match_set = mnum%2
        if mnum <= 2:
            match = 1
            match_code = mcode + str(match_set) + "m" + str(match)
            return EVENT_CODE, match_code
        if mnum > 2 and mnum <= 4:
            match = 2
            match_code = mcode + str(match_set) + "m" + str(match)
            return EVENT_CODE, match_code
        if mnum > 4 and mnum <= 6:
            match = 3
            match_code = mcode + str(match_set) + "m" + str(match)
            return EVENT_CODE, match_code
    if mcode == "f1m":
        match_code = MATCH_TYPE[mcode] + mnum
        return EVENT_CODE, match_code


def tba_results(options):
    ecode, mcode = get_match_code(MATCH_TYPE[options.mcode], options.mnum)
    match_data = get_match_results(ecode, mcode)
    blue1, blue2, blue3, blue_score, red1, red2, red3, red_score = parse_data(
        match_data)
    return blue1, blue2, blue3, blue_score, red1, red2, red3, red_score, mcode


def initialize_upload(youtube, options):
    tags = None
    blue1, blue2, blue3, blue_score, red1, red2, red3, red_score, mcode = tba_results(
        options) # Comment out if Blue Alliance is not responding

    if options.keywords:
        tags = options.keywords.split(",")
        tags.append("frc"+str(blue1))
        tags.append("frc"+str(blue2))
        tags.append("frc"+str(blue3))
        tags.append("frc"+str(red1))
        tags.append("frc"+str(red2))
        tags.append("frc"+str(red3))

    body = dict(
        snippet=dict(
            title=create_title(options),
            description=options.description % (blue1, blue2, blue3, blue_score,
                                               red1, red2, red3, red_score),
            tags=tags,
            categoryId=options.category
        ),
        status=dict(
            privacyStatus=options.privacyStatus
        )
    )

    # Call the API's videos.insert method to create and upload the video.
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(
            create_filename(options), chunksize=-1, resumable=True)
    )

    resumable_upload(insert_request, options.mnum, mcode, youtube)

# This method implements an exponential backoff strategy to resume a
# failed upload.


def resumable_upload(insert_request, mnum, mcode, youtube):
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
                print "Video id '%s' was successfully uploaded." % response['id']
                print "Video link is https://www.youtube.com/watch?v=%s" % response['id']
                update_thumbnail(youtube, response['id'], "thumbnail.png")
                print "Video thumbnail added"
                add_video_to_playlist(
                    youtube, response['id'], DEFAULT_PLAYLIST_ID)
                request_body = json.dumps({mcode:response['id']})
                post_video(TBA_TOKEN, TBA_SECRET, request_body, EVENT_CODE)

            else:
                exit("The upload failed with an unexpected response: %s" %
                     response)
        except HttpError, e:
            if e.resp.status in retry_status_codes:
                error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                                     e.content)
            else:
                raise
        except retry_exceptions, e:
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


if __name__ == '__main__':
    argparser.add_argument("--mnum", help="""Match Number to add, if in elims
      keep incrementing by one unless for tiebreaker, in which case add 8(qf), 4(sf), or 2(f) to the tiebreaker number""", required=True)
    argparser.add_argument(
        "--mcode", help="Match code (qm,qf,sf,f) starting at 0 ->3", default=0)
    argparser.add_argument(
        "--file", help="Video file to upload", default=DEFAULT_FILE)
    argparser.add_argument(
        "--title", help="Video title", default=DEFAULT_TITLE)
    argparser.add_argument(
        "--description", help="Video description", default=DEFAULT_DESCRIPTION)
    argparser.add_argument("--category", default=DEFAULT_VIDEO_CATEGORY, help="Numeric video category. " +
                           "See https://developers.google.com/youtube/v3/docs/videoCategories/list")
    argparser.add_argument(
        "--keywords", help="Video keywords, comma separated", default=DEFAULT_TAGS)
    argparser.add_argument("--privacyStatus", choices=VALID_PRIVACY_STATUSES,
                           default=VALID_PRIVACY_STATUSES[2], help="Video privacy status.")
    args = argparser.parse_args()

    youtube = get_authenticated_service(args)

    try:
        initialize_upload(youtube, args)
    except HttpError, e:
        print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

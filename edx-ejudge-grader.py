# coding=utf8

import ast
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import urllib2
import urlparse
import sys
import requests

import edx_util as edx
import error as e
import project_urls
import settings
import xqueue_util as util
from ejudge_grade import grader

logger = logging.getLogger('edx-ejudge-grader')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)-8s [%(asctime)s] %(filename)s : %(message)s')

ch = logging.StreamHandler(sys.stderr)
ch.setFormatter(formatter)
ch.setLevel(logging.INFO)
logger.addHandler(ch)

fh = logging.handlers.RotatingFileHandler('./log/log.log', maxBytes=(1048576*5), backupCount=7, encoding='utf-8')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)

QUEUE_NAME = settings.QUEUE_NAME


def each_cycle():
    print('[*]Logging in to xqueue')
    try:
        session = util.xqueue_login()
    except requests.HTTPError:
        logger.error('EDX server is not responding')
        return None
    success_length, queue_length = get_queue_length(QUEUE_NAME, session)
    if success_length and queue_length > 0:
        success_get, queue_item = get_from_queue(QUEUE_NAME, session)
        logger.info(queue_item)
        success_parse, content = util.parse_xobject(queue_item, QUEUE_NAME)
        if success_get and success_parse:
            try:
                answer = grade(content)
            except e.GraderException, err:
                answer = edx.answer_after_error(err)
            content_header = json.loads(content['xqueue_header'])
            content_body = json.loads(content['xqueue_body'])
            xqueue_header, xqueue_body = util.create_xqueue_header_and_body(
                content_header['submission_id'],
                content_header['submission_key'],
                answer['success'],
                answer['score'],
                edx.answer_msg(answer))
            (success, msg) = util.post_results_to_xqueue(session, json.dumps(
                xqueue_header), json.dumps(xqueue_body), )
            if success:
                logger.info("successfully posted result back to xqueue")
                print("successfully posted result back to xqueue")


def grade(content):
    body = json.loads(content['xqueue_body'])
    student_info = json.loads(body.get('student_info', '{}'))
    try:
        grader_payload = ast.literal_eval(
            body['grader_payload'].strip().lower())
    except SyntaxError, err:
        return edx.answer_after_error(err)
    resp = body.get('student_response', '')
    try:
        edx.validate_payload(grader_payload, resp)
    except (e.ValidationError, e.EmptyPayload, e.ProhibitedOperatorsError), err:
        logger.warning(err.msg)
        return edx.answer_after_error(err)
    try:
        answer = grader(resp, grader_payload)
    except (BaseException, e.StudentResponseCompilationError), err:
        logger.exception(err)
        if isinstance(err, e.StudentResponseCompilationError):
            return edx.answer_after_error(err)
        raise e.GraderException
    files = json.loads(content['xqueue_files'])
    for (filename, fileurl) in files.iteritems():
        response = urllib2.urlopen(fileurl)
        with open(filename, 'w') as f:
            f.write(response.read())
        f.close()
        response.close()
    return answer


def get_from_queue(queue_name, xqueue_session):
    """
        Get a single submission from xqueue
        """
    try:
        success, response = util._http_get(xqueue_session,
                                           urlparse.urljoin(
                                               settings.XQUEUE_INTERFACE['url'],
                                               project_urls.XqueueURLs.get_submission),
                                           {'queue_name': queue_name})
    except Exception as err:
        return False, "Error getting response: {0}".format(err)

    return success, response


def get_queue_length(queue_name, xqueue_session):
    """
        Returns the length of the queue
        """
    try:
        success, response = util._http_get(xqueue_session,
                                           urlparse.urljoin(
                                               settings.XQUEUE_INTERFACE['url'],
                                               project_urls.XqueueURLs.get_queuelen),
                                           {'queue_name': queue_name})

        if not success:
            return False, "Invalid return code in reply"

    except Exception as e:
        logger.critical("Unable to get queue length: {0}".format(e))
        return False, "Unable to get queue length."

    return True, response


try:
    while True:
        each_cycle()
        time.sleep(2)
except KeyboardInterrupt:
    print '^C received, shutting down'

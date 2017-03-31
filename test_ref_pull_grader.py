#coding=utf8
import time
import logging
import json
import urllib2
import xqueue_util as util
import settings
import urlparse
import project_urls
import subprocess
import xml.etree.ElementTree as etree
import json

log = logging.getLogger(__name__)

QUEUE_NAME = settings.QUEUE_NAME


def each_cycle():
    print('[*]Logging in to xqueue')
    session = util.xqueue_login()
    success_length, queue_length = get_queue_length(QUEUE_NAME, session)
    if success_length and queue_length > 0:
        success_get, queue_item = get_from_queue(QUEUE_NAME, session)
        print(queue_item)
        success_parse, content = util.parse_xobject(queue_item, QUEUE_NAME)
        if success_get and success_parse:
            ans = grade(content)
            content_header = json.loads(content['xqueue_header'])
            content_body = json.loads(content['xqueue_body'])
            xqueue_header, xqueue_body = util.create_xqueue_header_and_body(
                content_header['submission_id'],
                content_header['submission_key'],
                ans['success'],
                1,
                '<p><emph>Good Job!</emph></p>',
                'reference_dummy_grader')
            (success, msg) = util.post_results_to_xqueue(session, json.dumps(
                xqueue_header), json.dumps(xqueue_body), )
            if success:
                print("successfully posted result back to xqueue")


def grade(content):
    print(content)
    body = json.loads(content['xqueue_body'])
    student_info = json.loads(body.get('student_info', '{}'))
    resp = body.get('student_response', '')
    answer = grade_in_ejudge(resp)
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
        log.critical("Unable to get queue length: {0}".format(e))
        return False, "Unable to get queue length."

    return True, response


def grade_in_ejudge(response, contest_id=2, problem_name='A', lang='gcc'):
    response_file = open('response.txt', 'w')
    response_file.write(response)
    response_file.close()
    run_id, err = subprocess.Popen(["/opt/ejudge/bin/ejudge-contests-cmd",
                                    str(contest_id),
                                    "submit-run",
                                    "/home/ejudge/session.pwd",
                                    problem_name,
                                    lang,
                                    'response.txt'],
                                   stdout=subprocess.PIPE).communicate()

    run_id = run_id.replace('/n', ' ').strip()
    print run_id
    name_report_file = 'report_' + run_id + '.xml'
    command = '/opt/ejudge/bin/ejudge-contests-cmd ' + str(
        contest_id) + ' dump-report' + ' /home/ejudge/session.pwd ' + run_id + ' > ./report/' + name_report_file
    print command
    # КОСТЫЛЬ.это время, за которое еджадж должен проверить работу. сделать проверку в цикле
    time.sleep(2)
    subprocess.call(command, shell=True)
    rezult = dict()
    del_str_in_xml(name_report_file)
    result_xml = etree.parse('./report/' + name_report_file)
    test_tag = result_xml.getroot().find("tests").findall("test")
    checker_list = list()
    test_ok = 0
    for i in test_tag:
        checker_list.append(i.find("checker"))
    for checker in checker_list:
        if checker.text.strip().find('OK') != -1:
            test_ok += 1
    print test_ok, checker_list
    if test_ok != len(checker_list):
        rezult['success'] = False
    else:
        rezult['success'] = True
    compiler_out = result_xml.getroot().find("compiler_output").text
    if compiler_out:
        rezult['compiler_output'] = compiler_out
    print "rezult=", rezult
    return rezult


def create_task(grader_payload):
    pass

def exist_contest(name_contest):
    file = open('./contest_name_to_id.json','r')
    contest_table = json.load(file)
    file.close()
    if name_contest in contest_table:
        return -1
    else:
        contest_table[name_contest] = str(len(contest_table) + 1)
        outfile = open('./contest_name_to_id.json','w')
        json.dump(contest_table, outfile)
        outfile.close()
        return contest_table[name_contest]

def create_contest_xml(name_contest, contest_id):
    name_xml = (6 - len(contest_id)) * '0' + str(contest_id) + '.xml'
    root = etree.Element("contest")


def del_str_in_xml(name_file):
    file = open('./report/' + name_file, 'r')
    f_line = list()
    for line in file:
        f_line.append(line)
    file.close()
    f = open('./report/' + name_file, 'w')
    for line in f_line[2:]:
        f.write(line)
    f.close()
    print 'del 2 str = OK!'


try:
    logging.basicConfig()
    while True:
        each_cycle()
        time.sleep(2)
except KeyboardInterrupt:
    print '^C received, shutting down'

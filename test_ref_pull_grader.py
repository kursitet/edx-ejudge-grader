# coding=utf8
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
import os
import csv

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


def get_contest_id(name_contest):
    file = open('./contest_name_to_id.json', 'r')
    contest_table = json.load(file)
    file.close()
    if name_contest in contest_table:
        return contest_table[name_contest], True
    else:
        contest_table[name_contest] = str(len(contest_table) + 1)
        outfile = open('./contest_name_to_id.json', 'w')
        json.dump(contest_table, outfile)
        outfile.close()
        return contest_table[name_contest], False


def create_contest_xml(name_contest, contest_id):
    name_xml = (6 - len(contest_id)) * '0' + str(contest_id) + '.xml'
    root = etree.Element('contest', attrib={'id': contest_id,
                                            'disable_team_password': 'yes',
                                            'personal': 'yes', 'managed': 'yes',
                                            'run_managed': 'yes'})
    name = etree.SubElement(root, 'name')
    name.text = name_contest
    name_en = etree.SubElement(root, 'name_en')
    name_en.text = name_contest
    default_locale = etree.SubElement(root, 'default_locale')
    default_locale.text = 'Russian'
    register_url = etree.SubElement(root, 'register_url')
    register_url.text = 'http://ejudge.dev.mccme.ru/cgi-bin/new-register'
    team_url = etree.SubElement(root, 'team_url')
    team_url.text = 'http://ejudge.dev.mccme.ru/cgi-bin/new-client'
    register_access = etree.SubElement(root, 'register_access')
    register_access.set('default', 'allow')
    users_access = etree.SubElement(root, 'users_access')
    users_access.set('default', 'allow')
    master_access = etree.SubElement(root, 'master_access')
    master_access.set('default', 'allow')
    ip1 = etree.SubElement(master_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip1.text = '1.0.0.127'
    ip2 = etree.SubElement(master_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip2.text = '172.18.1.24'
    judge_access = etree.SubElement(root, 'judge_access',
                                    attrib={'default': 'allow'})
    ip1 = etree.SubElement(judge_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip1.text = '1.0.0.127'
    ip2 = etree.SubElement(judge_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip2.text = '172.18.1.24'
    team_access = etree.SubElement(root, 'team_access',
                                   attrib={'default': 'allow'})
    ip1 = etree.SubElement(team_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip1.text = '1.0.0.127'
    ip2 = etree.SubElement(team_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip2.text = '172.18.1.24'
    serve_control_access = etree.SubElement(root, 'serve_control_access',
                                            attrib={'default': 'allow'})
    ip1 = etree.SubElement(serve_control_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip1.text = '1.0.0.127'
    ip2 = etree.SubElement(serve_control_access, 'ip',
                           attrib={'allow': 'yes', 'ssl': 'no'})
    ip2.text = '172.18.1.24'
    caps = etree.SubElement(root, 'caps')
    cap = etree.SubElement(caps, 'cap', attrib={'login': 'nimere'})
    cap.text = 'FULL_SET,'
    etree.SubElement(root, 'contestants',
                     attrib={'min': '1', 'max': '1', 'initial': '1'})
    tree = etree.ElementTree(root)
    tree.write('/home/judges/data/contests/' + name_xml)


def create_dir_structure(contest_id):
    name_dir_contest = (6 - len(contest_id)) * '0' + str(contest_id) + '/'
    path_contest = '/home/judges/' + name_dir_contest
    os.makedirs(path_contest)
    os.makedirs(path_contest + 'conf/')
    os.makedirs(path_contest + 'problems/')
    os.makedirs(path_contest + 'var/')
    return path_contest


def create_serve_cfg(path_contest, lang_name, problem_name):
    serve = open(path_contest + 'conf/serve.cfg', 'w')
    global_param = ['# -*- coding: utf-8 -*-', '# $Id$', 'contest_time = 0',
                 'score_system = acm',
                 'compile_dir = "../../compile/var/compile"',
                 'team_enable_rep_view',
                 'ignore_compile_errors',
                 'problem_navigation',
                 'rounding_mode = floor',
                 'cr_serialization_key = 22723',
                 'enable_runlog_merge',
                 'advanced_layout',
                 'enable_l10n',
                 'team_download_time = 0',
                 'cpu_bogomips = 4533']
    lang_param = get_lang_param(lang_name)
    problem_param = get_problem_param(problem_name)
    tester_param = get_tester_param()
    all_param = global_param.extend(lang_param).extend(problem_param).extend(tester_param)
    for row in all_param:
        serve.write(row)


def get_lang_param(lang_short_name):
    lang_id = get_lang_id(lang_short_name)
    param = ['[language]']
    file = open('./programm_lang/' + lang_id, 'r')
    param.extend(list(file))
    return param


def get_lang_id(lang_short_name):
    file = open('./lang_short_to_id.csv', 'r')
    lang_list = csv.DictReader(file, delimiter=';', skipinitialspace=True)
    for lang in lang_list:
        if lang['name'] == lang_short_name:
            return lang['id']


def get_problem_param(problem_name):
    param = [
        '[problem]',
        'short_name = ' + '"'+problem_name+'"',
        'long_name = ""',
        'scoring_checker = 0',
        'interactive_valuer = 0',
        'manual_checking = 0',
        'check_presentation = 0',
        'use_stdin',
        'combined_stdin = 0',
        'use_stdout',
        'combined_stdout = 0',
        'binary_input = 0',
        'ignore_exit_code = 0',
        'test_sfx = ".dat"',
        'test_pat = ""',
        'use_corr',
        'corr_sfx = ".ans"',
        'corr_pat = ""',
        'use_info = 0',
        'info_sfx = ""',
        'info_pat = ""',
        'use_tgz = 0',
        'tgz_sfx = ""',
        'tgz_pat = ""',
        'tgzdir_sfx = ""',
        'tgzdir_pat = ""',
        'standard_checker = "cmp_int_seq"',
        'disable_auto_testing = 0',
        'disable_testing = 0',
        'enable_compilation = 0',
        'valuer_sets_marked = 0',
        'disable_stderr = 0',
        'normalization = "nl"'
    ]
    return param


def get_tester_param():
    param = ['[tester]',
             'any',
             'no_core_dump',
             'kill_signal = KILL',
             'memory_limit_type = "default"',
             'secure_exec_type = "static"',
             'clear_env',
             'start_env = "PATH=/usr/local/bin:/usr/bin:/bin"',
             'start_env = "HOME"',
             'check_dir = "TWD"',
             ]
    return param


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

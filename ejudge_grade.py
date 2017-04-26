# coding=utf8
import subprocess
import xml.etree.ElementTree as etree
from os import devnull

import ejudge_util


def grader(response, grader_payload):
    contest_id = ejudge_util.get_contest_id(grader_payload['course_name'])
    problem_exist = ejudge_util.problem_exist(contest_id,
                                              grader_payload['problem_name'])
    if not contest_id or not problem_exist:
        ejudge_util.create_task(grader_payload)
        contest_id = ejudge_util.get_contest_id(grader_payload['course_name'])
    check_payload = ejudge_util.check_grader_payload(grader_payload,
                                                     ejudge_util.get_contest_path(
                                                         contest_id),
                                                     grader_payload[
                                                         'problem_name'])
    if check_payload:
        ejudge_util.update_payload(check_payload, grader_payload)
    result = run_grade_in_ejudge(response, grader_payload)
    return result


def run_grade_in_ejudge(response, grader_payload):
    response_file = open('response.txt', 'w')
    response_file.write(response)
    response_file.close()
    contest_id = ejudge_util.get_contest_id(grader_payload['course_name'])
    problem_name = grader_payload['problem_name']
    lang = grader_payload['lang_short_name']
    run_id = ejudge_submit_run(contest_id, problem_name, lang)
    if not run_id:
        ejudge_util.update_session_file(contest_id)
        run_id = ejudge_submit_run(contest_id, problem_name, lang)
    run_id = run_id.strip()
    report = ejudge_dump_report(contest_id, run_id)
    if not report:
        pass
    result = pars_report(contest_id, run_id)
    return result


def pars_report(contest_id, run_id):
    result = dict()
    contest_path = ejudge_util.get_contest_path(contest_id)
    name_report_file = 'report_' + run_id + '.xml'
    del_str_in_report_xml(contest_path, name_report_file)
    result_xml = etree.parse(contest_path + 'report/' + name_report_file)
    test_tag = result_xml.getroot().find("tests").findall("test")
    test_ok = 0
    if not test_tag:
        result['success'] = False
        result['score'] = 0
        return result
    for i in test_tag:
        if i.attrib['status'] == 'OK':
            test_ok += 1
    print "number success test = ", test_ok
    if test_ok != len(test_tag):
        result['success'] = False
        result['score'] = 0
    else:
        result['success'] = True
        result['score'] = 1
    compiler_out = result_xml.getroot().find("compiler_output").text
    if compiler_out:
        result['compiler_output'] = compiler_out
    print "Report pars.\nresult=", result
    return result


def del_str_in_report_xml(contest_path, name_report):
    report_full_name = contest_path + 'report/' + name_report
    file_r = open(report_full_name, 'r')
    f_line = list()
    for line in file_r:
        f_line.append(line)
    file_r.close()
    f = open(report_full_name, 'w')
    for line in f_line[2:]:
        f.write(line)
    f.close()


def ejudge_submit_run(contest_id, problem_name, lang):
    session_key = ejudge_util.get_session_key(contest_id)
    command = ['/opt/ejudge/bin/ejudge-contests-cmd',
               str(contest_id),
               'submit-run',
               '--session',
               session_key,
               problem_name,
               lang,
               'response.txt']
    submit_run = subprocess.Popen(command, stdout=subprocess.PIPE)
    run_id, err = submit_run.communicate()
    print 'run id = ', run_id, 'contest_id = ', contest_id
    return run_id


def ejudge_dump_report(contest_id, run_id):
    name_report_file = 'report_' + run_id + '.xml'
    contest_path = ejudge_util.get_contest_path(contest_id)
    report_path = contest_path + 'report/' + name_report_file
    session_key = ejudge_util.get_session_key(contest_id)
    command = ['/opt/ejudge/bin/ejudge-contests-cmd',
               contest_id,
               'dump-report',
               '--session',
               session_key,
               run_id, '>',
               report_path]
    cmd_str = ''
    for arg in command:
        cmd_str += arg + ' '
    report_file = 1
    DEVNULL = open(devnull, 'wb')
    while report_file != 0:
        report_file = subprocess.call(cmd_str, shell=True,
                                      stdout=DEVNULL, stderr=DEVNULL)
    return True

# coding=utf8

import time
import logging
import os
import subprocess
import xml.etree.ElementTree as etree
from os import devnull

import ejudge_util
import error as e

logger = logging.getLogger('edx-ejudge-grader')
ROOT = os.path.dirname(os.path.realpath(__file__))+'/'

def grader(response, grader_payload):
    contest_id = ejudge_util.contest_id_get(grader_payload['course_name'])
    problem_exist = ejudge_util.problem_exist(contest_id,
                                              grader_payload['problem_name'])
    if not contest_id or not problem_exist:
        ejudge_util.task_create(grader_payload)
        contest_id = ejudge_util.contest_id_get(grader_payload['course_name'])
    check_payload = ejudge_util.grader_payload_check(grader_payload,
                                                     ejudge_util.contest_path_get(
                                                         contest_id),
                                                     grader_payload[
                                                         'problem_name'])
    if check_payload:
        ejudge_util.grader_payload_update(check_payload, grader_payload)
    result = run_grade_in_ejudge(response, grader_payload)
    return result


def run_grade_in_ejudge(response, grader_payload):
    response_file = open(ROOT+'response.txt', 'w')
    response_file.write(response.encode('utf-8'))
    response_file.close()
    contest_id = ejudge_util.contest_id_get(grader_payload['course_name'])
    problem_name = grader_payload['problem_name']
    lang = grader_payload['lang_short_name']
    run_id = ejudge_submit_run(contest_id, problem_name, lang)
    if not run_id:
        ejudge_util.session_file_update(contest_id)
        run_id = ejudge_submit_run(contest_id, problem_name, lang)
    if not run_id:
        raise e.GraderException("Ejudge didn`t started submit run")
    run_id = run_id.strip()
    report = ejudge_dump_report(contest_id, run_id)
    if not report:
        pass
    result = pars_report(contest_id, run_id)
    return result


def pars_report(contest_id, run_id):
    result = dict()
    contest_path = ejudge_util.contest_path_get(contest_id)
    name_report_file = 'report_' + run_id + '.xml'
    del_str_in_report_xml(contest_path, name_report_file)
    result_xml = etree.parse(contest_path + 'report/' + name_report_file)
    tests = result_xml.getroot().find("tests")
    if tests is None:
        raise e.StudentResponseCompilationError
    test_tag = tests.findall("test")
    test_ok = 0
    tests = {}
    if not test_tag:
        result['success'] = False
        result['score'] = 0
        return result
    for i in test_tag:
        status = i.attrib['status']
        num = int(i.attrib['num'])
        if status == 'OK':
            test_ok += 1
            tests[num] = 'OK'
        elif status == 'WA':
            tests[num] = 'Неправильный ответ'
        elif status == 'RT':
            tests[num] = 'Ошибка выполнения'
        elif status == 'CE':
            tests[num] = 'Ошибка компиляции'
        elif status == 'PT':
            tests[num] = 'Частичное решение'
        elif status == 'PE':
            tests[num] = 'Ошибка представления ответа'
        elif status == 'CF':
            tests[num] = 'Ошибка тестовых данных'
        else:
            tests[num] = status
    result['tests'] = tests
    if test_ok != len(test_tag):
        result['success'] = False
        result['score'] = 0
    else:
        result['success'] = True
        result['score'] = 1
    compiler_out = result_xml.getroot().find("compiler_output").text
    if compiler_out:
        result['compiler_output'] = compiler_out
    logger.info("Report pars.result=" + str(result))
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
    session_key = ejudge_util.session_key_get(contest_id)
    command = ['/opt/ejudge/bin/ejudge-contests-cmd',
               str(contest_id),
               'submit-run',
               '--session',
               session_key,
               problem_name,
               lang,
               ROOT+'response.txt']
    submit_run = subprocess.Popen(command, stdout=subprocess.PIPE)
    run_id, err = submit_run.communicate()
    logger.info('run id = ' + run_id + ' contest_id = ' + contest_id)
    return run_id


def ejudge_dump_report(contest_id, run_id):
    name_report_file = 'report_' + run_id + '.xml'
    contest_path = ejudge_util.contest_path_get(contest_id)
    report_path = contest_path + 'report/' + name_report_file
    session_key = ejudge_util.session_key_get(contest_id)
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
    start = time.time()
    while report_file != 0:
        report_file = subprocess.call(cmd_str, shell=True,
                                      stdout=DEVNULL, stderr=DEVNULL)
        finish = time.time()
        if (finish - start) > 15:
            raise e.GraderException("Not generate report file")
    logger.info('Get report file')
    return True


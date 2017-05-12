# coding=utf8
import csv
import json
import logging
import os
import random
import subprocess
import xml.etree.ElementTree as etree


def task_create(grader_payload):
    contest_name = grader_payload['course_name']
    problem_name = grader_payload['problem_name']
    problem_type = grader_payload['problem_type']
    lang_name = grader_payload['lang_short_name']
    test_data = grader_payload['input_data']
    answer_data = grader_payload['output_data']

    contest_id = contest_id_get(contest_name)
    if not contest_id:
        contest_id = contest_id_create(contest_name)
        contest_xml_create(contest_name, contest_id)
        contest_path = dir_structure_create(contest_id)
        serve_cfg_create(contest_path, lang_name, problem_name, problem_type)
        problem_dir_create(problem_name, contest_path)
        test_answer_data_create(problem_name, contest_path, test_data,
                                answer_data)
        session_file_update(contest_id)
        logging.info('Contest files create!')
    elif not problem_exist(contest_id, problem_name):
        problem_create(problem_name, problem_type, contest_id, lang_name,
                       test_data,
                       answer_data)
        logging.info('Problem create')
    grader_payload_save(grader_payload, contest_path_get(contest_id),
                        problem_name)


def contest_id_get(contest_name):
    try:
        file = open('./contest_name_to_id.json', 'r')
    except IOError:
        logging.warning('Not found file: contest_name_to_id.json')
        logging.info("create json contest name to id")
        contest_name_id_json_create()
    contest_table = json.load(file)
    file.close()
    if contest_name in contest_table:
        return str(contest_table[contest_name])
    else:
        return False


def contest_id_create(contest_name):
    file = open('./contest_name_to_id.json', 'r')
    contest_table = json.load(file)
    file.close()
    contest_table[contest_name] = str(len(contest_table) + 1)
    outfile = open('./contest_name_to_id.json', 'w')
    json.dump(contest_table, outfile)
    outfile.close()
    return contest_table[contest_name]


def contest_xml_create(contest_name, contest_id):
    name_xml = (6 - len(contest_id)) * '0' + str(contest_id) + '.xml'
    root = etree.Element('contest', attrib={'id': contest_id,
                                            'disable_team_password': 'yes',
                                            'personal': 'yes', 'managed': 'yes',
                                            'run_managed': 'yes'})
    name = etree.SubElement(root, 'name')
    name.text = contest_name
    name_en = etree.SubElement(root, 'name_en')
    name_en.text = contest_name
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
    cap.text = 'MASTER_SET,'
    etree.SubElement(root, 'contestants',
                     attrib={'min': '1', 'max': '1', 'initial': '1'})
    tree = etree.ElementTree(root)
    tree.write('/home/judges/data/contests/' + name_xml)


def contest_name_id_json_create():
    if os.path.exists('./contest_name_to_id.json'):
        return True
    path = '/home/judges/data/contests/'
    list_files = os.listdir(path)
    name_to_id = dict()
    for item in list_files:
        if item.endswith('.xml'):
            xml = etree.parse(path + item)
            root = xml.getroot()
            contest_id = root.attrib['id']
            name = root.find('name_en').text
            if id == 'auto':
                contest_id = item.replace('0', ' ').strip()
            name_to_id[name] = str(contest_id)
    json.dump(name_to_id, open('contest_name_to_id.json', 'w'))


def contest_path_get(contest_id):
    name_dir_contest = (6 - len(contest_id)) * '0' + str(contest_id) + '/'
    contest_path = '/home/judges/' + name_dir_contest
    return contest_path


def dir_structure_create(contest_id):
    name_dir_contest = (6 - len(contest_id)) * '0' + str(contest_id) + '/'
    contest_path = '/home/judges/' + name_dir_contest
    os.makedirs(contest_path)
    os.makedirs(contest_path + 'conf/')
    os.makedirs(contest_path + 'problems/')
    os.makedirs(contest_path + 'var/')
    os.makedirs(contest_path + 'report/')
    return contest_path


def serve_cfg_create(contest_path, lang_name, problem_name, problem_type):
    serve = open(contest_path + 'conf/serve.cfg', 'w')
    global_param = ['# -*- coding: utf-8 -*-', '# $Id$', 'contest_time = 0',
                    'score_system = acm',
                    'compile_dir = "../../compile/var/compile"',
                    'team_enable_rep_view',
                    'ignore_compile_errors',
                    'problem_navigation',
                    'rounding_mode = floor',
                    'cr_serialization_key = ' + str(
                        random.randint(10000, 99999)),
                    'enable_runlog_merge',
                    'advanced_layout',
                    'enable_l10n',
                    'team_download_time = 0',
                    'cpu_bogomips = 4533']
    lang_param = lang_param_get(lang_name)
    problem_param = problem_param_get(problem_name, problem_type)
    tester_param = tester_param_get()
    all_param = global_param
    all_param.extend(lang_param)
    all_param.extend(problem_param)
    all_param.extend(tester_param)
    for row in all_param:
        serve.write(row + '\n')
    serve.close()


def problem_param_get(problem_name, problem_type):
    param = [
        '[problem]',
        'short_name = ' + '"' + problem_name + '"',
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
        'time_limit = 5',
        'real_time_limit = 15',
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


def problem_dir_create(problem_name, contest_path):
    problem_path = contest_path + 'problems/' + problem_name + '/'
    os.makedirs(problem_path)
    os.makedirs(problem_path + 'tests')


def problem_exist(contest_id, problem_name):
    if contest_id:
        name_dir_contest = (6 - len(contest_id)) * '0' + str(contest_id) + '/'
        contest_path = '/home/judges/' + name_dir_contest + 'problems/'
        problems_list = os.listdir(contest_path)
        if problem_name in problems_list:
            return True
        else:
            return False
    return False


def problem_create(problem_name, problem_type, contest_id, lang_name, test_data,
                   answer_data):
    contest_path = contest_path_get(contest_id)
    problem_dir_create(problem_name, contest_path)
    test_answer_data_create(problem_name, contest_path, test_data, answer_data)
    problem_add_in_serve(contest_path, problem_name, problem_type)
    lang_add_in_serve(lang_name, contest_path)
    makefile_create(contest_path, problem_name)


def problem_add_in_serve(contest_path, problem_name, problem_type):
    problem_param = problem_param_get(problem_name, problem_type)
    serve_path = contest_path + 'conf/serve.cfg'
    with open(serve_path, 'a') as f:
        f.write('\n')
        for row in problem_param:
            f.write(row + '\n')


def lang_param_get(lang_short_name):
    lang_id = lang_id_get(lang_short_name)
    param = ['\n[language]']
    file = open('./programm_lang/' + lang_id, 'r')
    param.extend(list(file))
    return param


def lang_id_get(lang_short_name):
    file = open('./lang_short_to_id.csv', 'r')
    lang_list = csv.DictReader(file, delimiter=';', skipinitialspace=True)
    for lang in lang_list:
        if lang['name'] == lang_short_name:
            return lang['id']
    return False


def lang_del_in_serve(lang_short_name, contest_path):
    serve = open(contest_path + '/conf/serve.cfg', 'r')
    lang_id = lang_id_get(lang_short_name)
    param = serve.readlines()
    index = 0
    flag = False
    while not flag:
        try:
            lang = param.index('[language]\n', index)
        except ValueError:
            flag = True
            break
        if param[lang + 1].endswith(str(lang_id) + '\n'):
            param.pop(lang)
            while param[lang] != '\n' and not param[lang].startswith('['):
                param.pop(lang)
        else:
            index = lang + 1
    serve.close()
    serve = open(contest_path + '/conf/serve.cfg', 'w')
    for row in param:
        serve.write(row)
    serve.close()


def lang_add_in_serve(lang_short_name, contest_path):
    serve = open(contest_path + '/conf/serve.cfg', 'a')
    lang_param = lang_param_get(lang_short_name)
    for row in lang_param:
        serve.write(row + '\n')
    serve.close()


def test_answer_data_create(problem_name, contest_path, test_data, answer_data):
    test_path = contest_path + 'problems/' + problem_name + '/' + 'tests/'
    num_test = 1
    for i in range(0, len(test_data)):
        file_dat = open(test_path + '00' + str(num_test) + '.dat', 'w')
        file_ans = open(test_path + '00' + str(num_test) + '.ans', 'w')
        file_dat.write(test_data[i])
        file_ans.write(answer_data[i])
        file_dat.close()
        file_ans.close()
        num_test += 1


def tester_param_get():
    param = ['\n[tester]',
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


def grader_payload_save(grader_payload, contest_path, problem_name):
    file_payload = contest_path + 'problems/' + problem_name + '/' + 'grader_payload.json'
    json.dump(grader_payload, open(file_payload, 'w'))


def grader_payload_check(new_payload, contest_path, problem_name):
    file_payload = contest_path + 'problems/' + problem_name + '/' + 'grader_payload.json'
    payload = json.load(open(file_payload, 'r'))
    old_test = payload['input_data']
    old_answer = payload['output_data']
    new_test = new_payload['input_data']
    new_answer = new_payload['output_data']
    old_lang = payload['lang_short_name']
    new_lang = new_payload['lang_short_name']
    change_list = list()
    if old_lang != new_lang:
        change_list.append('lang_short_name')
    if old_test != new_test:
        change_list.append('input_data')
    if old_answer != new_answer:
        change_list.append('output_data')
    logging.info("check grader payload. change list = " + str(change_list))
    return change_list


def grader_payload_update(change_list, grader_payload):
    contest_id = contest_id_get(grader_payload['course_name'])
    contest_path = contest_path_get(contest_id)
    lang = grader_payload['lang_short_name']
    problem_name = grader_payload['problem_name']
    test_data = grader_payload['input_data']
    answer_data = grader_payload['output_data']
    if 'input_data' in change_list or 'output_data' in change_list:
        test_answer_data_create(problem_name, contest_path, test_data,
                                answer_data)
        logging.info('Test and answer data update')
    if 'lang_short_name' in change_list:
        lang_del_in_serve(lang, contest_path)
        lang_add_in_serve(lang, contest_path)
        logging.info('Languages update')
    grader_payload_save(grader_payload, contest_path, problem_name)


def session_file_update(contest_id):
    session_file_name = session_file_name_get(contest_id)
    command = '/opt/ejudge/bin/ejudge-contests-cmd ' + contest_id + ' master-login ' + session_file_name
    file_login = open('login', 'r')
    login = file_login.readline().strip()
    password = file_login.readline()
    command = command + ' ' + login + ' ' + password
    subprocess.call(command, shell=True)
    logging.info("session file updated")


def session_file_name_get(contest_id):
    name = '/home/ejudge/sessions/' + contest_id + '.pwd'
    return name


def session_key_get(contest_id):
    name = session_file_name_get(contest_id)
    session_file = open(name, 'r')
    key = session_file.read().strip()
    session_file.close()
    return key


def makefile_create(contest_path, problem_name):
    makefile = ['### BEGIN ejudge auto-generated makefile ###',
                'EJUDGE_PREFIX_DIR ?= /opt/ejudge',
                'EJUDGE_CONTESTS_HOME_DIR ?= /home/judges',
                'EJUDGE_SERVER_BIN_PATH ?= /opt/ejudge/libexec/ejudge/bin',
                'EXECUTE = ${EJUDGE_PREFIX_DIR}/bin/ejudge-execute',
                'EXECUTE_FLAGS =  --use-stdin --use-stdout --test-pattern=%03d.dat --corr-pattern=%03d.ans',
                'NORMALIZE = ${EJUDGE_SERVER_BIN_PATH}/ej-normalize',
                'NORMALIZE_FLAGS = --workdir=tests --test-pattern=%03d.dat --corr-pattern=%03d.ans --type=nl',
                'all :',
                'check_settings : all normalize',
                'normalize :',
                '	${NORMALIZE} ${NORMALIZE_FLAGS} --all-tests',
                'clean :',
                '	-rm -f *.o *.class *.exe *~ *.bak',
                '### END ejudge auto-generated makefile ###'
                ]
    name = contest_path + 'problems/' + problem_name + '/Makefile'
    file = open(name, 'w')
    for row in makefile:
        file.write(row)
    file.close()

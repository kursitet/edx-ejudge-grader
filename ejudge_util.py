# coding=utf8
import csv
import json
import os
import xml.etree.ElementTree as etree


def create_task(grader_payload):
    contest_name = grader_payload['course_name']
    problem_name = grader_payload['problem_name']
    problem_type = grader_payload['problem_type']
    lang_name = grader_payload['lang_short_name']
    test_data = grader_payload['input_data']
    answer_data = grader_payload['output_data']

    contest_id = get_contest_id(contest_name)
    if not contest_id:
        contest_id = create_contest_id(contest_name)
        create_contest_xml(contest_name, contest_id)
        contest_path = create_dir_structure(contest_id)
        create_serve_cfg(contest_path, lang_name, problem_name, problem_type)
        create_problem_dir(problem_name, contest_path)
        create_test_answer_data(problem_name, contest_path, test_data,
                                answer_data)
        print 'Contest files create!'
    elif not problem_exist(contest_id, problem_name):
        create_problem(problem_name, problem_type, contest_id, test_data,
                       answer_data)
        print 'Problem create'
    save_grader_payload(grader_payload, get_contest_path(contest_id),
                        problem_name)


def get_contest_id(contest_name):
    file = open('./contest_name_to_id.json', 'r')
    contest_table = json.load(file)
    file.close()
    if contest_name in contest_table:
        return contest_table[contest_name]
    else:
        return False


def create_contest_id(contest_name):
    file = open('./contest_name_to_id.json', 'r')
    contest_table = json.load(file)
    file.close()
    contest_table[contest_name] = str(len(contest_table) + 1)
    outfile = open('./contest_name_to_id.json', 'w')
    json.dump(contest_table, outfile)
    outfile.close()
    return contest_table[contest_name]


def create_contest_xml(contest_name, contest_id):
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
    cap.text = 'FULL_SET,'
    etree.SubElement(root, 'contestants',
                     attrib={'min': '1', 'max': '1', 'initial': '1'})
    tree = etree.ElementTree(root)
    tree.write('/home/judges/data/contests/' + name_xml)


def create_dir_structure(contest_id):
    name_dir_contest = (6 - len(contest_id)) * '0' + str(contest_id) + '/'
    contest_path = '/home/judges/' + name_dir_contest
    os.makedirs(contest_path)
    os.makedirs(contest_path + 'conf/')
    os.makedirs(contest_path + 'problems/')
    os.makedirs(contest_path + 'var/')
    return contest_path


def create_serve_cfg(contest_path, lang_name, problem_name, problem_type):
    serve = open(contest_path + 'conf/serve.cfg', 'w')
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
    problem_param = get_problem_param(problem_name, problem_type)
    tester_param = get_tester_param()
    all_param = global_param
    all_param.extend(lang_param)
    all_param.extend(problem_param)
    all_param.extend(tester_param)
    for row in all_param:
        serve.write(row + '\n')
    serve.close()


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


def get_problem_param(problem_name, problem_type):
    param = [
        '[problem]',
        'short_name = ' + '"' + problem_name + '"',
        'long_name = ""',
        'type = ' + problem_type,
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


def create_problem_dir(problem_name, contest_path):
    problem_path = contest_path + 'problems/' + problem_name + '/'
    os.makedirs(problem_path)
    os.makedirs(problem_path + 'tests')


def create_test_answer_data(problem_name, contest_path, test_data, answer_data):
    test_path = contest_path + 'problems/' + problem_name + '/' + 'tests/'
    num_test = 1
    if len(test_data) == len(answer_data):
        for i in range(0, len(test_data)):
            file_dat = open(test_path + '00' + str(num_test) + '.dat', 'w')
            file_ans = open(test_path + '00' + str(num_test) + '.ans', 'w')
            file_dat.write(test_data[i])
            file_ans.write(answer_data[i])
            file_dat.close()
            file_ans.close()
            num_test += 1


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


def get_contest_path(contest_id):
    name_dir_contest = (6 - len(contest_id)) * '0' + str(contest_id) + '/'
    contest_path = '/home/judges/' + name_dir_contest
    return contest_path


def create_problem(problem_name, problem_type, contest_id, test_data,
                   answer_data):
    contest_path = get_contest_path(contest_id)
    create_problem_dir(problem_name, contest_path)
    create_test_answer_data(problem_name, contest_path, test_data, answer_data)
    problem_add_in_serve(contest_path, problem_name, problem_type)


def problem_add_in_serve(contest_path, problem_name, problem_type):
    problem_param = get_problem_param(problem_name, problem_type)
    serve_path = contest_path + 'conf/serve.cfg'
    with open(serve_path, 'a') as f:
        f.write(problem_param)


def save_grader_payload(grader_payload, contest_path, problem_name):
    file_payload = contest_path + problem_name + '/' + 'grader_paload'
    json.dump(grader_payload, file_payload)


def check_grader_payload(new_payload, contest_path, problem_name):
    file_payload = contest_path + problem_name + '/' + 'grader_paload'
    payload = json.load(file_payload)
    old_test = payload['input_data']
    old_answer = payload['output_data']
    new_test = new_payload['input_data']
    new_answer = new_payload['output_data']
    change_list = list()
    if old_test != new_test:
        change_list.append('input_data')
    if old_answer != new_answer:
        change_list.append('output_data')
    return change_list


def update_payload(change_list, grader_payload):
    contest_id = get_contest_id(grader_payload['contest_name'])
    contest_path = get_contest_path(contest_id)
    problem_name = grader_payload['problem_name']
    test_data = grader_payload['input_data']
    answer_data = grader_payload['output_data']
    create_test_answer_data(problem_name, contest_path, test_data, answer_data)
    save_grader_payload(grader_payload, contest_path, problem_name)
    print 'Test and answer data update'

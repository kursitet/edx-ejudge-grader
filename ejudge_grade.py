import subprocess
import time
import ejudge_util
import xml.etree.ElementTree as etree


def grade_in_ejudge(response, grader_playload):
    response_file = open('response.txt', 'w')
    response_file.write(response)
    response_file.close()
    contest_id = 2
    problem_name ='A'
    lang = 'gcc'
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
    contest_path = get_contest_path(contest_id)
    command = '/opt/ejudge/bin/ejudge-contests-cmd ' + str(
        contest_id) + ' dump-report' + ' /home/ejudge/session.pwd ' + run_id + ' >' + contest_path + 'report/' + name_report_file
    print command
    # КОСТЫЛЬ.это время, за которое еджадж должен проверить работу. сделать проверку в цикле
    time.sleep(2)
    subprocess.call(command, shell=True)
    rezult = dict()
    del_str_in_report_xml(contest_path, name_report_file)
    result_xml = etree.parse(contest_path + 'report/' + name_report_file)
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
    print 'del 2 str = OK!'
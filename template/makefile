### BEGIN ejudge auto-generated makefile ###
EJUDGE_PREFIX_DIR ?= /opt/ejudge
EJUDGE_CONTESTS_HOME_DIR ?= /home/judges
EJUDGE_SERVER_BIN_PATH ?= /opt/ejudge/libexec/ejudge/bin
EXECUTE = ${EJUDGE_PREFIX_DIR}/bin/ejudge-execute
EXECUTE_FLAGS =  --use-stdin --use-stdout --test-pattern=%03d.dat --corr-pattern=%03d.ans
NORMALIZE = ${EJUDGE_SERVER_BIN_PATH}/ej-normalize
NORMALIZE_FLAGS = --workdir=tests --test-pattern=%03d.dat --corr-pattern=%03d.ans --type=nl
all :
check_settings : all normalize
normalize :
	${NORMALIZE} ${NORMALIZE_FLAGS} --all-tests
clean :
	-rm -f *.o *.class *.exe *~ *.bak
### END ejudge auto-generated makefile ###

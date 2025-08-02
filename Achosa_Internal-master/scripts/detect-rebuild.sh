#!/bin/bash
# may need to be run with `bash` command instead of `sh` command

BRANCH="ao-1049-detect-rebuild-script" # human readable part of the name returned by printenv PGDATABASE that corresponds to the name of the branch

PGDB=$(printenv PGDATABASE)
if [[ $PGDB =~ $BRANCH ]]; then # check that we're on the right branch before doing anything
	bash /home/odoo/src/user/scripts/createLogDir.sh
	LOG_PATH=~/src/user/scripts/logs/pgdb.log
	TIME=$(date +%s)
	if test -f "$LOG_PATH"; then # check if file at $LOG_PATH already exists
		PGDB_TXT=$(awk 'END{print $1}' $LOG_PATH)
		if [ "$PGDB" != "$PGDB_TXT" ]; then # compare file contents to command result
			echo "Updated './logs/pgdb.log'"
			# execute commands here #
			LINE="$PGDB $TIME"
			echo $LINE >> $LOG_PATH # update file at $LOG_PATH
		fi
	else
		echo "Created './logs/pgdb.log'"
		echo "PGDB UnixTimestamp" > $LOG_PATH # create file at $LOG_PATH since it does not exist yet
		LINE="$PGDB $TIME"
		echo $LINE >> $LOG_PATH
	fi
else
	echo "Branch is NOT ${BRANCH}!"
fi

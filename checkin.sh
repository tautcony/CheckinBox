#!/usr/bin/env bash
export PIPENV_IGNORE_VIRTUALENVS=1

BASE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "${BASE_PATH}" || exit 1


ret=0
checkin_list=$(find . -type f -name "checkin.py" -not -path "./template/*")

for checkin in ${checkin_list}
do
  echo "${checkin} matched, executing..."
  if ! pipenv run python3 "${checkin}"; then
    ret=1
  fi
done

exit "${ret}"

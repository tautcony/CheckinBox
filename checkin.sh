#!/usr/bin/env bash
BASE_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

cd "${BASE_PATH}" || exit 1

checkin_list=$(find . -type f -name "checkin.py" -not -path "./template/*")

ret=0

for checkin in ${checkin_list}
do
  if not pipenv run python3 "${checkin}"; then
    ret=1
  fi
done

exit "${ret}"

# compatibility with MacOS ( https://stackoverflow.com/a/9484017 )
function absolute_path() {
  DIR="${1%/*}"
  (cd "$DIR" && echo "$(pwd -P)")
}

export PYTHONPATH=$(absolute_path ../../)
echo "PYTHONPATH = ${PYTHONPATH}"

ERDPY="python3.8 -m erdpy.cli"
SANDBOX=./testdata-out/SANDBOX
USERS=~/elrondsdk/testwallets/latest/users
VALIDATORS=~/elrondsdk/testwallets/latest/validators
DENOMINATION="000000000000000000"
PROXY="http://localhost:7950"
CHAIN_ID="localnet"

cleanSandbox() {
    rm -rf ${SANDBOX}
    mkdir -p ${SANDBOX}
}

assertFileExists() {
    if [ ! -f "$1" ]
    then
        echo "Error: file [$1] does not exist!" 1>&2
        return 1
    fi

    return 0
}

assertFileDoesNotExist() {
    if [ -f "$1" ]
    then
        echo "Error: expected file [$1] to be missing, but it exists!" 1>&2
        return 1
    fi

    return 0
}

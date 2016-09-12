# temporary pyenv installation to get latest pypy until the travis
# container infra is upgraded
if [[ "${TOXENV}" = pypy* ]]; then
    git clone https://github.com/yyuu/pyenv.git ~/.pyenv
    PYENV_ROOT="$HOME/.pyenv"
    PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    pyenv install "pypy-$PYPY_VERSION"
    pyenv global "pypy-$PYPY_VERSION"

    pip install --upgrade tox

    pyenv rehash
fi


pip install --upgrade tox

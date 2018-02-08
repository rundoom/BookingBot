.PHONY: docs
install:
	pip install pipenv --upgrade
	pipenv install --dev --skip-lock

flake8:
	pipenv run flake8 bookboot

coverage:
	pipenv run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=requests tests
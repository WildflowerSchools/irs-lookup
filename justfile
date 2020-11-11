stage := "dev"

build:
    python setup.py install build

install-dev:
    pip install -e ".[development]"

clean:
    python setup.py clean --all

fmt:
    autopep8 --aggressive --recursive --in-place ./irs_lookup/

deploy: build
    pip freeze | grep -v 'irs-lookup' > requirements.txt
    serverless deploy --stage {{stage}}

build-poppler:
    #!/usr/bin/env sh
    setopt +o nomatch RM_STAR_SILENT
    cd poppler-layer
    mkdir -p layer && rm -rf ./layer/* && cd layer
    curl -LO https://github.com/WildflowerSchools/aws-lambda-poppler-layer/releases/download/1.0.1/poppler.zip
    unzip poppler.zip
    rm poppler.zip
    cd ..
    sls deploy
    cd ..

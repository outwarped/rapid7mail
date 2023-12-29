# Email Python exec bot

Runs SMTP server. Checks if emails contain inside the body a keyword and an attached python file, the file is executed with python and send the output back to the recipient inside the email body

## Requirements

* Python 3.12
* poetry
* Docker (optional)

## Build

Clone repo:

```bash
git clone git@github.com:outwarped/rapid7mail.git
cd rapid7mail
```

Install project dependencies and development dependencies

```bash
poetry install
```

Build main docker image

```bash
docker build -t application . 
```

## Local Run

Start mock SMTP server where resutls are going to be sent

```bash
docker run -ti --network host application \
    server
```

Start main application:

```bash
docker run -ti --network host application \
    --agent-email='agent@localhost' \
    --allowed-emails='anonymous@localhost' \
    --body-keywords='banana'
```

Send test email:

```bash
docker run -ti --network host \
    -v ${PWD}/rapid7mail/tools/eval_sample.py:/app/eval_sample.py \
    application \
    client \
        --email-from='anonymous@localhost' \
        --email-to='agent@localhost' \
        --email-subject="Subject" \
        --email-body="Eat this banana" \
        --email-attachment=/app/eval_sample.py
```

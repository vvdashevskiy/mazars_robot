# mazars_robot

## SemanticScholar robot description

The robot is used to automate the process of https://semanticscholar.org literature collection for the user-defined topic. Result of the process is an email with attached zip archive.

#### Used libraries

* [dotenv](https://www.npmjs.com/package/dotenv) - module that loads environment variables from a .env file
* [beautifulsoup4](https://pypi.org/project/beautifulsoup4/) - web pages scrapper
* [smtplib](https://docs.python.org/3/library/smtplib.html) \ [email](https://docs.python.org/3/library/email.examples.html) - email creating and sending

#### Algorithm 

1. User defines a topic, number of pages, and receiver of the resulting email
2. Robot uses API to parse articles by topic
3. Robot scraps article's info and downloads source file if available
4. Robot writes all info zip archive and sends email

#### How to use

1. Clone git repository to your computer
2. Install packages from ```requirements.txt```
3. Make setup correcting ```.emv``` file
4. Run script python ```main.py``` --topic="yourtopic" --pages=yourpagescount --pdf --email=targetemail

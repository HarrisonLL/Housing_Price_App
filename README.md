## Simple House Price Monitor app

- This app monitors monthly house price changes. Since it depends on scrapped house price, scraping
  would be done manually to prevent website blocking. To automate this part, an ideal solution would be using Cron Job.
  After monthly scraping, do the following command to sync database and the app will show the updates right after.
- For data security purpose, I remove the scraping part from the git repo.
- The app is intended for individual user to monitor their local housing price, not intended for business use whatsoever. Therefore, user does not need to login the app.
- Current supported City: Princeton, NJ. NYC,NJ, Seattle,WA


![NYC](markdown_images/NYC.png)
![Princeton](markdown_images/Princeton.png)
![Seattle](markdown_images/Seattle.png)


# initialize the Database
$ flask --app housing init-db

# update the Database (crawl data first then update the DB)
$ cd ./housing/utils/
$ python <some-crawler.py>
$ flask --app housing update-db-monthly

# run the app
$ flask --app housing --debug run

Reference:
The fUll tutorial to create a flask app: https://flask.palletsprojects.com/en/2.2.x/tutorial/

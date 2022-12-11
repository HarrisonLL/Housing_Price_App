# Simple Housing Price Monitor app

# Intro
- This app shows housing price heatmap by location, it also monitors monthly house price changes. Since it depends on scrapped house price, scraping
  would be done manually to prevent website blocking. To automate this part, an ideal solution would be using Cron Job.
  After monthly scraping, do the following command to sync database and the app will show the updates right after.
- For data security purpose, I remove the scraping part from the git repo.
- The app is intended for individual user to have an insight of their local housing price to make wise investment decisions, not intended for business use whatsoever. Therefore, I do not add user log in functionalities.
- Current supported City: Princeton, NJ. NYC,NJ, Seattle,WA


![NYC](markdown_images/NYC.png)
![Princeton](markdown_images/Princeton.png)
![Seattle](markdown_images/Seattle.png)

## create a conda env and activate it
```
$ conda create -n housing python=3.8
$ conda activate housing
$ pip install -r requirements.txt
```

## initialize the Database
```
$ flask --app housing init-db
```


## update the Database (scrape data first then update the DB)
```
$ cd ./housing/utils/
$ python <some-crawler.py>
$ flask --app housing update-db-monthly <month in the format of year-month>
```

## run the app (go to http://localhost:5000)
```
$ flask --app housing --debug run
```

Reference:
The fUll tutorial to create a flask app: https://flask.palletsprojects.com/en/2.2.x/tutorial/

# Adaptive Quiz App

Adaptive Quiz app version 0.1 
- Prototype version

- Based on 'app' folder
- All models are on 'app/model' including algorithm for adaptive quiz
- 'static' and 'template' contain JavaScript and HTML/CSS


## Deployment

Hosting on virtual private server

 
## Created Users (student000 to student050)
Registration system is required for admin

## Operation Procedure
----
0. Install dependencies on your system with console prompt `pip install -r requirements.txt`
1. Go to model_usercontrol.py and create user via SystemAdminClass.registration (example provided)
2. Start the server_frontend.py from console prompt, e.g. python server_frontend.py 0 (debugging mode) python server_frontend.py 1 (production mode)
3. Go to webpage (simple case is to go to http://localhost)
4. Login with created credential from step 1

## Operation Scenarios (Tentative User Story)
----
1. After completed *Operation Procedure* it will lead you to Pre-test session
2. Complete the Pre-test session, webpage will redirect you to homepage (Must complete, otherwise you will not be able to go to main application)
3. There will be 3 pages:
    - `Overview`, a page to see your profile, mastery status, performance of ability and score
    - `Report`, a page to show your last attempt performance
    - `Setting`, a page to config your quiz session
4. From `Overview` page, simply click `Start Quiz` will direct you to `Disclaimer` page
    - There is an icon `Refreshing` (Togglable) which will switch between graph of performance of ability and performance of score
5. From `Disclaimer` page:
6. From `Setting` page:
    - `Timer` is to configure in each quiz session time limit (`-- No timer --` means timer will never expire), time runs out will force attempt to the completion
    - `Number of Questions` is to configure a number of questions in each module
    - `Maximum number of questions limit` is to configure the amount of questions that can be found (upto) for user in each attempt.
    - `Configuration` is to select module(s) or to let system randomly choose for you
    - `Setting` page will save the settings until user logs out
7. Once the quiz is started:
    - There will be timer (if one configures it)
    - `Abort the attempt` button will be shown (to abort the session), and the attempt will not be taken into account
    - First question will be automatically fetch
    - `Submit` button will be used to submit your answer, once submitted, it will be disabled until new question is fetched
    - `Next` button will be used to fetch next question, and to end the session if final question is submitted on answer
    - `Next` button will not be able to click until user submitted answer
8. For every question answered:
    - There will be an explanation and result show after answer submitted, even if it is correct or incorrect
    - `Show explanation` will be used to hide/show the explanation to question
9. Once the quiz is completed:
    - You will automatically be redirected to `Report` page
    - Performance score will be shown
    - Answer history will be shown
    - Each cell of `Answer history` can be clicked to see your session's question and answer, along with explanation
    - You can also submit any query that you have with provided form in `Report` page#

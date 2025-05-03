# Instructions

## Setup

### Prerequisites
All of these steps must be done before you begin setup

1. Have up-to-date version of Python installed on your system.
2. Have up-to-date version of Node.js and NPM installed on your system.
3. Download dataset from: `https://www.kaggle.com/datasets/irkaal/foodcom-recipes-and-reviews`
4. Extract dataset into `/backend/dataset/`

### Automated
There is an easy, automated way to setup and run the project.

Simply open a terminal in the root of the project (or navigate to it) and run `python run.py`.

This will:
- Create the virtual environment
- Install all needed libraries for both backend and frontend
- Create the database and populates it with the needed data
- Finally, start both backend and frontend servers

This process will take a while, and you might see some errors, but do not be afraid, just let it run until the servers have started.

### Manual
If for some reason the automated setup fails, you can do all the steps manually as a fallback.

1. Open terminal in the root of the project (or navigate to it)
2. Run `python -m venv venv`
3. On Windows `venv\Scripts\activate`, or on Unix systems `source venv/bin/activate`
4. Run `pip install -r backend/requirements.txt`
5. Run `cd backend` then `python webapp.py` for backend
6. Open a separate terminal in the root of the project (or navigate to it), then run `cd frontend` then `npm install` then finally `npm run dev` for frontend

## Using the System
Once all setup has been successfully completed, you can open your browser and go to `http://localhost:5173` to access the web application.

To run the system, simply open a terminal in the root of the project (or navigate to it) and run `python run.py`.
This will start both backend and frontend servers (in separate terminals).

To stop the servers, simply go to their respective terminals, then:
- For backend press `CTRL + C`
- For frontend press `CTRL + C` then type `y` and press `Enter`

The original terminal that was used to run `python run.py` can be closed any time after the servers have started.

If for some reason the backend server does not close properly, you can run `python run.py --cleanup` to shut it down.

# Testing
Automated tests are implemented and can be run like this:

1. Open a terminal in the root of the project (or navigate to it)
2. Run `python run.py --test`

# Troubleshoot
If there is a problem with the database:

1. Go to `/backend/database/` and delete `app_database.db`
2. Open a terminal in the root of the project (or navigate to it) and run `python run.py`

This should recreate the database and populate it with the needed data.

# Project Structure
`backend/`
- `components/` - parts of the Flask server architecture
- `database/` - database
- `dataset/` - dataset used for the system
- `modules/` - recommendation algorithms and utility functions
- `setup/` - load database with needed data

`frontend/`
- various configuration files, important files are found in `src/`
- `src/` - contains the frontend files

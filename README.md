![Lint-free](https://github.com/nyu-software-engineering/containerized-app-exercise/actions/workflows/lint.yml/badge.svg)

# Containerized App Exercise

Welcome to Chequemate 2.0, the premier place to scan receipts and split them with your friends.

This project is an extension of our [first specification project](https://github.com/software-students-spring2024/1-specification-exercise-bestswegroup) and [second project](https://github.com/software-students-spring2024/2-web-app-exercise-bswe) which defined and implemented a bill splitting web app. This exercise aims to build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

In this project, we redesigned the front end, containerized the web app and database, and added an OCR machine-learning container for receipt scanning and parsing.

# Team Members

[Edison Chen](https://github.com/ebc5802), [Natalie Wu](https://github.com/nawubyte), [Chelsea Li](https://github.com/qiaoxixi1), and [Jacklyn Hu](https://github.com/Jacklyn22)

# How To Run ChequeMate

First, rename the `env.sample` file to `.env` and make any necessary adjustments.

Next, from the root directory, run `docker compose up --build`

Finally, open `http://localhost:10000/` in your local browser to view our web app.

The three containers are connected through a docker network. Note that the OCR API key is from a free version, so it can only properly process a couple of requests per hour.

# Learnings + Limitations

We were able to utilize docker and docker compose to develop a multi-container app that leverages machine learning.

We ended up falling short again due to our inexperience with docker containers and transferring files properly between the database image and other images. We pivoted to using atlas clusters instead of localhost to host our mongodb database.

We are hopeful however, in the utility of our app and will continue to make improvements until we have a working bill-splitting OCR app.

# Credits

ML client based off tutorial by [NeuralNine](https://www.youtube.com/watch?v=dSCJ7DImGdA) using the asprise OCR API.

# Exercise Details

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

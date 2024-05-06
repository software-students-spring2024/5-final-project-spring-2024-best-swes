# Final Project

An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.


# Team Members

[Edison Chen](https://github.com/ebc5802), [Natalie Wu](https://github.com/nawubyte), [Chelsea Li](https://github.com/qiaoxixi1), and [Jacklyn Hu](https://github.com/Jacklyn22)

# How To View ChequeMate Online

You can view our upload online on Digital Ocean: http://161.35.189.70:10000/. This upload will only be available for the 2-month trial available as of May 2024.

# How To Run ChequeMate Locally

First, rename the `env.sample` file to `.env` and make any necessary adjustments including changing the OCR API key to a valid API key from mindee.

Next, from the root directory, run `docker compose up --build`

Finally, open `http://localhost:10000/` in your local browser to view our web app.
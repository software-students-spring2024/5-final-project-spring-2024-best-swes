# Final Project

[link to our project](http://161.35.189.70:10000)
An exercise to put to practice software development teamwork, subsystem communication, containers, deployment, and CI/CD pipelines. See [instructions](./instructions.md) for details.

# Team Members

[Edison Chen](https://github.com/ebc5802), [Natalie Wu](https://github.com/nawubyte), [Chelsea Li](https://github.com/qiaoxixi1), and [Jacklyn Hu](https://github.com/Jacklyn22)

# How To Run ChequeMate

First, rename the `env.sample` file to `.env` and make any necessary adjustments including changing the OCR API key to a valid API key from mindee.

Next, from the root directory, run `docker compose up --build`

Finally, open `http://localhost:10000/` in your local browser to view our web app.

# Docker Images 
- [Docker Hub repo](https://hub.docker.com/repository/docker/sennyy/5-final-project-spring-2024-best-swes/general)
- [Machine Learning Client](https://hub.docker.com/layers/sennyy/5-final-project-spring-2024-best-swes/latest/images/sha256-8e6f5dc5c28f64ee5f8deb15ed03da005c09c8933a5b3f9f6d3aca934774eb17?context=repo)
- [Webapp](https://hub.docker.com/layers/sennyy/5-final-project-spring-2024-best-swes/webapp/images/sha256-a2177768a9c1b34b5995fa325076f42fb24d56aeb087b8824f203efdae94cd96?context=repo)
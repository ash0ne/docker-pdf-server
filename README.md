# Docker PDF Server

![CI Status Badge](https://github.com/ash0ne/docker-pdf-server/actions/workflows/ci.yml/badge.svg)
![GitHub License](https://img.shields.io/github/license/ash0ne/docker-pdf-server)
[![Docker Image Version](https://img.shields.io/docker/v/a0ne/docker-pdf-server)](https://hub.docker.com/r/a0ne/docker-pdf-server)
![Docker Pulls](https://img.shields.io/docker/pulls/a0ne/docker-pdf-server)

Welcome to the Docker PDF Server! This project provides an ultra-minimalist PDF server running on Docker. Built with
Flask and HTML, it offers a no-nonsense, straightforward way to upload, delete, view, search, and serve PDFs.

## Why Docker PDF Server?

I developed this server out of a personal need for a quick, e-book-like viewing experience for my PDF library. Unlike
document organizers like Paperless-ngx or eBook focused apps like Calibre-web, Kavita etc., this server focuses solely
on delivering a simple way to upload, browse, search, and access PDF e-books for reading. When you click on a PDF,
it is served as is.

It is actually functionally similar to any typical client app for a NAS. However, this server brings the convenience of
browser-based access, allowing for quick viewing and on-the-go reading on any device.

<img src="screenshots/Home.png" alt="Alt text" style="width:70%;">

## What Docker PDF Server is not

- This server is not designed to be a comprehensive document organizer like Paperless-ngx.
- It lacks a database or any form of grouping/bookmarking system and relies solely on file system, potentially limiting
  scalability if you want to have anything over a few 1000 files.
- Basic HTTP authentication is implemented, but not OAuth. It is advisable not to expose the server publicly without additional
  security. I use this with Authelia running on my reverse-proxy.
- Currently, it lacks a folder system. Although this feature is simple enough to do and could be considered for future
  implementation.
- Error handling although basic covers most scenarios.

## Getting Started

Just run the below docker command replacing the username, password and secret with your preferred values, and you should
be up and running.

```
docker run -e DOCKER_PDF_SERVER_USER=<your-username> \
 -e DOCKER_PDF_SERVER_PASSWORD=<your-password> \
 -e DOCKER_PDF_SERVER_KEY=<your-random-secret-key> \
 -v /Users/writable/host/path/pdf-library:/app/library/ \
 -v /Users/writable/host/path/user-db:/app/instance/ \
 -p 3040:5000 ghcr.io/ash0ne/docker-pdf-server:latest
```

You can then access the app by going to `http://localhost:3040`

> Note: Starting the container without setting the env vars will start it with the default key, username and password

### User Management

Any version after 1.4.x, the default admin user configured through env vars `DOCKER_PDF_SERVER_USER` and `DOCKER_PDF_SERVER_PASSWORD`
can add additional admins, maintainers and readers

- **Admin** - Can add other users
- **Maintainer** - Cannot add users but can upload, delete files
- **Reader** - Can only read files

> Note: Because of how Basic HTTP auth works, the only way to switch user is to close and re-open the browser. 
> On MacOS, this means exiting the browser fully and re-opening it. If you have the user and password saved in the browser, 
> you might also have to delete that.

### Building and Running Locally for Development

- Get started by creating a python venv in this directory by running `python3 -m venv venv` or `python -m venv venv`
- Then run `source venv/bin/activate` on Linux/macOS.
- If on Windows, run `env/Scripts/activate.bat` in CMD or `env/Scripts/Activate.ps1`for PowerShell.
- Then run `pip install -r requirements.txt`
- After that, you can start your app server for development by running `python3 app.py` or `python app.py`
- If you want to build a docker image you can do so by running `docker build . -t docker-pdf-server:latest`

> Note: The default [Flask Secret Key](https://explore-flask.readthedocs.io/en/latest/configuration.html) is set to
> `super_secret_key` in the app and should be changed by setting the env var `DOCKER_PDF_SERVER_KEY`
>
> Similarly, the default user is `admin` and can be changed by setting the env var `DOCKER_PDF_SERVER_USER`
> and the default password is `password` and can be changed by setting the env var `DOCKER_PDF_SERVER_PASSWORD`

## Ideas and Enhancements

Feature development has been driven by personal use case, primarily centered around managing a few hundred PDFs
for reading. However, I might think of additions that maintain the server's lightweight nature, such as a folder
system etc.

Feel free to contribute or raise issues to improve the Docker PDF Server!

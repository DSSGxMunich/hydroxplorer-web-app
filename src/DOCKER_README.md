## Steps to run the docker image

In order to create a docker image of our application please follow the steps described below:

0. Install docker.
1. Clone this git repo.
2. Go to hydroxplorer-web-app/src on your terminal.
3. Type ```docker image build -t hydrant_app```
4. Type ```docker run -d -p 5000:5000 hydrant_app```
5. Go to localhost:5000 on your browser.
6. Done!

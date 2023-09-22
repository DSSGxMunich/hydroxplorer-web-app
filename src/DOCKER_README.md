## Steps to run the docker image
0. Install docker.
1. Clone the git repo.
2. Go to dssgx_fire_hydrant_range_finder/src on your terminal.
3. docker image build -t hydrant_app .
4. docker run -d -p 5000:5000 hydrant_app
5. Go to localhost:5000 on your browser.
6. Done!
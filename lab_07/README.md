# Lab 07 — Containerise and Prove Your AI Service

In the previous practice, we ran the AI service directly on an Ubuntu virtual machine. In this final Lab, we will package the same service as a Docker image, check that its behaviour is unchanged, and then apply the same approach to the team project.

Follow the reference demonstration with me first. Then work with your team project.

During the demonstration, keep the SSH terminal and your web browser visible. We will build the image, start the container, send two requests, inspect the evidence, and then replace the container.

## By the end of the practice

- The reference service runs from a Docker image.
- Another computer can reach its API.
- A valid image reaches prediction and an invalid file does not.
- The JSONL evidence remains after the container is replaced.
- Your team can start its project service again for the project defense.

## 1. Connect to the existing VM

Use the Ubuntu VM from Lab 06. The same SSH command works in macOS Terminal, Linux Terminal, and current Windows PowerShell:

```text
ssh <username>@<public-ip>
```

All remaining commands in the reference demonstration run inside the Ubuntu VM.

## 2. Download the final Lab files

Clone the released course materials into a new directory on the VM:

```bash
git clone https://github.com/naziherrahel/ai-implementation-technologies-students.git ~/ait-course-final-lab
cd ~/ait-course-final-lab/labs/lab_07/starter
```

If that directory already exists, update it instead:

```bash
cd ~/ait-course-final-lab
git pull
cd labs/lab_07/starter
```

## 3. Check Docker and the available disk space

```bash
docker --version
docker buildx version
df -h /
```

If Docker or Buildx is not found, install the Ubuntu packages:

```bash
sudo apt update
sudo apt install -y docker.io docker-buildx
sudo systemctl enable --now docker
```

Confirm that Docker can start a container:

```bash
sudo docker run --rm hello-world
```

## 4. Inspect the container boundary

The starter adds two files to the Lab 06 service:

- `Dockerfile` describes the Python runtime, installed packages, service files, and startup command.
- `.dockerignore` keeps local environments, secrets, model weights, generated evidence, and Git files outside the image build context.

Open them before building:

```bash
sed -n '1,200p' Dockerfile
sed -n '1,200p' .dockerignore
```

The image contains the service. The `.env` configuration and `reports/` evidence directory will be connected when the container starts.

## 5. Build and test the reference image

Prepare the runtime configuration and evidence directory:

```bash
cp .env.example .env
mkdir -p reports
```

Build the image:

```bash
sudo docker build -t ait-yolo-service:1 .
```

The first build downloads the Python base image and the required packages. On the course VM, this will usually take about 10 minutes.

Run the existing automated checks inside the image:

```bash
sudo docker run --rm ait-yolo-service:1 python -m unittest tests/test_app.py
```

Continue when the tests report `OK`.

## 6. Run the service from the image

```bash
sudo docker run --rm --name ait-yolo \
  -p 8000:8000 \
  --env-file .env \
  --mount type=bind,src="$(pwd)/reports",dst=/app/reports \
  ait-yolo-service:1
```

Keep this terminal open while the container is running.

The command makes three connections to the VM:

- `-p 8000:8000` publishes the API through the VM's port 8000;
- `--env-file .env` supplies the runtime configuration;
- `--mount ...` connects the container's evidence path to the VM's `reports/` directory.

## 7. Check the same two request paths

On your own computer, download the [Ultralytics bus image](https://ultralytics.com/images/bus.jpg) and keep a small text file ready. These are the two inputs for the demonstration.

In your browser, open:

- `http://<public-ip>:8000/health`
- `http://<public-ip>:8000/docs`

In `/docs`, open `POST /predict`, select **Try it out**, enter `req-cloud-001`, upload `bus.jpg`, and select **Execute**. The response should contain:

```json
"prediction_called": true
```

The first valid request may be slower because the container downloads `yolo26n.pt` before CPU inference.

Repeat the request with `req-cloud-002` and upload the text file. HTTP 400 is the expected response because the input is rejected before prediction. The response should contain:

```json
"action": "reject_input",
"prediction_called": false
```

Return to the SSH terminal and stop the container with `Ctrl+C`.

Check the saved decisions on the VM:

```bash
tail -n 2 reports/yolo_predictions.jsonl
```

The two lines should contain `req-cloud-001` and `req-cloud-002`.

## 8. Replace the container and check the evidence again

Start a new container from the same image, this time in the background:

```bash
sudo docker run -d --rm --name ait-yolo \
  -p 8000:8000 \
  --env-file .env \
  --mount type=bind,src="$(pwd)/reports",dst=/app/reports \
  ait-yolo-service:1
```

Check the startup output:

```bash
sudo docker logs ait-yolo
```

When the log shows that application startup is complete, open `http://<public-ip>:8000/health` again from your own computer. Then check the saved evidence on the VM:

```bash
tail -n 2 reports/yolo_predictions.jsonl
```

The new container should answer `/health`, and the two earlier request records should still be present.

The replacement container may show `"model_loaded": false` until it receives its first valid image. This does not affect the evidence saved in the VM's `reports/` directory.

Stop the reference container:

```bash
sudo docker stop ait-yolo
```

## Team project task

Now apply the same approach to the inference service in your team repository.

You may copy the two container files as a starting point. This example assumes that the team repository is in `~/team-project`; use the real path to your repository.

```bash
cd ~/team-project
cp ~/ait-course-final-lab/labs/lab_07/starter/Dockerfile .
cp ~/ait-course-final-lab/labs/lab_07/starter/.dockerignore .
```

Use this order:

1. Check that the `Dockerfile` installs the team's dependencies, copies the required service files, and starts the real API command.
2. Check that `.dockerignore` excludes `.env`, local environments, credentials, generated evidence such as `reports/` and `*.jsonl`, and large model weights that will be downloaded or mounted at runtime.
3. Build a named image and run the existing project tests inside it.
4. Start the service with its port, runtime configuration, and evidence directory connected to the container.
5. Demonstrate one valid request and one rejected request, then inspect the saved evidence.
6. Replace the container and confirm that the earlier evidence remains.

If your project kept the Lab 06 directory structure and port, these commands provide a starting point:

```bash
mkdir -p reports
sudo docker build -t team-ai-service:1 .
sudo docker run -d --rm --name team-ai-service \
  -p 8000:8000 \
  --env-file .env \
  --mount type=bind,src="$(pwd)/reports",dst=/app/reports \
  team-ai-service:1
```

Use the project's real test command before starting the service. Change the port, configuration file, startup command, and evidence path when the project uses different ones.

Adapt the reference files to your own input type and dependencies. Do not copy YOLO-specific packages or image rules into a project that does not use them.

Commit the working container files and any necessary code correction to the team repository. Do not commit `.env`, model weights, credentials, private inputs, or generated traces.

## Prepare for next week's project defense

Before leaving, make sure:

- another team member can start the service;
- the team has one valid example ready to demonstrate;
- the team can explain one rejected input and the evidence it produced;
- screenshots or saved output are available if the live connection fails;
- every member knows which part of the project they will explain.

Next week is reserved for the project defense. Every team must show its project and explain the work completed during the course to receive course credit.

## Completion check

The final Lab is complete when another computer can call the containerised team service, a valid and an invalid request follow the expected paths, and the evidence remains after the container is replaced.

## If something does not work

Check the current state before changing anything:

```bash
sudo docker ps -a
sudo docker logs ait-yolo
df -h /
```

- If the container name is already in use, stop the old `ait-yolo` container before starting another one.
- If port 8000 is already in use, check whether the Lab 06 Uvicorn process or another container is still running.
- If the build reports that the disk is full, show the `df -h /` and `sudo docker system df` output before removing images.
- If the API does not open, check the container log, the VM public IP, and the published port.
- If evidence is missing, confirm that the `reports` directory existed before `docker run` and that the `--mount` path matches the command above.

## Finish safely

Stop running containers when you finish:

```bash
sudo docker ps
sudo docker stop <container-name>
```

Stop the cloud VM when the team is not using it, and start it again before the project defense.

References: [Dockerfile reference](https://docs.docker.com/reference/dockerfile/), [docker run](https://docs.docker.com/reference/cli/docker/container/run/), and [bind mounts](https://docs.docker.com/engine/storage/bind-mounts/).

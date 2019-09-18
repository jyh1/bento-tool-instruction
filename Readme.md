# BENTO Tool Instruction

## Set up Docker environment
Docker container provides an OS-level virtualization where you can specify the exact system environments for executing your code, so your experiment results could be easily reproduced by others or even yourself at a future date. 

### Docker Basics

#### Test Docker installation
Docker has already been set up in the UML GPU server(10.116.12.46). Use the following command after logging in to test you have the correct permission to use Docker. Contact the admin if there is any problem.
```bash
docker run hello-world
```

#### Image v.s. Container
A Docker image is an inert, immutable, file that's essentially a snapshot of a system environment. An image usually has a unique tag associated with it and will produce a container when started with `docker run`. For example, the default docker image for CodaLab is tagged with `codalab/default-cpu`. If we use the following command:
```bash
docker run --rm codalab/default-cpu pip list
```
What happened here is that we used the `docker run` sub-command with option `--rm` and the image `codalab/default-cpu` is selected. Docker will produce a running container based on the image and executed the command `pip list` inside it. Obviously, this command will print out the python packages that are installed in the `codalab/default-cpu` image. Option `--rm` is used to delete the produced container after the command finished.

To start an interactive session:
```bash
docker run -it --rm codalab/default-cpu bash
```
This will land you in a bash session in the produced container and you can further explore its environment.

#### Mount folders to container
Docker container is a sandboxed environment isolated from the host system. In order to access your code and data inside a container, you need to use the `-v` option to mount your folder at the start of the container. For example:

```bash
docker run -it --rm -v /host/path:/opt/data codalab/default-cpu bash
```

This will mount your folder `/host/path` to `/opt/data` in the container. You can have multiple `-v`s to mount as many folders/files as you need. Note only absolute paths are allowed in the `v` option.

### Build your docker image
The canonical way to build a docker image is to use the `docker build` command with a [Dockerfile](https://docs.docker.com/engine/reference/builder/). For our purpose to build a BENTO tool image, we can use an easier way which be illustrated with an example.  



```
NV_GPU="0,1" nvidia-docker run --rm codalab/default-gpu nvidia-smi
```
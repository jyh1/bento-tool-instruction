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
The canonical way to build a docker image is to use the `docker build` command with a [Dockerfile](https://docs.docker.com/engine/reference/builder/). For our purpose to just build a BENTO tool image, we can use an easier approach which will be illustrated with a simple example.

An example folder can be found in this repository. In the following sections, we will try to build a docker image for running its code.

#### Pick a base image
Base image will serve as a initial system environment in which you can install additional libraries and tools to build a customized environment. You can start from a basic image like a bare bone [`ubuntu`](https://hub.docker.com/_/ubuntu?tab=description), which will take a lot of efforts to set up everything. 

For our use case, it is recommended to pick the base image according to your deep learning framework. There are official image repositories for [pytorch](https://hub.docker.com/r/pytorch/pytorch/tags) and [tensorflow](https://hub.docker.com/r/tensorflow/tensorflow/tags) on DockerHub. You should pick image with tags containing `cuda` or `gpu` if you need to use GPUs. If you are using `tensorflow`, also consider using `codalab/default-gpu` or `codalab/default-cpu` which have already pre-installed other commonly used libraries.

The example code used pytorch, so we will use the image with the tag `1.2-cuda10.0-cudnn7-runtime` from the [pytorch](https://hub.docker.com/r/pytorch/pytorch/tags) DockerHub as the base image.

#### Customize your container
Docker image is an immutable file. In order to add new libraries to it, we need to start a container from the image, customize the container and commit the modified container as a new image.

Assuming we are in the `example` directory, start a container from the base image:
```bash
docker run --runtime nvidia -it --name my_container -v $PWD:/opt/example pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime bash
```
We have introduced the `docker run` earlier. The `--runtime nvidia` option will expose the GPU resources to your container. We specify a name for our container with the `--name` option. The `example` folder in the host system is mounted to the `/opt/example` in the container.

If everything went well, you should be in a bash session inside your newly created container. Try running the example code inside the container:

```bash
root@f590d7c561e1:/workspace# cd /opt/example
root@f590d7c561e1:/opt/example# ls
code  data
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt 
Traceback (most recent call last):
  File "code/main.py", line 3, in <module>
    from nltk.tokenize import word_tokenize
ModuleNotFoundError: No module named 'nltk'
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt 
```

Turns out we still miss the `nltk` package. Install it with:
```bash
conda install nltk
```
Note that the `pytorch` image we are using have already installed `conda`. If your base image have not, consider other existing package management tools like `pip` or simply install `conda` yourself.

Try again:
```bash
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt
Resource punkt not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('punkt')
```
Another error occurred, repeating the same process as before:
```bash
root@f590d7c561e1:/opt/example# python -c 'import nltk; nltk.download("punkt")'
[nltk_data] Downloading package punkt to /root/nltk_data...
[nltk_data]   Unzipping tokenizers/punkt.zip.
```

The code finally worked:
```bash
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt 
['an', 'example', 'sentence', '.']
['another', 'example', 'sentence', '.']
GPU count:  4
```

#### Create your image
Our code finally run correctly inside our container. The last step is to commit the container as an image, which will essentially take a snapshot of the container and save it in an image file. Note that the data in the mounted volumes will not be included, we can only mount folders to containers. 

Existing the container bash session with `Ctrl+D` and executing the following command in the host system:
```bash
docker commit my_container example_image
```
Voilá, we successfully build a docker image for our example code. The `my_container` is the name of our created container. If you forget the name, using `docker ps -a` to find out the name or id. `example_image` is the tag we would like to assign to the newly created image.

From now on, we can run our code simply by:
```bash
docker run --runtime nvidia -it  -v $PWD:/opt/example example_image python /opt/example/code/main.py /opt/example/data/sample.txt
```

It will start a container based on our recently created `example_image` and execute the command.
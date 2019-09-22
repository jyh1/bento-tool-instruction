# BENTO Tool Instruction
- [BENTO Tool Instruction](#bento-tool-instruction)
  - [Set up Docker environment](#set-up-docker-environment)
    - [Docker Basics](#docker-basics)
      - [Test Docker installation](#test-docker-installation)
      - [Image v.s. Container](#image-vs-container)
      - [Mount folders to container](#mount-folders-to-container)
    - [Build your docker image](#build-your-docker-image)
      - [Pick a base image](#pick-a-base-image)
      - [Customize your container](#customize-your-container)
      - [Create your image](#create-your-image)
      - [Publish to DockerHub](#publish-to-dockerhub)
    - [Common Problems](#common-problems)
  - [Use CodaLab](#use-codalab)
    - [Introduction](#introduction)
    - [CodaLab Basics](#codalab-basics)
      - [cl run](#cl-run)
    - [Run commands on CodaLab](#run-commands-on-codalab)
      - [Upload code and data](#upload-code-and-data)
      - [Run command](#run-command)
  - [The BENTO Tool Design Pattern](#the-bento-tool-design-pattern)
      - [Split pipeline into smaller steps](#split-pipeline-into-smaller-steps)
      - [Use command line arguments](#use-command-line-arguments)
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
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt result.txt
Traceback (most recent call last):
  File "code/main.py", line 3, in <module>
    from nltk.tokenize import word_tokenize
ModuleNotFoundError: No module named 'nltk'
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt result.txt 
```

Turns out we still miss the `nltk` package. Install it with:
```bash
conda install nltk
```
Note that the `pytorch` image we are using have already installed `conda`. If your base image have not, consider other existing package management tools like `pip` or simply install `conda` yourself.

Try again:
```shell
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt result.txt
Resource punkt not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('punkt')
```
Another error occurred, repeating the same process as before:
```shell
root@f590d7c561e1:/opt/example# python -c 'import nltk; nltk.download("punkt")'
[nltk_data] Downloading package punkt to /root/nltk_data...
[nltk_data]   Unzipping tokenizers/punkt.zip.
```

The code finally worked:
```bash
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt result.txt
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
Voilá, we just successfully build a docker image for our example code. The `my_container` is the name of the container we just created. If you forget the name, using `docker ps -a` to find out the name or id. `example_image` is the tag we would like to assign to the newly created image.

From now on, we can run our code simply by:
```bash
docker run --runtime nvidia -it --rm  -v $PWD:/opt/example example_image python /opt/example/code/main.py /opt/example/data/sample.txt /opt/example/result.txt
```

It will start a container based on our recently created `example_image` and execute the command inside the container. 

#### Publish to [DockerHub](https://hub.docker.com)
The docker image we just created only exist on our server. We can publish it to the [DockerHub](https://hub.docker.com) to make it accessible everywhere.

You need to create an account on [DockerHub](https://hub.docker.com) and create a public repository.

First, login to DockerHub on the host system with the following command:
```bash
docker login
```
Assign a new tag to your local image with a special format. In my case, my DockerHub user name is `jyh1`, the name of the repository I want to push to is `bento` and I want to name it `example`. The local image I want to publish has a local tag `example_image`. The commands I used might look like:
```bash
docker tag example_image jyh1/bento:example
docker push jyh1/bento:example
```

After this, the image could be accessed anywhere using the tag `jyh1/bento:example`:
```bash
docker run --runtime nvidia -it --rm  -v $PWD:/opt/example jyh1/bento:example python /opt/example/code/main.py /opt/example/data/sample.txt /opt/example/result.txt
```

### Common Problems
Some common problems when migrating your code to a docker environment:

1. Hard-coded file paths
   - Try to avoid hard coded file paths in your program, use command line options instead. This applies to both reading (accessing data file) and writing (generating results). Quite possibly file paths hard-coded in your program do not exist in the container. This will become more necessary when using CodaLab.
2. What to include in a docker image
   - A container can access data from either its private virtualized disk (populated from its image) or the volumes mounted from host system. In an extreme scenario, you can include your data/code and everything you need in the image, so you don't need to mount any thing to run your code. This will bloat the size of image and make it harder to be reused (building a new image every time the codes are updated or use a new data set). As a rule of thumb, only include libraries/executable distributed by a package-management system in the image and dynamically mount your own code directory and data.

## Use CodaLab

### Introduction

As we have seen in the previous example, Docker will help you set up a consistent "system environment" anywhere anytime from a docker image. However, this is not the whole picture. The exact environment of a newly created container also includes the contents of the mounted folders. Even though you use the same mounting options every time, the contents of the files can change. Docker will not help you keep track of those "external contents" unless, of course, you are willing to go all out and include everything you need to the image and we have already seen why that is a bad idea.

CodaLab is built to solve this problem. It is built upon Docker and can help you easily reproduce the complete environment of a container without creating a new docker image each time. It achieves this by recording not only the Docker image but all the contents mounted to the container. 

CodaLab can be thought as a high-level interface of Docker designed for the purpose of data science research. You can run arbitrary command in CodaLab and the command will be executed inside a container created from the image you specified. But how to mount data to the container? When using Docker, you use the file paths in the host system. In CodaLab, you mount bundles. Bundles are immutable files/folders in CodaLab and can be uniquely identified by their UUIDs. In this way, CodaLab can record those "external contents" of a container simply by recording the UUIDs of the bundles mounted to it. 

[A quick introduction video of CodaLab](https://www.youtube.com/watch?time_continue=9&v=WwFGfgf3-5s).

### CodaLab Basics
It is recommended to use our own CodaLab server and follow the [quick example](https://github.com/codalab/worksheets-examples/blob/master/00-quickstart/README.md) to get a feeling of how it works.

#### cl run

In CodaLab, we use `cl run` to replace the `docker run` that we used before. For example:

```bash
cl run --request-gpus 2 --request-docker-image jyh1/bento:example code:0x3b5f831f09f04a22bcd3020b7a1cb69c data:0xd4c5712c156f41e48e6400f05cc5441c 'ls -R && python code/main.py data result.txt'
```
We first use two `--request-*` options to specify the resources we would like to use, which are followed by the bundle dependency declaration. The canonical form of bundle dependency is `<name>:<UUID>` (You can use a shorthand form if referencing bundles from the current worksheet, which will later be expanded to the canonical form). The last part is the command we want to run.

After receiving the `cl run` command, CodaLab will try to schedule it to a worker. Once a worker receives the job, it will: 1. create a container from the image we specified; 2. mount an empty directory and set it as working directory; 3. mount the bundles in the dependency list to the working directory under their names; 4. execute the command in the current directory and wait for it to finish; 5. dismount everything and save the contents of the working directory as a new bundle.

In the above example, there will be two folders in the working directory, named `code` and `data`. Their contents will be the bundle `0x3b5f...` and `0xd4c5...`.

Bundles could be files or folders. For folder bundle, you can choose to depend on a child element. For example:
```bash
cl run data:0x233 'cat data/d1.txt'
```
produces the same results with:
```bash
cl run d1:0x233/d1.txt 'cat d1'
```

### Run commands on CodaLab

In this section, we will use the same [example](./example) and run it on CodaLab.

#### Upload code and data
Upload the code and data to CodaLab, either through the web interface or `cl upload`.

```shell
cl upload code
cl upload data/sample.txt
```
We upload the code and data separately instead of bundling the code and data together. This is not required but will make the tool more flexible handling new data set.

#### Run command
We can use the image just published on DockerHub to execute our code on CodaLab.
```shell
cl run --request-gpus 2 --request-docker-image jyh1/bento:example :sample.txt :code 'python code/main.py sample.txt result.txt'
```

## The BENTO Tool Design Pattern

#### Split pipeline into smaller steps


#### Use command line arguments


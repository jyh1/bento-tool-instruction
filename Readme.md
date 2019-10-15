# BENTO Tool Instruction <!-- omit in toc -->
- [Set up Docker environments](#set-up-docker-environments)
  - [Docker Basics](#docker-basics)
    - [Test Docker environment](#test-docker-environment)
    - [Image v.s. Container](#image-vs-container)
    - [Mount folders to container](#mount-folders-to-container)
  - [Build your docker image](#build-your-docker-image)
    - [Pick a base image](#pick-a-base-image)
    - [Customize your container](#customize-your-container)
    - [Create your image](#create-your-image)
    - [Publish your images to DockerHub](#publish-your-images-to-dockerhub)
  - [What to include in a Docker Image](#what-to-include-in-a-docker-image)
- [Use CodaLab](#use-codalab)
  - [Introduction](#introduction)
  - [CodaLab Basics](#codalab-basics)
    - [cl run](#cl-run)
  - [Move your program to CodaLab](#move-your-program-to-codalab)
    - [Upload code and data](#upload-code-and-data)
    - [Run command](#run-command)
- [The BENTO Tool Design Pattern](#the-bento-tool-design-pattern)
  - [Split into smaller steps](#split-into-smaller-steps)
  - [Use command-line arguments](#use-command-line-arguments)
## Set up Docker environments
Docker container provides an OS-level virtualization where you can specify the exact system environments for executing your code, so your experiment results could be easily reproduced by others or even yourself at a future date. 

### Docker Basics

#### Test Docker environment
Docker has already been set up in our UML GPU server(10.116.12.46). Use the following command to test you have the correct permission to use Docker.
```bash
docker run hello-world
```

#### Image v.s. Container
A Docker image is an inert, immutable file that is essentially a snapshot of a system environment. An image usually has a unique tag and will produce a container when started with `docker run`. For example, the default docker image for CodaLab is tagged with `codalab/default-cpu`. If we use the following command:
```bash
docker run --rm codalab/default-cpu pip list
```
What happened is that we used the `docker run` command with option `--rm` and the image `codalab/default-cpu`. Docker will produce a running container from the image and executed the command `pip list` inside it. Obviously, this command will print out the python packages that are installed in the `codalab/default-cpu` image. Option `--rm` is used to delete the newly generated container after it stops.

To start an interactive session:
```bash
docker run -it --rm codalab/default-cpu bash
```
This will land you in a bash session in the new container and allow you to further explore the system environment.

#### Mount folders to container
Docker container is a sandboxed environment which is isolated from the host system. In order to access your code and data inside the container, you need to use the `-v` option to mount your folder to the container. For example:

```bash
docker run -it --rm -v /host/path:/opt/data codalab/default-cpu bash
```

This will mount host system folder `/host/path` to `/opt/data` in the container. You can have multiple `-v`s to mount as many folders/files as you need. Note only absolute paths are allowed in the `-v` option.

### Build your docker image
The canonical way to build a docker image is through the `docker build` command with a [Dockerfile](https://docs.docker.com/engine/reference/builder/). For the purpose of building an environment for your code, we can use an easier approach which we will illustrate with a simple example.

The [example folder](./example) in this repository contains a simple program and data. In the following sections, we will build a docker image for that program step by step.

#### Pick a base image
Base image will serve as an initial system environment in which you can install new libraries and tools to build a new image. 

You can pick any image as base image. For our use case, it is recommended to pick the base image according to your deep learning framework. There are official repositories for [pytorch](https://hub.docker.com/r/pytorch/pytorch/tags) and [tensorflow](https://hub.docker.com/r/tensorflow/tensorflow/tags) on DockerHub. You can pick images with tags containing `cuda` or `gpu` if you want to use GPUs. If you are using `tensorflow`, also consider using `codalab/default-gpu` or `codalab/default-cpu` which is based on `tensorflow` and has already pre-installed other commonly used NLP libraries. If your code does not use deep learning framework, you can start with an image with package manager pre-installed like [conda](https://hub.docker.com/r/conda/miniconda3) or simply start with a basic one like [ubuntu](https://hub.docker.com/_/ubuntu/).

In the example code `pytorch` is used, so we will choose the image `1.2-cuda10.0-cudnn7-runtime` from the [pytorch](https://hub.docker.com/r/pytorch/pytorch/tags) repository as our base image.

#### Customize your container
In order to build the image we need from the base image, we basically follow the following steps: 1. start a container from the base image; 2. customize the container and finally 3. save the modified container as a new image.

Assuming we are currently in the `example` directory, start a container from with base image with the following command:
```bash
docker run --runtime nvidia -it --name my_container -v $PWD:/opt/example pytorch/pytorch:1.2-cuda10.0-cudnn7-runtime bash
```
We have already seen the `docker run` command before. The `--runtime nvidia` option will allow your container to access GPUs. We specify a name for the container with the `--name` option. The `example` folder in our host system is mounted to the `/opt/example` of the container.

If everything went well, you should be in a bash session inside your newly created container. Next we will try running the example code inside it:

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
Note that the `pytorch` image we are using has pre-installed `conda`. If the base image you used has not, consider other existing package management tools like `pip` or simply install `conda` yourself.

Try again:
```shell
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt result.txt
Resource punkt not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('punkt')
```
Another error occurred, it seems we have to download the nltk data:
```shell
root@f590d7c561e1:/opt/example# python -c 'import nltk; nltk.download("punkt", download_dir="/opt/conda/nltk_data")'
[nltk_data] Downloading package punkt to /root/nltk_data...
[nltk_data]   Unzipping tokenizers/punkt.zip.
```

The default download location for nltk_data is `~/nltk_data`, we change it to a user-agnostic position so it will work when migrating to CodaLab (CodaLab will execute your command with a newly created user in the container).

Keep installing missing packages until your program runs correctly. Meanwhile, you can edit your code files with editors in the host system if needed.
```bash
root@f590d7c561e1:/opt/example# python code/main.py data/sample.txt result.txt
['an', 'example', 'sentence', '.']
['another', 'example', 'sentence', '.']
GPU count:  4
```

#### Create your image
After the code run correctly in the container. The last step is to commit the container as an image, which will essentially take a snapshot of the current container and save it in an image file. Note that the data in the mounted volumes will not be included, we can only mount folders to containers. 

Exit the container session with `Ctrl+D` and use the following command in the host system:
```bash
docker commit my_container example_image
```
Voilá, we just successfully build a docker image for the example code. The `my_container` is the container name we are trying to commit. If you forget the name, using `docker ps -a` to find out. `example_image` will be the tag of the new image.

From now on, we can run our code in the correct environment by doing:
```bash
docker run --runtime nvidia -it --rm  -v $PWD:/opt/example example_image python /opt/example/code/main.py /opt/example/data/sample.txt /opt/example/result.txt
```

Docker will start a container from `example_image` and execute the command inside the container. 

#### Publish your images to [DockerHub](https://hub.docker.com)
The docker image we just created only exist in our server right now. We can publish it to the [DockerHub](https://hub.docker.com) to make it available everywhere.

You need to create an account on [DockerHub](https://hub.docker.com) and create a public repository. After this, you can login to DockerHub on the host system with the following command:
```bash
docker login
```

The image we just built is tagged with `example_image`, we can use it to identify this image locally. In order to publish it to DockerHub, we need to change the tag to a certain format:
```bash
docker tag example_image jyh1/bento:example
```
Here `jyh1` is my DockerHub username, `bento` is the repository name and `example` is the repository tag we want to use.

Publish to DockerHub via:
```
docker push jyh1/bento:example
```

After this, we can use the tag `jyh1/bento:example` to fetch our image from DockerHub on any machine:
```bash
docker run --runtime nvidia -it --rm  -v $PWD:/opt/example jyh1/bento:example python /opt/example/code/main.py /opt/example/data/sample.txt /opt/example/result.txt
```

### What to include in a Docker Image
A container can access data either from its private virtualized storage (populated from the image) or the volumes mounted from the host system. In an extreme scenario, you can save everything you need including all the data and code to your image, so you don't need to mount them. This is not recommended as it will bloat the image size and make it harder to be reused (building a new image every time a different data is used). As a rule of thumb, only include libraries/executable from package-management systems (like apt, pip, conda ...) in the image. The data and code files should be mounted.

## Use CodaLab

### Introduction

As we have seen in the previous example, Docker will help you set up a consistent "system environment" anywhere anytime from a docker image. However, this is not the whole picture. The exact environment of a newly created container also includes the contents of the mounted folders. Even though you use the same mounting options every time, the contents of the files can change. Docker will not help you keep track of those "external contents" unless, of course, you are willing to go all out and include everything you need to the image. However we have already seen why this is a bad idea.

CodaLab is built to solve this problem. It is built upon Docker and can help you keep track of the "external contents" you used when executing a certain command.

CodaLab can be thought as a high-level interface of Docker designed for doing data science research. In CodaLab, you can run arbitrary command inside a container created from the image you specified. But how to mount data to the container? When using Docker, you use the file paths in the host system. In CodaLab, you mount bundles. Bundles are immutable file/folder objects in CodaLab and can be uniquely identified by their UUIDs. CodaLab can record the exact "external contents" of a container simply by recording the UUIDs of the bundles mounted to it. 

[A quick introduction video of CodaLab](https://www.youtube.com/watch?time_continue=9&v=WwFGfgf3-5s).

### CodaLab Basics
It is recommended to follow the offical CodaLab [quick example](https://github.com/codalab/worksheets-examples/blob/master/00-quickstart/README.md) first to get a feeling of how it works.

You can use our own CodaLab instance at the url [https://bio-nlp.org/codalab/](https://bio-nlp.org/codalab/), not to be confused with the public CodaLab instance: [https://worksheets.codalab.org/](https://worksheets.codalab.org/). You can start by creating an account on it. In the following section, we will assume you are using our lab instance of CodaLab. (__Sometimes the web page might incorrectly navigate to our lab homepage due to a problem in the proxy server, if that happens just go to the CodaLab url https://bio-nlp.org/codalab/ with the trailing slash again__). 

Jobs submitted to our CodaLab instance will be scheduled to the GPU server in UML. This means you can run your experiments on the GPU server without the need of actually logging into the server anymore. Using CodaLab will become more convenient when we have more servers in the future. CodaLab will take care of job scheduling among multiple servers for you.

If you plan to use CodaLab instance through the command line tool `cl` instead of on the web page, you can set up your `cl` program with:
```bash
cl alias bionlp https://bio-nlp.org/codalab/ # due to a problem in the DNS server that will hopefully be fixed soon, use https://fenway.cs.uml.edu/codalab/ instead if you are doing this in the UML GPU server
cl work bionlp::
```

#### cl run

In CodaLab, we use `cl run` to replace the previous `docker run` to run command inside a container. For example, run this command on our CodaLab instance:
```bash
cl run --request-gpus 2 --request-docker-image jyh1/bento:example code:0x9d49ead692f14d3a8c0e9810dbec9d9c data:0x756af36c15804990aff05367f5e99742 'ls -R && python code/main.py data result.txt'
```
We first use two `--request-*` options to specify the resources we would like to use, which are followed by the bundle dependency declaration. The canonical form of bundle dependency is `<name>:<UUID>` (You can use a shorthand form if referencing bundles from the current worksheet, which will be expanded to the canonical form by the program). The last part is the quoted command we want to run in the container.

After receiving the `cl run` command, CodaLab will try to schedule it to a worker. Once a worker receives the job, it will: 1. create a container from the image we specified; 2. mount an empty directory and set it as working directory; 3. mount the bundles in the dependency list to the working directory under their names; 4. execute the command in the current directory and wait for it to finish; 5. dismount everything and save the contents of the working directory as a new bundle which can be used in later steps. 

In the above example, there will be two folders in the working directory: `code` and `data`. Their contents will be the bundle `0x9d49...` and `0x756a...`.

Bundle can be either files or folders. For folder bundles, you can use a sub-path in dependency declaration. For example, the following commands produce same result:
```bash
cl run data:0x233 'cat data/d1.txt'
```
```bash
cl run d1:0x233/d1.txt 'cat d1'
```
The folder bundle is mounted with the name `data` in the first command. In the second one, only the child file `d1.txt` is mounted under the name `d1`.

### Move your program to CodaLab

In this section, we will use the same [example](./example) as before and move it to CodaLab.

#### Upload code and data
Upload the code and data to CodaLab, either through the web interface or `cl upload`.

```shell
cl upload code
cl upload data/sample.txt
```
We upload the code and data separately instead of bundling them together. This will make our command more flexible dealing with new data set or new code.

#### Run command
Run the command on CodaLab, of course we will use the Docker image we built for it.
```shell
cl run --request-gpus 2 --request-docker-image jyh1/bento:example code:0x9d49ead692f14d3a8c0e9810dbec9d9c sample.txt:0x756af36c15804990aff05367f5e99742 'python code/main.py sample.txt result.txt'
```

That's it. It's trivial to use CodaLab once you have the image ready.

## The BENTO Tool Design Pattern

Publishing your program as a tool might be a bit different with using it in research. The CodaLab itself enforce little restriction on how you should run your programs. However, in order to publish your programs on BENTO and make them flexible, composable and easy to use, it is recommended to make some small adaptions to your programs according to certain general guidelines which are collectively called the BENTO tool design pattern. 

### Split into smaller steps
You can certainly make your program do everything with a single command (like from training to evaluating). Although that might come in handy while doing experiments, it's inflexible to use for other people. Sometimes we might just want to apply the trained model to a new data set. A more sensible approach is to split your pipeline into smaller steps. Each step only performs a single-ish task. We can always compose individual steps in to a single pipeline. The same cannot be said of the reverse process. It is easy to do composition in the BENTO system.

For our purpose, a typical tool can be split into the following steps:
1. Preprocessing: Transform raw data to a more usable format. 
2. Training: Take the processed data as input and save the trained model into weight files.
3. Predicting: Take a saved model and input data, output prediction results.
4. Evaluation: Evaluate the prediction with gold standard. 

This is just a very general description and might not 100% apply to your programs. You can certainly split the tool into even smaller steps

Note this doesn't mean you have to literally split your code into different files. You can use a command line option to control the behavior of your program.

### Use command-line arguments
Try using a command-line arguments for everything that you expect users might want to change in your program. This includes the input/output locations and important hyper-parameters. Some people might prefer using a config file when there are too many arguments. Since editing files in BENTO is generally hard, it is recommended to add command-line options that are able to override the config file for important parameters in your tool. 

Be aware of some "implicit" file paths in your code. For example, your program might save training results to a folder called `saved_models` and when doing prediction, the program will automatically load weights from that folder. Usually people don't bother to use a command-line options for folders like `saved_models`. However, in BENTO, it might be better to make all input and output paths explicit in the arguments.

# fsleyes-plugin-shimming-toolbox

This plugin allows users to integrate `NeuroPoly`'s `shimming-toolbox` application with the
`FSLeyes` GUI.

## Installation

In the `fsleyes-plugin-shimming-toolbox` folder, run:

```
make install
```

## Running

In the `fsleyes-plugin-shimming-toolbox` folder, run:

```
make run
```


### Developers


First, you will need to create a `conda` virtual environment, and activate it.

```
conda create --name pst_venv
conda activate pst_venv
```

Next, install `fsleyes`:

```
yes | conda install -c conda-forge fsleyes
```

Next, install ``wxPython`` using ``conda-forge``:

```
yes | conda install -c conda-forge/label/cf202003 wxpython
```

Now, you can install `fsleyes-plugin-shimming-toolbox`:

```
pip install -e path/to/fsleyes-plugin-shimming-toolbox
```

Now, install `pipx`. See their documentation for more details. You can install `pipx` either in
this virtual environment, or in your root environment. If you install in the venv, you won't
be able to access `pipx` elsewhere (but you can still access the packages installed through
`pipx` anywhere).

Once you have `pipx` installed, you need to install `shimming-toolbox`. You can install it
in any environment you want, as long as you can use `pipx`.

```
pipx install -e path/to/shimming-toolbox
```

## Testing with Docker

We can use `Docker` to spin up a Linux instance and test our install procedure in a clean
environment. You will need to install `Docker` on your computer first: https://www.docker.com/products/docker-desktop

To create our testing container, we will first build an image called `fpst:latest`:
```
docker build --tag fpst:latest .
```

Once our image is built, we want to remove any running instances of the container:
```
docker rm --force fpst
```

Then, we can create a container from our `fpst:latest` image:
```
docker run --name fpst -dit fpst:latest
```

To test our package, we can use the `bash` function of the container:
```
docker exec -it fpst bash
```

Once inside the container terminal, we can find our plugin package and test it:
```
cd src/fsleyes-plugin-shimming-toolbox
make install
```

Altogether:

```
docker rm --force fpst
docker build --tag fpst:latest .
docker run --name fpst -dit fpst:latest
docker exec -it fpst bash
```

## Testing with VirtualBox

To test on different operating systems, you will need to use a virtual machine. You will need to
install `VirtualBox`: https://www.virtualbox.org/wiki/Downloads. You will also need to install
the Oracle VM VirtualBox Extension Pack in order to test MacOSX.

`Vagrant` is a tool that interfaces with `VirtualBox` and streamlines the process:
https://learn.hashicorp.com/tutorials/vagrant/getting-started-index?in=vagrant/getting-started

We have 3 different folders with `Vagrantfile`s for testing each OS:

```
| testing
| -- vagrant_linux/
| -- vagrant_mac/
| -- vagrant_windows/
```

To create the virtual box, run:
```
cd testing/vagrant_{OS}
vagrant up
```

Next, ssh into the shell and run the `fsleyes-plugin-shimming-toolbox` installer:
```
cd src/fsleyes-plugin/shimming-toolbox/
sudo make install
```

### Vagrant Tips

To stop the box from running (but not remove it):
```
vagrant suspend
```

To resume the box:
```
vagrant resume
```

To remove the box completely:
```
vagrant destroy
```

If you update your `Vagrantfile` and you want to reload the box:
```
vagrant reload
```

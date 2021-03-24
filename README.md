# fsleyes-plugin-shimming-toolbox

## Installation


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
